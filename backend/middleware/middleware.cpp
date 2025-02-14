#include "uart_socket_bridge.hpp"
#include "socket_interface.hpp"
#include <iostream>

std::unique_ptr<SocketInterface> create_interface(
    const std::string INTERFACE_NAME)
{
    std::unique_ptr<SocketInterface> interface;

    if (INTERFACE_NAME == "UART")
    {
        interface = std::make_unique<UartSocketBridge>();
    }
    else
    {
        throw new std::runtime_error("Error: Invalid interface type");
    }

    return interface;
}

bool run_logic(std::unique_ptr<SocketInterface> interface,
               const std::string DEVICE_PATH,
               const std::string SOCKET_PATH)
{
    // Run setup methods
    if (!interface->attachToDevice(DEVICE_PATH))
    {
        throw new std::runtime_error("Error: Could not attach to device");
        return EXIT_FAILURE;
    }

    if (!interface->connectUnixSocket(SOCKET_PATH))
    {
        throw new std::runtime_error("Error: Could not connect to socket");
        return EXIT_FAILURE;
    }

    constexpr int TIMEOUT = 1000; // Change if needed. Default is 0
    if (!interface->setTimeout(TIMEOUT))
    {
        std::cerr << "Error: Could not set timeout" << std::endl;
    }

    // TODO Before you get protobuf running, just write to the socket for now

    interface->write(std::vector<uint8_t>{0x01, 0x02, 0x03, 0x04, 0x05});

    if (!interface->disconnect())
    {
        std::cerr << "Error: Could not disconnect gracefully" << std::endl;
    }

    return EXIT_SUCCESS;
}

// Pass arugments as
// ./middleware <socket type> <device path> <socket path>
int main(int argc, char *argv[])
{

    // Pick interface based on the first argument
    if (argc < 4)
    {
        std::cerr << "Error: Not enough arugments provided" << std::endl;
        // Throw error silenced by main
        throw new std::runtime_error("Error: Not enough arugments provided");
        return EXIT_FAILURE;
    }
    else if (argc > 4)
    {
        std::cerr << "Warning: Too many arugments provided" << std::endl;
    }

    std::unique_ptr<SocketInterface> interface = create_interface(std::string(argv[1]));
    const std::string DEVICE_PATH = std::string(argv[2]);
    const std::string SOCKET_PATH = std::string(argv[3]);

    return run_logic(std::move(interface), DEVICE_PATH, SOCKET_PATH);
}