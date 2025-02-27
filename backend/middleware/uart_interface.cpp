// uart_interface.cpp
#include "uart_interface.hpp"
#include <fcntl.h>
#include <unistd.h>
#include <termios.h>
#include <system_error>
#include <algorithm>
#include <iostream>
#include <chrono>
#include <sstream>
#include <iomanip>
#include <cstring>
#include <thread>
#include <sys/select.h>
#include "process_logging.hpp"

UartInterface::UartInterface(const std::string &device_path, int baud_rate)
    : baud_rate_(baud_rate), device_path_(device_path) {}

UartInterface::~UartInterface()
{
    // If file descriptor indicates it is open, close it
    if (uart_fd_ >= 0)
        close(uart_fd_);
}

bool UartInterface::initialize()
{

    uart_fd_ = open(device_path_.c_str(), O_RDWR | O_NOCTTY | O_SYNC);
    if (uart_fd_ < 0)
    {
        process_logging::error("Failed to open UART device: " + device_path_);
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
        throw std::system_error(errno, std::system_category(), "tcgetattr failed");
    }

    cfsetospeed(&tty, baud_rate_);
    cfsetispeed(&tty, baud_rate_);

    // 8N1 configuration
    tty.c_cflag &= ~PARENB; // No parity
    tty.c_cflag &= ~CSTOPB; // 1 stop bit
    tty.c_cflag &= ~CSIZE;
    tty.c_cflag |= CS8;    // 8 data bits
    tty.c_cflag |= CREAD;  // Enable receiver
    tty.c_cflag |= CLOCAL; // Ignore modem controls

    // Raw input/output
    tty.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG);
    tty.c_iflag &= ~(IXON | IXOFF | IXANY | IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL);
    tty.c_oflag &= ~OPOST;

    // Timeout configuration (0.5s)
    tty.c_cc[VMIN] = 0;
    tty.c_cc[VTIME] = 5;

    if (tcsetattr(uart_fd_, TCSANOW, &tty) != 0)
    {
        throw std::system_error(errno, std::system_category(), "tcsetattr failed");
    }

    at_setup();
}

