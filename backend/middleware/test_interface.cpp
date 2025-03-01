#include "test_interface.hpp"
#include <fcntl.h>
#include <unistd.h>
#include <termios.h>
#include <system_error>
#include <iostream>
#include <cstring>
#include "process_logging.hpp"

TestInterface::TestInterface(const std::string &device_path, int baud_rate)
    : baud_rate_(baud_rate), device_path_(device_path) {}

TestInterface::~TestInterface()
{
    // If file descriptor indicates it is open, close it
    if (uart_fd_ >= 0)
        close(uart_fd_);
}

bool TestInterface::initialize()
{

    uart_fd_ = open(device_path_.c_str(), O_RDWR | O_NOCTTY | O_SYNC);
    if (uart_fd_ < 0)
    {
        process_logging::error("Error: Failed to open TEST UART device: " + device_path_);
        throw std::system_error(errno, std::system_category(),
                                "Failed to open TEST UART device");
    }

    configure_test_interface();
    return true;
}

void TestInterface::configure_test_interface()
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

ssize_t TestInterface::read_data(std::vector<uint8_t> &buffer)
{
    if (uart_fd_ < 0)
    {
        process_logging::error("TEST UART file descriptor is invalid");
        return -1;
    }

    ssize_t count = read(uart_fd_, buffer.data(), buffer.size());
    if (count < 0)
    {
        throw std::system_error(errno, std::system_category(),
                                "TEST UART read failed");
    }
    return count;
}

ssize_t TestInterface::write_data(const std::vector<uint8_t> &data)
{
    if (uart_fd_ < 0)
        return -1;

    ssize_t written = write(uart_fd_, data.data(), data.size());
    if (written < 0)
    {
        throw std::system_error(errno, std::system_category(),
                                "TEST UART write failed");
    }
    return written;
}