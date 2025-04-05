// uart_interface.hpp
#pragma once

#include <termios.h>

#include <chrono>
#include <mutex>
#include <string>
#include <vector>

#include "lora_interface.hpp"

class UartInterface : public LoraInterface {
 public:
  UartInterface(
      const std::string &device_path = "/dev/ttyAMA0",
      int baud_rate = B230400);  // Default to RPi ttyAMA0 and 230400 baud
  virtual ~UartInterface();

  bool initialize() override;
  ssize_t read_data(std::vector<uint8_t> &buffer) override;
  ssize_t write_data(const std::vector<uint8_t> &data) override;

 private:
  std::recursive_mutex io_mutex_;
  int baud_rate_;
  int uart_fd_ = -1;
  std::string device_path_;
  std::string response_buffer_;

  bool at_send_command(const std::string &command,
                       const std::string &expected_response,
                       int timeout_ms = 1000);
  void configure_uart();
  void at_setup();
  ssize_t write_serial(const std::vector<uint8_t> &data);
  std::vector<uint8_t> read_with_timeout(int timeout_ms);
  std::vector<uint8_t> hex_string_to_bytes(const std::string &hex);
};