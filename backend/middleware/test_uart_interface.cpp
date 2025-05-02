// uart_test_interface.cpp
#include "test_uart_interface.hpp"

#include <fcntl.h>
#include <sys/select.h>
#include <termios.h>
#include <unistd.h>

#include <algorithm>
#include <chrono>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <system_error>
#include <thread>

#include "subprocess_logging.hpp"
#include "uart_interface.hpp"

TestUartInterface::TestUartInterface(const std::string &device_path,
                                     int baud_rate)
    : baud_rate_(baud_rate), device_path_(device_path) {}

TestUartInterface::~TestUartInterface() {
  std::lock_guard<std::recursive_mutex> lock(io_mutex_);
  // If file descriptor indicates it is open, close it
  if (uart_fd_ >= 0) close(uart_fd_);
}

bool TestUartInterface::initialize() {
  std::lock_guard<std::recursive_mutex> lock(io_mutex_);
  uart_fd_ = open(device_path_.c_str(), O_RDWR | O_NOCTTY | O_SYNC);
  if (uart_fd_ < 0) {
    slogger::error("Failed to open UART TEST device: " + device_path_);
    throw std::system_error(errno, std::system_category(),
                            "Failed to open UART TEST device");
  }

  configure_test_uart();
  slogger::debug("" + device_path_ + " opened successfully");
  return true;
}

void TestUartInterface::configure_test_uart() {
  struct termios tty;
  if (tcgetattr(uart_fd_, &tty) != 0) {
    throw std::system_error(errno, std::system_category(), "tcgetattr failed");
  }

  cfsetospeed(&tty, baud_rate_);
  cfsetispeed(&tty, baud_rate_);

  tty.c_cflag = (tty.c_cflag & ~CSIZE) | CS8;  // 8-bit chars
  tty.c_iflag &=
      ~(IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL | IXON);
  tty.c_oflag = 0;
  tty.c_lflag = 0;

  tty.c_cc[VMIN] = 0;   // read doesn't block
  tty.c_cc[VTIME] = 5;  // 0.5 seconds read timeout

  // Timeout configuration (0.5s)
  tty.c_cc[VMIN] = 0;
  tty.c_cc[VTIME] = 5;

  if (tcsetattr(uart_fd_, TCSANOW, &tty) != 0) {
    throw std::system_error(errno, std::system_category(), "tcsetattr failed");
  }
}

/// @brief
/// @param buffer
/// @return Returns amount of bytes read. -1 if failed
ssize_t TestUartInterface::read_data(std::vector<uint8_t> &buffer) {
  std::lock_guard<std::recursive_mutex> lock(io_mutex_);
  if (uart_fd_ < 0) {
    slogger::error("UART file descriptor is invalid");
    return -1;
  }

  // Responses looks like this
  // ...

  // +TEST: LEN:32, RSSI:-46, SNR:10
  // +TEST: RX
  // "0400FFEA0838001FFFDA0400FFC1FFEB0007FFA73C6DAABE0000000000000000"

  // +TEST: LEN:32, RSSI:-45, SNR:10
  // +TEST: RX
  // "0400001908490042FFCD03F7FFCFFFC0002DFFE93C6DAABE0000000000000000"

  // ...

  int rssi = 0;
  int snr = 0;
  std::vector<uint8_t> payload;
  size_t payload_size = 0;

  // Process complete messages in buffer
  size_t message_end;
  ssize_t count = read(uart_fd_, buffer.data(), buffer.size());

  std::string buffer_string =
      std::string(buffer.begin(), buffer.begin() + count);
  while ((message_end = buffer_string.find("\r\n")) != std::string::npos) {
    std::string message = buffer_string.substr(0, message_end);
    buffer_string.erase(0, message_end + 2);  // Remove processed message

    // Clean up any remaining line endings
    message.erase(std::remove(message.begin(), message.end(), '\r'),
                  message.end());
    message.erase(std::remove(message.begin(), message.end(), '\n'),
                  message.end());
    // Parse message content

    if (message.find("+TEST: LEN:") == 0) {
      size_t rssi_pos = message.find("RSSI:");
      size_t snr_pos = message.find("SNR:");

      if (rssi_pos != std::string::npos && snr_pos != std::string::npos) {
        try {
          rssi = std::stoi(
              message.substr(rssi_pos + 5, snr_pos - (rssi_pos + 5) - 2));
          snr = std::stoi(message.substr(snr_pos + 4));

          // Signal quality monitoring
          constexpr int RSSI_THRESHOLD = -85;
          constexpr int SNR_THRESHOLD = 10;
          if (rssi < RSSI_THRESHOLD) {
            slogger::warning("Poor RSSI: " + std::to_string(rssi) + " dBm");
          }
          if (snr > SNR_THRESHOLD) {
            slogger::warning("High SNR: " + std::to_string(snr));
          }
        } catch (const std::exception &e) {
          slogger::error("Failed to parse metrics: " + std::string(e.what()));
        }
      }
    } else if (message.find("+TEST: RX\"") != std::string::npos) {
      // IDK why but for some reason this needs the \" not to be matched in
      // comparison to the actual UART
      size_t payload_start = message.find('\"') + 1;
      size_t payload_end = message.find('\"', payload_start);
      if (payload_end != std::string::npos) {
        try {
          std::string hex_str =
              message.substr(payload_start, payload_end - payload_start);
          payload = UartInterface::hex_string_to_bytes(hex_str);

          float rssi_float = static_cast<float>(rssi);
          float snr_float = static_cast<float>(snr);

          // Convert to big-endian bytes
          auto rssi_bytes = float_to_be_bytes(rssi_float);
          auto snr_bytes = float_to_be_bytes(snr_float);

          // Insert at index 1 (after 1st byte)
          if (!payload.empty()) {
            // Ensure we have at least 1 byte for the ID
            payload.insert(payload.begin() + 1, rssi_bytes.begin(),
                           rssi_bytes.end());
            payload.insert(payload.begin() + 5,  // 1 + 4 bytes
                           snr_bytes.begin(), snr_bytes.end());
          } else {
            slogger::warning("Empty payload, skipping metrics insertion");
          }

          payload_size = payload.size();
        } catch (const std::exception &e) {
          slogger::error("Payload conversion failed: " + std::string(e.what()));
        }
      }
    }
  }

  // Copy payload to output buffer if valid
  if (!payload.empty()) {
    try {
      if (buffer.size() < payload_size) {
        buffer.resize(payload_size);
      }
      std::copy(payload.begin(), payload.end(), buffer.begin());
    } catch (const std::exception &e) {
      slogger::error("Buffer copy failed: " + std::string(e.what()));
      return -1;
    }
  }

  return payload_size;
}

/// @brief Write serial data to the LoRa band through the LoRa interface
/// @param data Binary data bytes
/// @return
ssize_t TestUartInterface::write_data(const std::vector<uint8_t> &data) {
  // Write to the Aether. This doesn't actually do anything
  return static_cast<ssize_t>(data.size());
}