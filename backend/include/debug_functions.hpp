#pragma once

#include <iomanip>
#include <sstream>

namespace debug {

static std::string vectorToHexString(const std::vector<uint8_t> &data,
                                     const ssize_t BUFFER_BYTE_COUNT) {
  std::ostringstream oss;
  oss << std::uppercase << std::hex << std::setfill('0');
  if (BUFFER_BYTE_COUNT == 0) {
    return "Empty vector";
  }
  if (BUFFER_BYTE_COUNT > 255) {
    return "Vector too long: " + std::to_string(BUFFER_BYTE_COUNT);
  }
  if (BUFFER_BYTE_COUNT < 0) {
    return "Vector too short: " + std::to_string(BUFFER_BYTE_COUNT);
  }
  for (ssize_t i = 0; i < BUFFER_BYTE_COUNT; ++i) {
    oss << std::setw(2) << static_cast<int>(data[i]);
    if (i != BUFFER_BYTE_COUNT - 1) oss << " ";
  }
  return oss.str();
}

}  // namespace debug