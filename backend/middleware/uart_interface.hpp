#pragma once

#include "lora_interface.hpp"
#include <string>
#include <termios.h>

class UartInterface : public LoraInterface
{
public:
    UartInterface(
        const std::string &device_path,
        int baud_rate = B115200);
    virtual ~UartInterface();

    bool initialize() override;
    ssize_t read_data(std::vector<uint8_t> &buffer) override;
    ssize_t write_data(const std::vector<uint8_t> &data) override;

private:
    int baud_rate_;
    int uart_fd_ = -1;
    std::string device_path_;

    void configure_uart();
};
