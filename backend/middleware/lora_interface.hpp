#pragma once

// Abstract class that defines methods for interfacing with the LoRa module.

#include <arpa/inet.h>
#include <unistd.h>  // For ssize_t

#include <cstdint>
#include <cstring>
#include <vector>

class LoraInterface {
 public:
  virtual ~LoraInterface() = default;

  virtual bool initialize() = 0;
  virtual ssize_t read_data(std::vector<uint8_t> &buffer) = 0;
  virtual ssize_t write_data(const std::vector<uint8_t> &data) = 0;

 protected:
  /// @brief Convert native float value to big-endian byte array.
  /// @param VALUE
  /// @return Big endian byte array representation of the float value.
  static std::vector<uint8_t> float_to_be_bytes(const float VALUE) {
    uint32_t bits;
    static_assert(sizeof(VALUE) == sizeof(bits), "Float size mismatch");
    std::memcpy(&bits, &VALUE, sizeof(bits));
    bits = htonl(bits);  // To Big Endian
    return {static_cast<uint8_t>((bits >> 24) & 0xFF),
            static_cast<uint8_t>((bits >> 16) & 0xFF),
            static_cast<uint8_t>((bits >> 8) & 0xFF),
            static_cast<uint8_t>(bits & 0xFF)};
  }
};