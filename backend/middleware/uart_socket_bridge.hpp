#pragma once
#include "socket_interface.hpp"
#include <sys/socket.h>
#include <sys/un.h>
#include <termios.h>

class UartSocketBridge : public SocketInterface
{
private:
    int uart_fd_ = -1;
    int socket_fd_ = -1;
    struct termios original_uart_config_;
    bool is_uart_open_ = false;
    bool is_socket_connected_ = false;
    std::string device_path_;
    std::string socket_path_;

public:
    UartSocketBridge() = default;
    ~UartSocketBridge();

    // Delete copy operations
    UartSocketBridge(const UartSocketBridge &) = delete;
    UartSocketBridge &operator=(const UartSocketBridge &) = delete;

    // Interface implementation
    bool attachToDevice(const std::string &devicePath) override;
    bool connectUnixSocket(const std::string &socketPath) override;
    bool disconnect() override;
    bool isConnected() const override { return is_uart_open_ && is_socket_connected_; }

    size_t write(const std::vector<uint8_t> &data) override;
    size_t read(std::vector<uint8_t> &buffer, size_t maxLength) override;
    bool setTimeout(int milliseconds) override;

private:
    bool configureUart();
    bool setupUnixSocket(const std::string &socketPath);
};