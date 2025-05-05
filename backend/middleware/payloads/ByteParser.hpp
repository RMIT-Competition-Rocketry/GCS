#pragma once

#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <stdexcept>

#include "subprocess_logging.hpp"

// A helper to sequentialy parse data bit by bit

constexpr int PROTOCOL_BYTE_SIZE = 8;

enum ByteOrder { BIG_ENDIAN_ORDER, LITTLE_ENDIAN_ORDER };

class ByteParser {
 public:
  /// @brief Provides a handler to safely extract bits from a byte array.
  /// @param data Incoming raw bytes
  /// @param num_bytes Amount of bytes in the data array
  /// @param endianness Byte order of the data (big-endian default)
  /// @throws std::out_of_range if you don't read the amount of bytes specified
  /// in the constructor

  ByteParser(const uint8_t *data, size_t num_bytes,
             ByteOrder endianness = ByteOrder::BIG_ENDIAN_ORDER)

      : data_(data),
        size_(num_bytes),
        byte_index_(0),
        bit_offset_(0),
        endianness_(endianness) {}

#ifdef DEBUG
  ~ByteParser() {
    if (bits_remaining() != 0) {
      slogger::critical(
          "ByteParser destroyed without consuming all data. Processed " +
          std::to_string(byte_index_) + " of " + std::to_string(size_) +
          " bytes (bit offset: " + std::to_string(bit_offset_) + ")");
    }
    // I don't care this kills everything. I want it to fail ASAP in debug
    assert(bits_remaining() == 0);
  }
#else
  ~ByteParser() = default;
#endif

  uint32_t extract_unsigned_bits(const uint8_t num_bits) {
    if (num_bits == 0) {
      return 0;
    }

    if (num_bits > 32 || num_bits > bits_remaining()) {
      throw std::out_of_range("Invalid bit extraction request.");
    }

    uint32_t result = 0;

    for (uint8_t i = 0; i < num_bits; ++i) {
      if (byte_index_ >= size_) break;

      // Black magic looking code:
      // Extracting the current bit from the byte
      //    - `data_[byte_index_]` is the current byte
      //    - `(7 - bit_offset_)` calculates the position of the bit within the
      //    byte
      //    - `>>` shifts the bit to the least significant position
      //    - `& 0x01` masks out all other bits
      //    - `|` appends the bit to the result
      result =
          (result << 1) | ((data_[byte_index_] >> (7 - bit_offset_)) & 0x01);
      bit_offset_ = (bit_offset_ + 1) % PROTOCOL_BYTE_SIZE;
      if (bit_offset_ == 0) {
        ++byte_index_;
      }
    }

    // If little-endian, reverse the byte order of the result
    if (endianness_ == LITTLE_ENDIAN_ORDER) {
      uint8_t bytes_used = (num_bits + 7) / PROTOCOL_BYTE_SIZE;
      result = swap_byte_order(result, bytes_used);
    }

    return result;
  }

  /// @brief Swaps byte order for multi-byte values.
  static uint32_t swap_byte_order(uint32_t value, uint8_t num_bytes) {
    uint32_t result = 0;
    for (uint8_t i = 0; i < num_bytes; ++i) {
      result |= ((value >> (PROTOCOL_BYTE_SIZE * i)) & 0xFF)
                << (PROTOCOL_BYTE_SIZE * (num_bytes - 1 - i));
    }
    return result;
  }

  int32_t extract_signed_bits(const uint8_t num_bits) {
    if (num_bits == 0) {
      return 0;
    }

    if (num_bits > 32) {
      throw std::out_of_range("Invalid bit extraction request.");
    }

    uint32_t value = extract_unsigned_bits(num_bits);

    if (num_bits < 32) {
      if (value & (1 << (num_bits - 1))) {  // Check sign bit
        value |= (~((1 << num_bits) - 1));  // Sign extend
      }
    }

    return static_cast<int32_t>(value);
  }

  std::string extract_string(uint8_t num_chars) {
    std::string result;
    result.reserve(num_chars);
    for (uint8_t i = 0; i < num_chars; i++) {
      uint32_t byte_val = extract_unsigned_bits(PROTOCOL_BYTE_SIZE);
      result.push_back(static_cast<char>(byte_val));
    }
    return result;
  }

  size_t bits_remaining() const {
    // runs with the whole assumption that you're only using data with this
    // class byte wise, such that total_bits % 8 == 0
    return (size_ - byte_index_) * PROTOCOL_BYTE_SIZE - bit_offset_;
  }

 private:
  const uint8_t *data_;  // Data to be parsed
  size_t size_;          // Total number of bytes in the data
  size_t byte_index_;    // Index of the current byte in data_
  uint8_t bit_offset_;   // Bit offset within the current byte
  ByteOrder endianness_;
};