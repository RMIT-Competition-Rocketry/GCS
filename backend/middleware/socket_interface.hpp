#pragma once
#include <string>
#include <vector>
#include <memory>

class SocketInterface
{
public:
    virtual ~SocketInterface() = default;

    virtual bool attachToDevice(const std::string &devicePath) = 0;    // For UART
    virtual bool connectUnixSocket(const std::string &socketPath) = 0; // For Unix socket
    virtual bool disconnect() = 0;
    virtual bool isConnected() const = 0;

    // Data transmission
    virtual size_t write(const std::vector<uint8_t> &data) = 0;
    virtual size_t read(std::vector<uint8_t> &buffer, size_t maxLength) = 0;

    // Configuration
    virtual bool setTimeout(int milliseconds) = 0;
};