void UartInterface::at_setup()
{
    process_logging::debug("AT setup TEST");
    process_logging::debug("Connecting to LoRa E5...");

    // Retry AT command until successful
    bool module_found = false;
    while (!module_found)
    {
        module_found = at_send_command("AT", "+AT: OK", 100);
        if (!module_found)
        {
            process_logging::error("No E5 module found");
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }

    process_logging::debug("E5 module found");
    // Configuration sequence
    at_send_command("AT+MODE=TEST", "+MODE: TEST", 1000);
    // Returns like:
    // +TEST: RFCFG F:915000000, SF9, BW500K, TXPR:12, RXPR:16, POW:14dBm, CRC:OFF, IQ:OFF, NET:OFF
    at_send_command("AT+TEST=RFCFG,915,SF9,500,12,16,14,OFF,OFF,OFF",
                    "+TEST: RFCFG", 1000);

    // Uncomment to change baud rate (requires module reset)
    // if (at_send_command("AT+UART=BR, 230400", "+UART=BR, 230400", 1000)) {
    //     at_send_command("AT+RESET", "+RESET: OK, 9600", 1000);
    //     std::this_thread::sleep_for(std::chrono::milliseconds(2000));
    //     // Reinitialize with new baud rate here if needed
    // }

    at_send_command("AT+TEST=RXLRPKT", "+TEST: RXLRPKT", 1000);
    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    process_logging::debug("End of Setup...");
}

std::vector<uint8_t> UartInterface::read_with_timeout(int timeout_ms)
{
    std::vector<uint8_t> buffer;
    fd_set set;
    timeval timeout{};

    FD_ZERO(&set);
    FD_SET(uart_fd_, &set);

    timeout.tv_sec = timeout_ms / 1000;
    timeout.tv_usec = (timeout_ms % 1000) * 1000;

    int result = select(uart_fd_ + 1, &set, nullptr, nullptr, &timeout);
    if (result > 0)
    {
        std::vector<uint8_t> temp_buf(512);
        ssize_t n = read(uart_fd_, temp_buf.data(), temp_buf.size());
        if (n > 0)
        {
            buffer.insert(buffer.end(), temp_buf.begin(), temp_buf.begin() + n);
        }
    }
    else
    {
        process_logging::error("Timeout or error while reading from UART");
    }
    return buffer;
}

static std::string bytes_to_hex(const std::vector<uint8_t> &data)
{
    std::ostringstream oss;
    oss << std::hex << std::uppercase << std::setfill('0');
    for (uint8_t byte : data)
    {
        oss << std::setw(2) << static_cast<int>(byte);
    }
    return oss.str();
}

/// @brief Write data to the serial port. This is lower level then write_data which writes data to the LoRa band though this function
/// @param data raw serial data
/// @return amount of bytes written
ssize_t UartInterface::write_serial(const std::vector<uint8_t> &data)
{
    if (uart_fd_ < 0)
        return -1;

    ssize_t written = write(uart_fd_, data.data(), data.size());
    if (written < 0)
    {
        process_logging::error("Failed to write to serial port");
        throw std::system_error(errno, std::system_category(),
                                "Serial write failed");
    }
    return written;
}

bool UartInterface::at_send_command(const std::string &command,
                                    const std::string &expected_response,
                                    int timeout_ms)
{
    // Send command with CRLF termination using direct serial write
    std::string full_command = command + "\r\n";
    std::vector<uint8_t> cmd_data(full_command.begin(), full_command.end());

    if (write_serial(cmd_data) != static_cast<ssize_t>(cmd_data.size()))
    {
        process_logging::error("Failed to send AT command: " + command);
        return false;
    }

    // Read response
    auto response = read_with_timeout(timeout_ms);
    std::string response_str(response.begin(), response.end());

    // Check for expected response
    if (response_str.find(expected_response) != std::string::npos)
    {
        process_logging::debug("AT command successful: " + command);
        return true;
    }

    process_logging::error("AT command failed. Expected: " + expected_response +
                           ", Received: " + response_str);
    return false;
}

// ssize_t UartInterface::read_data(std::vector<uint8_t> &buffer)
// {
//     if (uart_fd_ < 0)
//     {
//         process_logging::error("UART file descriptor is invalid");
//         return -1;
//     }

//     // Responses looks like this
//     // ...

//     // +TEST: LEN:32, RSSI:-46, SNR:10
//     // +TEST: RX "0400FFEA0838001FFFDA0400FFC1FFEB0007FFA73C6DAABE0000000000000000"

//     // +TEST: LEN:32, RSSI:-45, SNR:10
//     // +TEST: RX "0400001908490042FFCD03F7FFCFFFC0002DFFE93C6DAABE0000000000000000"

//     // ...

//     // Put into read mode
//     at_send_command("AT+TEST=RXLRPKT", "+TEST: RXLRPKT", 1000);
//     ssize_t count = read(uart_fd_, buffer.data(), buffer.size());
//     if (count < 0)
//     {
//         throw std::system_error(errno, std::system_category(),
//                                 "TEST UART read failed");
//     }
//     return count;
// }

ssize_t UartInterface::read_data(std::vector<uint8_t> &buffer)
{
    if (uart_fd_ < 0)
    {
        process_logging::error("UART file descriptor is invalid");
        return -1;
    }

    // Responses looks like this
    // ...

    // +TEST: LEN:32, RSSI:-46, SNR:10
    // +TEST: RX "0400FFEA0838001FFFDA0400FFC1FFEB0007FFA73C6DAABE0000000000000000"

    // +TEST: LEN:32, RSSI:-45, SNR:10
    // +TEST: RX "0400001908490042FFCD03F7FFCFFFC0002DFFE93C6DAABE0000000000000000"

    // ...

    // Read all available data with timeout
    auto raw_data = read_with_timeout(1000); // 1 second timeout
    std::string data(raw_data.begin(), raw_data.end());

    int rssi = 0;
    int snr = 0;
    std::vector<uint8_t> payload;
    size_t payload_size = 0;

    // Split response into lines
    std::istringstream stream(data);
    std::string line;
    while (std::getline(stream, line))
    {
        // Clean up line endings
        line.erase(std::remove(line.begin(), line.end(), '\r'), line.end());
        line.erase(std::remove(line.begin(), line.end(), '\n'), line.end());

        if (line.find("+TEST: LEN:") == 0)
        {
            // Parse signal metrics
            size_t rssi_pos = line.find("RSSI:");
            size_t snr_pos = line.find("SNR:");

            if (rssi_pos != std::string::npos && snr_pos != std::string::npos)
            {
                rssi = std::stoi(line.substr(rssi_pos + 5, snr_pos - (rssi_pos + 5) - 2));
                snr = std::stoi(line.substr(snr_pos + 4));

                // Signal quality checks
                if (rssi < -85)
                { // Critical RSSI threshold
                    process_logging::warning("Poor signal strength (RSSI: " +
                                             std::to_string(rssi) + " dBm)");
                }
                if (snr < 5)
                { // Critical SNR threshold
                    process_logging::warning("Low signal-to-noise ratio (SNR: " +
                                             std::to_string(snr) + " dB)");
                }
            }
        }
        else if (line.find("+TEST: RX \"") == 0)
        {
            // Extract hex payload
            size_t start = line.find('\"') + 1;
            size_t end = line.find('\"', start);
            if (end != std::string::npos)
            {
                std::string hex_str = line.substr(start, end - start);
                payload = hex_string_to_bytes(hex_str);
                payload_size = payload.size();
            }
        }
    }

    // Copy payload to output buffer
    if (!payload.empty())
    {
        if (buffer.size() < payload_size)
        {
            buffer.resize(payload_size);
        }
        std::copy(payload.begin(), payload.end(), buffer.begin());
    }

    return payload_size;
}

std::vector<uint8_t> UartInterface::hex_string_to_bytes(const std::string &hex)
{
    std::vector<uint8_t> bytes;
    for (size_t i = 0; i < hex.length(); i += 2)
    {
        std::string byte_str = hex.substr(i, 2);
        uint8_t byte = static_cast<uint8_t>(std::stoul(byte_str, nullptr, 16));
        bytes.push_back(byte);
    }
    return bytes;
}

/// @brief Write serial data to the LoRa band through the LoRa interface
/// @param data
/// @return
ssize_t UartInterface::write_data(const std::vector<uint8_t> &data)
{
    if (uart_fd_ < 0)
        return -1;

    // Convert binary data to hex string
    std::string hex_payload = bytes_to_hex(data);

    // Format AT command for pure packet TX
    std::string command = "AT+TEST=TXLRPKT, \"" + hex_payload + '\"';

    bool success = at_send_command(command, "+TEST: TX DONE", 1000);

    if (success)
    {
        return data.size();
    }
    else
    {
        process_logging::error("LoRa transmission failed");
        return -1;
    }
}