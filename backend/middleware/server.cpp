#include "uart_interface.hpp"
#include "test_interface.hpp"
#include <zmq.hpp>
#include <iostream>
#include <thread>
#include <atomic>
#include <unistd.h> // For debug sleep()
#include <signal.h>
#include "payloads/AV_TO_GCS_DATA_1.hpp"
#include "process_logging.hpp"

// This file hosts the ZeroMQ IPC server stuff

std::atomic<bool> running{true};
volatile bool debugger_attached = false;

// Thread safe signal handler
void signal_handler(int)
{
    process_logging::info("Signal received, stopping server");
    running = false;
}

void set_thread_name(const char *name)
{
#ifdef __APPLE__
    pthread_setname_np(name);
#endif
}

void uart_read_loop(std::unique_ptr<LoraInterface> interface, zmq::socket_t &pub_socket)
{
    set_thread_name("uart_read_loop");
    std::vector<uint8_t> buffer(256);

    while (running)
    {
        ssize_t count = interface->read_data(buffer);
        if (count > 0)
        {
            // Check if we have enough bytes for the ID
            if (count >= 1)
            {
                int8_t packet_id = buffer[0];

                // Send packet ID to receiving ends so they know which proto file to use
                std::string packet_id_string(1, packet_id);
                zmq::message_t msg(packet_id_string.data(), sizeof(int8_t));
                pub_socket.send(msg, zmq::send_flags::none);

                // Check if this is an AV_TO_GCS_DATA_1 packet
                if (packet_id == AV_TO_GCS_DATA_1::ID)
                {
                    // Ensure we have enough bytes for the full payload
                    if (count >= AV_TO_GCS_DATA_1::SIZE) // This includes the byte already read
                    {
                        try
                        {
                            // Create payload object from buffer (skipping ID byte)
                            AV_TO_GCS_DATA_1 payload(&buffer[1]);

                            // Convert to protobuf
                            auto proto_msg = payload.toProtobuf();

                            // Serialize protobuf to string
                            std::string serialized;
                            if (proto_msg.SerializeToString(&serialized))
                            {
                                // Send proto via ZMQ
                                zmq::message_t msg(serialized.data(), serialized.size());
                                pub_socket.send(msg, zmq::send_flags::none);
                            }
                            else
                            {
                                std::cerr << "Failed to serialise to string for protobuf" << std::endl;
                            }
                        }
                        catch (const std::exception &e)
                        {
                            std::cerr << "Error processing payload: " << e.what() << std::endl;
                        }
                    } // TODO: What are you gonna do if the buffer needs to be filled again for more bytes? Or is it hardware controlled?
                }
                // Add handling for other packet types here
            }
        }
        else
        {
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
    }
}

std::unique_ptr<LoraInterface> create_interface(
    const std::string INTERFACE_NAME,
    const std::string DEVICE_PATH)
{
    std::unique_ptr<LoraInterface> interface;

    if (INTERFACE_NAME == "UART")
    {
        interface = std::make_unique<UartInterface>(DEVICE_PATH);
    }
    else if (INTERFACE_NAME == "TEST")
    {
        interface = std::make_unique<TestInterface>(DEVICE_PATH);
    }
    else
    {
        throw new std::runtime_error("Error: Invalid interface type");
    }

    return interface;
}

// ./file <interface type> <device path> <socket path>
int main(int argc, char *argv[])
{

#ifdef DEBUG
    process_logging::debug("Starting server in DEBUG mode.");
    // while (!debugger_attached)
    // {
    //     sleep(1);
    // }
    // process_logging::debug("Debugger attached");
#endif

    GOOGLE_PROTOBUF_VERIFY_VERSION;

    // Pick interface based on the first argument
    if (argc < 4)
    {
        process_logging::error("Not enough arugments provided.");
        process_logging::error("Usage: ./file <socket type> <device path> <socket path>");
        // Throw error silenced by main
        throw new std::runtime_error("Error: Not enough arugments provided");
        return EXIT_FAILURE;
    }
    else if (argc > 4)
    {
        std::cerr << "Warning: Too many arugments provided" << std::endl;
    }

    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    try
    {
        // Create an interface
        const std::string DEVICE_PATH = std::string(argv[2]);
        const std::string SOCKET_PATH = std::string(argv[3]);
        std::unique_ptr<LoraInterface> interface = create_interface(
            std::string(argv[1]),
            DEVICE_PATH);

        interface->initialize();
        process_logging::info("Interface initialised for type: " + std::string(argv[1]));

        // ZeroMQ setup
        zmq::context_t context(1);

        // PUB socket for broadcasting incoming data
        zmq::socket_t pub_socket(context, ZMQ_PUB);
        pub_socket.bind("ipc:///tmp/" + SOCKET_PATH + "_pub.sock");

        // PULL socket for fowarding commands to LoRa
        zmq::socket_t pull_socket(context, ZMQ_PULL);
        pull_socket.bind("ipc:///tmp/" + SOCKET_PATH + "_pull.sock");

        // Start UART reading thread
        std::thread reader(uart_read_loop, std::move(interface), std::ref(pub_socket));

        // http://api.zeromq.org/3-0:zmq-poll
        zmq::pollitem_t items[] = {{pull_socket, 0, ZMQ_POLLIN, 0}};

        // Main command loop
        while (running)
        {
            zmq::poll(items, 1, std::chrono::milliseconds(100)); // 100ms timeout

            if (items[0].revents & ZMQ_POLLIN)
            {
                zmq::message_t msg;
                zmq::recv_result_t result = pull_socket.recv(msg, zmq::recv_flags::none);

                // Process command (example: echo back)
                std::vector<uint8_t> cmd_data(
                    static_cast<uint8_t *>(msg.data()),
                    static_cast<uint8_t *>(msg.data()) + msg.size());

                interface->write_data(cmd_data);
            }
        }

        // Cleanup
        reader.join();
    }
    catch (const std::exception &e)
    {
        std::cerr << "Error: " << e.what() << "\n";
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}