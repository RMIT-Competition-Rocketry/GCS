#pragma once

// Abstract class that defines methods for interfacing with the LoRa module.

#include <unistd.h>  // For ssize_t

#include <cstdint>
#include <vector>

class LoraInterface {
 public:
  virtual ~LoraInterface() = default;

  virtual bool initialize() = 0;
  virtual ssize_t read_data(std::vector<uint8_t> &buffer) = 0;
  virtual ssize_t write_data(const std::vector<uint8_t> &data) = 0;
};