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
  static std::vector<uint8_t> hex_string_to_bytes(const std::string &hex);

 private:
  std::recursive_mutex io_mutex_;
  int baud_rate_;
  int uart_fd_ = -1;
  std::string device_path_;
  std::string response_buffer_;

  constexpr static int AT_TIMEOUT_MS = 1000;

  // Enums to track if you need to override continuous modes
  enum ModemContinuousState {
    NOT_CONTINUOUS,
    TXCW,     // Not currently used
    TXCLORA,  // Not currently used
    RXLRPKT,  // Basic RX
  };
  // Keep track if you're currently in a continuous mode
  ModemContinuousState modem_state_;

  bool at_send_command(
      const std::string &command, const std::string &expected_response,
      const int timeout_ms = AT_TIMEOUT_MS,
      const ModemContinuousState = ModemContinuousState::NOT_CONTINUOUS);
  void configure_uart();
  void at_setup();
  // https://files.seeedstudio.com/products/317990687/res/LoRa-E5+AT+Command+Specification_V1.0+.pdf#page=52

  ssize_t write_serial(const std::vector<uint8_t> &data);
  std::vector<uint8_t> read_with_timeout(int timeout_ms);
};