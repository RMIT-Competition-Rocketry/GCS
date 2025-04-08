// uart_interface.cpp
#include "uart_interface.hpp"

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

UartInterface::UartInterface(const std::string &device_path, int baud_rate)
    : baud_rate_(baud_rate),
      device_path_(device_path),
      modem_state_(ModemContinuousState::NOT_CONTINUOUS) {}

UartInterface::~UartInterface() {
  std::lock_guard<std::recursive_mutex> lock(io_mutex_);
  // If file descriptor indicates it is open, close it
  if (uart_fd_ >= 0) close(uart_fd_);
}

bool UartInterface::initialize() {
  std::lock_guard<std::recursive_mutex> lock(io_mutex_);
  uart_fd_ = open(device_path_.c_str(), O_RDWR | O_NOCTTY | O_SYNC);
  if (uart_fd_ < 0) {
    slogger::error("Failed to open UART device: " + device_path_);
    throw std::system_error(errno, std::system_category(),
                            "Failed to open UART device");
  }

  configure_uart();
  return true;
}

void UartInterface::configure_uart() {
  struct termios tty;
  if (tcgetattr(uart_fd_, &tty) != 0) {
    throw std::system_error(errno, std::system_category(), "tcgetattr failed");
  }

  cfsetospeed(&tty, baud_rate_);
  cfsetispeed(&tty, baud_rate_);

  // 8N1 configuration
  tty.c_cflag &= ~PARENB;  // No parity
  tty.c_cflag &= ~CSTOPB;  // 1 stop bit
  tty.c_cflag &= ~CSIZE;
  tty.c_cflag |= CS8;     // 8 data bits
  tty.c_cflag |= CREAD;   // Enable receiver
  tty.c_cflag |= CLOCAL;  // Ignore modem controls

  // Raw input/output
  tty.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG);
  tty.c_iflag &= ~(IXON | IXOFF | IXANY | IGNBRK | BRKINT | PARMRK | ISTRIP |
                   INLCR | IGNCR | ICRNL);
  tty.c_oflag &= ~OPOST;

  // Timeout configuration (0.5s)
  tty.c_cc[VMIN] = 0;
  tty.c_cc[VTIME] = 5;

  if (tcsetattr(uart_fd_, TCSANOW, &tty) != 0) {
    throw std::system_error(errno, std::system_category(), "tcsetattr failed");
  }

  at_setup();
}

