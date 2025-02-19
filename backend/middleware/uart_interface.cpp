#include "uart_interface.hpp"
#include <fcntl.h>
#include <unistd.h>
#include <termios.h>
#include <system_error>
#include <iostream>
#include <cstring>

UartInterface::UartInterface(const std::string &device_path, int baud_rate)
    : baud_rate_(baud_rate), device_path_(device_path) {}

UartInterface::~UartInterface()
{
    if (uart_fd_ >= 0)
        close(uart_fd_);
}

bool UartInterface::initialize()
{
    uart_fd_ = open(device_path_.c_str(), O_RDWR | O_NOCTTY | O_SYNC);
    if (uart_fd_ < 0)
    {
        std::cerr << "Error: Failed to open UART device: " << device_path_ << std::endl;
        throw std::system_error(errno, std::system_category(),
                                "Failed to open UART device");
    }

    configure_uart();
    return true;
}

void UartInterface::configure_uart()
{
    struct termios tty;
    if (tcgetattr(uart_fd_, &tty) != 0)
    {
        throw std::system_error(errno, std::system_category(),
                                "tcgetattr failed");
    }

    cfsetospeed(&tty, baud_rate_);
    cfsetispeed(&tty, baud_rate_);

    tty.c_cflag = (tty.c_cflag & ~CSIZE) | CS8; // 8-bit chars
    tty.c_iflag &= ~(IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL | IXON);
    tty.c_oflag = 0;
    tty.c_lflag = 0;

    tty.c_cc[VMIN] = 0;  // read doesn't block
    tty.c_cc[VTIME] = 5; // 0.5 seconds read timeout

    if (tcsetattr(uart_fd_, TCSANOW, &tty) != 0)
    {
        throw std::system_error(errno, std::system_category(),
                                "tcsetattr failed");
    }
}

ssize_t UartInterface::read_data(std::vector<uint8_t> &buffer)
{
    if (uart_fd_ < 0)
    {
        std::cerr << "Error: UART file descriptor is invalid" << std::endl;
        return -1;
    }

    ssize_t count = read(uart_fd_, buffer.data(), buffer.size());
    if (count < 0)
    {
        throw std::system_error(errno, std::system_category(),
                                "UART read failed");
    }
    return count;
}

ssize_t UartInterface::write_data(const std::vector<uint8_t> &data)
{
    if (uart_fd_ < 0)
        return -1;

    ssize_t written = write(uart_fd_, data.data(), data.size());
    if (written < 0)
    {
        throw std::system_error(errno, std::system_category(),
                                "UART write failed");
    }
    return written;
}