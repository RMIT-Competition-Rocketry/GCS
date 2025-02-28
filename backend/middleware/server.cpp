#include "uart_interface.hpp"
#include "test_interface.hpp"
#include <zmq.hpp>
#include <iostream>
#include <thread>
#include <atomic>
#include <unistd.h> // For debug sleep()
#include <signal.h>
#include "payloads/AV_TO_GCS_DATA_1.hpp"
#include "payloads/AV_TO_GCS_DATA_2.hpp"
#include "payloads/AV_TO_GCS_DATA_3.hpp"
#include "payloads/GCS_TO_AV_STATE_CMD.hpp"
#include "payloads/GCS_TO_GSE_STATE_CMD.hpp"
#include "payloads/GSE_TO_GCS_DATA_1.hpp"
#include "payloads/GSE_TO_GCS_DATA_2.hpp"
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

template <typename PacketType>
void process_packet(const ssize_t BUFFER_BYTE_COUNT,
                    std::vector<uint8_t> &buffer,
                    zmq::socket_t &pub_socket)
{
    if (BUFFER_BYTE_COUNT >= PacketType::SIZE) // SIZE should include the already read ID byte.
    {
        try
        {
            // Construct the packet object (skipping the ID byte)
            PacketType payload(&buffer[1]);

            // Convert to protobuf and serialize to a string
            auto proto_msg = payload.toProtobuf();
            if (!proto_msg.IsInitialized())
            {
                std::string missing_info = proto_msg.InitializationErrorString();
                process_logging::warning(std::string(PacketType::PACKET_NAME) +
                                         ": Not all fields are initialized in the protobuf message. Missing: " +
                                         missing_info);
            }
            std::string serialized;
            if (proto_msg.SerializeToString(&serialized))
            {
                // Has to be At LEAST bigger than the input size with proto
                // process_logging::debug("NAME: " + std::string(PacketType::PACKET_NAME));
                // process_logging::debug("ID  : " + std::to_string(PacketType::ID));
                // assert(serialized.size() >= PacketType::SIZE && PacketType::ID != 0x05);
                zmq::message_t msg(serialized.data(), serialized.size());
                pub_socket.send(msg, zmq::send_flags::none);
            }
            else
            {
                process_logging::error(std::string(PacketType::PACKET_NAME) +
                                       ": Failed to serialize to string for protobuf");
            }
        }
        catch (const std::exception &e)
        {
            process_logging::error(std::string(PacketType::PACKET_NAME) +
                                   ": Error processing payload: " + e.what());
        }
    }
    // Else: Consider handling when not enough data is available.
}

void input_read_loop(std::unique_ptr<LoraInterface> interface, zmq::socket_t &pub_socket)
{
    set_thread_name("input_read_loop");
    std::vector<uint8_t> buffer(256);
    auto last_read_time = std::chrono::steady_clock::now();

    while (running)
    {
        ssize_t count = interface->read_data(buffer);
        if (count > 0)
        {
            last_read_time = std::chrono::steady_clock::now();
            // Check if we have enough bytes for the ID
            if (count >= 1)
            {
                int8_t packet_id = static_cast<int8_t>(buffer[0]);

                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                packet_id = 0x03;

                // Send packet ID to receiving ends so they know which proto file to use
                std::string packet_id_string(1, packet_id);
                zmq::message_t msg(packet_id_string.data(), sizeof(int8_t));
                pub_socket.send(msg, zmq::send_flags::none);

                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                // TEMPORARY FOR SPAMMER MACHINE
                process_packet<AV_TO_GCS_DATA_1>(count, buffer, pub_socket);
                // For temporary debugging because spammer machine has wrong ID

                // // Note that some packet types are observed can be skipped if not meant for GCS
                // switch (packet_id)
                // {
                // case AV_TO_GCS_DATA_1::ID: // 3
                //     process_packet<AV_TO_GCS_DATA_1>(count, buffer, pub_socket);
                //     break;
                // case AV_TO_GCS_DATA_2::ID: // 4
                //     process_packet<AV_TO_GCS_DATA_2>(count, buffer, pub_socket);
                //     break;
                // case AV_TO_GCS_DATA_3::ID: // 5
                //     process_packet<AV_TO_GCS_DATA_3>(count, buffer, pub_socket);
                //     break;
                // case GCS_TO_AV_STATE_CMD::ID: // 1
                //     process_packet<GCS_TO_AV_STATE_CMD>(count, buffer, pub_socket);
                //     break;
                // case GCS_TO_GSE_STATE_CMD::ID: // 2
                //     process_packet<GCS_TO_GSE_STATE_CMD>(count, buffer, pub_socket);
                //     break;
                // case GSE_TO_GCS_DATA_1::ID: // 6
                //     process_packet<GSE_TO_GCS_DATA_1>(count, buffer, pub_socket);
                //     break;
                // case GSE_TO_GCS_DATA_2::ID: // 7
                //     process_packet<GSE_TO_GCS_DATA_2>(count, buffer, pub_socket);
                //     break;
                // default:
                //     std::string numeric_val = std::to_string(static_cast<int>(packet_id));
                //     process_logging::error("Unknown packet ID: " + std::to_string(packet_id) + "numeric: " + numeric_val);
                //     break;
                // }
            }
        }
        else
        {
            // CPU sleeper
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
            // Timeout warning
            auto now = std::chrono::steady_clock::now();
            if (std::chrono::duration_cast<std::chrono::seconds>(now - last_read_time).count() >= 3)
            {
                process_logging::warning("No data received for over 3 seconds.");
                last_read_time = now; // Wait another 3 seconds
            }
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
        // This will sent AT setup commands as well in constructor
        interface = std::make_unique<UartInterface>(DEVICE_PATH);
    }
    else if (INTERFACE_NAME == "TEST")
    {
        interface = std::make_unique<TestInterface>(DEVICE_PATH);
    }
    else
    {
        throw std::runtime_error("Error: Invalid interface type");
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
        throw std::runtime_error("Error: Not enough arugments provided");
        return EXIT_FAILURE;
    }
    else if (argc > 4)
    {
        process_logging::warning("Too many arugments provided");
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
        std::thread reader(input_read_loop, std::move(interface), std::ref(pub_socket));

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
        process_logging::error("Generic error on main: " + std::string(e.what()));
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}