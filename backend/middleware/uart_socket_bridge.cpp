// uart_socket_bridge.cpp
#include "uart_socket_bridge.hpp"
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <iostream>

UartSocketBridge::~UartSocketBridge()
{
    disconnect();
}

bool UartSocketBridge::attachToDevice(const std::string &devicePath)
{
    uart_fd_ = ::open(devicePath.c_str(), O_RDWR | O_NOCTTY | O_NDELAY);
    if (uart_fd_ < 0)
    {
        std::cerr << "Error opening UART device: " << strerror(errno) << std::endl;
        return false;
    }

    if (!configureUart())
    {
        ::close(uart_fd_);
        uart_fd_ = -1;
        return false;
    }

    device_path_ = devicePath;
    is_uart_open_ = true;
    return true;
}

bool UartSocketBridge::connectUnixSocket(const std::string &socketPath)
{
    if (!setupUnixSocket(socketPath))
    {
        return false;
    }

    socket_path_ = socketPath;
    is_socket_connected_ = true;
    return true;
}

bool UartSocketBridge::disconnect()
{
    bool success = true;

    if (is_uart_open_)
    {
        if (tcsetattr(uart_fd_, TCSANOW, &original_uart_config_) < 0)
        {
            std::cerr << "Warning: Could not restore UART settings" << std::endl;
            success = false;
        }
        if (::close(uart_fd_) < 0)
        {
            std::cerr << "Error closing UART: " << strerror(errno) << std::endl;
            success = false;
        }
        uart_fd_ = -1;
        is_uart_open_ = false;
    }

    if (is_socket_connected_)
    {
        if (::close(socket_fd_) < 0)
        {
            std::cerr << "Error closing socket: " << strerror(errno) << std::endl;
            success = false;
        }
        socket_fd_ = -1;
        is_socket_connected_ = false;
        unlink(socket_path_.c_str()); // Remove the socket file
    }

    return success;
}

/// @brief Writes bytes to unix socket
/// @param data
/// @return Amount of bytes written
size_t UartSocketBridge::write(const std::vector<uint8_t> &data)
{
    if (!isConnected())
        return 0;

    // Write to Unix socket
    ssize_t bytes_written = ::write(socket_fd_, data.data(), data.size());
    if (bytes_written < 0)
    {
        std::cerr << "Socket write error: " << strerror(errno) << std::endl;
        return 0;
    }
    return static_cast<size_t>(bytes_written);
}

/// @brief Reads data from the UART connection
/// @param buffer Buffer to place bytes into
/// @param maxLength Maximum number of bytes to read
/// @return Amount of bytes read
size_t UartSocketBridge::read(std::vector<uint8_t> &buffer, size_t maxLength)
{
    if (!isConnected())
        return 0;

    // Read from UART
    buffer.resize(maxLength);
    ssize_t bytes_read = ::read(uart_fd_, buffer.data(), maxLength);
    if (bytes_read < 0)
    {
        std::cerr << "UART read error: " << strerror(errno) << std::endl;
        buffer.clear();
        return 0;
    }
    buffer.resize(bytes_read);
    return static_cast<size_t>(bytes_read);
}

/// @brief Set timeout for UART and socket
/// @param milliseconds
/// @return Any failure or success
bool UartSocketBridge::setTimeout(int milliseconds)
{
    if (!isConnected())
        return false;

    // Set UART timeout
    struct termios config;
    if (tcgetattr(uart_fd_, &config) < 0)
        return false;
    config.c_cc[VTIME] = milliseconds / 100;
    config.c_cc[VMIN] = 0;
    if (tcsetattr(uart_fd_, TCSANOW, &config) < 0)
        return false;

    // Set socket timeout
    struct timeval tv;
    tv.tv_sec = milliseconds / 1000;
    tv.tv_usec = (milliseconds % 1000) * 1000;
    return setsockopt(socket_fd_, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv)) >= 0;
}

bool UartSocketBridge::configureUart()
{
    if (tcgetattr(uart_fd_, &original_uart_config_) < 0)
        return false;

    struct termios config;
    memset(&config, 0, sizeof(config));

    // Basic 8N1 configuration
    config.c_cflag = CS8 | CLOCAL | CREAD;
    config.c_iflag = 0;
    config.c_oflag = 0;
    config.c_lflag = 0;

    return tcsetattr(uart_fd_, TCSANOW, &config) >= 0;
}

/// @brief Create the unix socket and return true if successful
/// @param socketPath
/// @return true if successful, false otherwise
bool UartSocketBridge::setupUnixSocket(const std::string &socketPath)
{
    // https://man7.org/linux/man-pages/man2/socket.2.html
    socket_fd_ = socket(AF_UNIX, SOCK_STREAM, 0);
    if (socket_fd_ < 0)
    {
        std::cerr << "Error creating Unix socket: " << strerror(errno) << std::endl;
        return false;
    }

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, socketPath.c_str(), sizeof(addr.sun_path) - 1);

    // Remove existing socket file if it exists
    unlink(socketPath.c_str());

    // https://man7.org/linux/man-pages/man2/bind.2.html
    if (bind(socket_fd_, (struct sockaddr *)&addr, sizeof(addr)) < 0)
    {
        std::cerr << "Error binding Unix socket: " << strerror(errno) << std::endl;
        ::close(socket_fd_);
        return false;
    }

    if (listen(socket_fd_, 1) < 0)
    {
        std::cerr << "Error listening on Unix socket: " << strerror(errno) << std::endl;
        ::close(socket_fd_);
        return false;
    }

    return true;
}