void UartInterface::at_setup() {
  slogger::info("AT setup TEST");
  slogger::info("Connecting to LoRa E5...");

  // Retry AT command until successful
  bool module_found = false;
  while (!module_found) {
    module_found = at_send_command("AT", "+AT: OK", 100);
    if (!module_found) {
      slogger::error("No E5 module found");
      std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
  }

  slogger::info("E5 module found");
  // Configuration sequence
  at_send_command("AT+MODE=TEST", "+MODE: TEST", 1000);
  // Returns like:
  // +TEST: RFCFG F:915000000, SF9, BW500K, TXPR:12, RXPR:16, POW:14dBm,
  // CRC:OFF, IQ:OFF, NET:OFF
  at_send_command("AT+TEST=RFCFG,915,SF9,500,12,16,14,OFF,OFF,OFF",
                  "+TEST: RFCFG", 1000);

  // Uncomment to change baud rate (requires module reset)
  // if (at_send_command("AT+UART=BR, 230400", "+UART=BR, 230400", 1000)) {
  //     at_send_command("AT+RESET", "+RESET: OK, 9600", 1000);
  //     std::this_thread::sleep_for(std::chrono::milliseconds(2000));
  //     // Reinitialize with new baud rate here if needed
  // }

  at_send_command("AT+TEST=RXLRPKT", "+TEST: RXLRPKT", 1000,
                  ModemContinuousState::RXLRPKT);
  // std::this_thread::sleep_for(std::chrono::milliseconds(200));

  slogger::info("End of Setup...");
}

std::vector<uint8_t> UartInterface::read_with_timeout(int timeout_ms) {
  std::vector<uint8_t> buffer;
  fd_set set;
  timeval timeout{};
  constexpr int chunk_size = 128;  // Arbitrary

  FD_ZERO(&set);
  FD_SET(uart_fd_, &set);

  timeout.tv_sec = timeout_ms / 1000;
  timeout.tv_usec = (timeout_ms % 1000) * 1000;

  while (true) {
    int result = select(uart_fd_ + 1, &set, nullptr, nullptr, &timeout);
    if (result > 0) {
      std::vector<uint8_t> temp_buf(chunk_size);
      ssize_t n = read(uart_fd_, temp_buf.data(), temp_buf.size());
      if (n > 0) {
        buffer.insert(buffer.end(), temp_buf.begin(), temp_buf.begin() + n);
        // Continue reading while data is immediately available
        timeout.tv_sec = 0;
        timeout.tv_usec = 10000;  // 10ms subsequent timeout
      } else {
        break;
      }
    } else {
      break;
    }
  }
  return buffer;
}

static std::string bytes_to_hex(const std::vector<uint8_t> &data) {
  std::ostringstream oss;
  oss << std::hex << std::uppercase << std::setfill('0');
  for (uint8_t byte : data) {
    oss << std::setw(2) << static_cast<int>(byte);
  }
  return oss.str();
}

/// @brief Write data to the serial port. This is lower level then write_data
/// which writes data to the LoRa band though this function
/// @param data raw serial data
/// @return amount of bytes written
ssize_t UartInterface::write_serial(const std::vector<uint8_t> &data) {
  if (uart_fd_ < 0) return -1;

  ssize_t written = write(uart_fd_, data.data(), data.size());
  if (written < 0) {
    slogger::error("Failed to write to serial port");
    throw std::system_error(errno, std::system_category(),
                            "Serial write failed");
  }
  return written;
}

bool UartInterface::at_send_command(const std::string &command,
                                    const std::string &expected_response,
                                    const int timeout_ms,
                                    const ModemContinuousState modem_state) {
  // Optimisation. Do not enter mode if already in it
  switch (modem_state) {
    case ModemContinuousState::RXLRPKT:
      if (modem_state_ == ModemContinuousState::RXLRPKT) {
        return true;
      }
      break;
    default:
      // Other states not currently used
      break;
  }

  // Clear buffer before new command
  response_buffer_.clear();

  std::string full_command = command + "\r\n";
  slogger::debug("Sending AT command: " + full_command);
  std::vector<uint8_t> cmd_data(full_command.begin(), full_command.end());

  if (write_serial(cmd_data) != static_cast<ssize_t>(cmd_data.size())) {
    slogger::error("Failed to send AT command: " + command);
    return false;
  }

  auto start = std::chrono::steady_clock::now();
  bool response_found = false;

  while (!response_found) {
    auto elapsed = std::chrono::steady_clock::now() - start;
    if (std::chrono::duration_cast<std::chrono::milliseconds>(elapsed).count() >
        timeout_ms) {
      slogger::warning("AT command timed out: " + command);
      break;
    }

    auto raw_data = read_with_timeout(100);
    response_buffer_ += std::string(raw_data.begin(), raw_data.end());

    // // Remove echo of the command itself
    // size_t echo_pos = response_buffer_.find(command);
    // if (echo_pos != std::string::npos) {
    //   // Find the end of the echo (either \r\n or just to the end of the
    //   echoed
    //   // command)
    //   size_t echo_end = response_buffer_.find("\r\n", echo_pos);
    //   if (echo_end != std::string::npos) {
    //     // Remove the echo and the line ending
    //     response_buffer_.erase(echo_pos, (echo_end + 2) - echo_pos);
    //   } else {
    //     // If no line ending found, just remove the command part
    //     response_buffer_.erase(echo_pos, command.length());
    //   }
    // }

    // Check for expected response
    if (response_buffer_.find(expected_response) != std::string::npos) {
      response_found = true;
      slogger::debug("AT command successful: " + command);

      // Clean buffer after successful match
      size_t pos = response_buffer_.find(expected_response);
      response_buffer_.erase(0, pos + expected_response.length());
      break;
    }

    // Check for common error responses
    if (response_buffer_.find("ERROR") != std::string::npos) {
      break;
    }

    std::this_thread::sleep_for(std::chrono::milliseconds(10));
  }

  if (!response_found) {
    slogger::error("AT command failed. Expected: " + expected_response +
                   ", Buffer Content: " + response_buffer_);
    response_buffer_.clear();
    return false;
  }

  return true;
}

/// @brief
/// @param buffer
/// @return Returns amount of bytes read. -1 if failed
ssize_t UartInterface::read_data(std::vector<uint8_t> &buffer) {
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

  // Start listening (don't check git blame timestamp)
  if (modem_state_ != ModemContinuousState::RXLRPKT) {
    at_send_command("AT+TEST=RXLRPKT", "+TEST: RXLRPKT", 1000,
                    ModemContinuousState::RXLRPKT);
  }

  // Read new data and append to persistent buffer
  auto raw_data = read_with_timeout(1000);
  response_buffer_.append(raw_data.begin(), raw_data.end());

  int rssi = 0;
  int snr = 0;
  std::vector<uint8_t> payload;
  size_t payload_size = 0;

  // Process complete messages in buffer
  size_t message_end;
  while ((message_end = response_buffer_.find("\r\n")) != std::string::npos) {
    std::string message = response_buffer_.substr(0, message_end);
    response_buffer_.erase(0, message_end + 2);  // Remove processed message

    // Clean up any remaining line endings
    message.erase(std::remove(message.begin(), message.end(), '\r'),
                  message.end());
    message.erase(std::remove(message.begin(), message.end(), '\n'),
                  message.end());

    if (!message.empty()) {
      slogger::debug("Received message from interface: " + message);
    }

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
          constexpr int SNR_THRESHOLD = 5;
          if (rssi < RSSI_THRESHOLD) {
            slogger::warning("Poor RSSI: " + std::to_string(rssi) + " dBm");
          }
          if (snr < SNR_THRESHOLD) {
            slogger::warning("Low SNR: " + std::to_string(snr) + " dB");
          }
        } catch (const std::exception &e) {
          slogger::error("Failed to parse metrics: " + std::string(e.what()));
        }
      }
    } else if (message.find("+TEST: RX \"") == 0) {
      size_t payload_start = message.find('\"') + 1;
      size_t payload_end = message.find('\"', payload_start);

      if (payload_end != std::string::npos) {
        try {
          std::string hex_str =
              message.substr(payload_start, payload_end - payload_start);
          payload = hex_string_to_bytes(hex_str);
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

std::vector<uint8_t> UartInterface::hex_string_to_bytes(
    const std::string &hex) {
  std::vector<uint8_t> bytes;
  for (size_t i = 0; i < hex.length(); i += 2) {
    std::string byte_str = hex.substr(i, 2);
    uint8_t byte = static_cast<uint8_t>(std::stoul(byte_str, nullptr, 16));
    bytes.push_back(byte);
  }
  return bytes;
}

/// @brief Write serial data to the LoRa band through the LoRa interface
/// @param data Binary data bytes
/// @return
ssize_t UartInterface::write_data(const std::vector<uint8_t> &data) {
  std::lock_guard<std::recursive_mutex> lock(io_mutex_);
  if (uart_fd_ < 0) {
    slogger::error("Uart device unavailable for write");
    return -1;
  }

  // Convert binary data to hex string
  std::string hex_payload = bytes_to_hex(data);

  // Format AT command for pure packet TX
  std::string command = "AT+TEST=TXLRPKT, \"" + hex_payload + '\"';
  bool success = at_send_command(command, "+TEST: TX DONE", 1000);
  if (success) {
    return data.size();
  } else {
    slogger::error("LoRa transmission failed");
    return -1;
  }
}