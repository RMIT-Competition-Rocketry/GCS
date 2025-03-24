#pragma once
#include <bit>
#include <cstdint>
#include <iostream>

#include "ByteParser.hpp"
#include "GSE_TO_GCS_DATA_2.pb.h"

#define SET_PROTO_FIELD(proto, field) proto.set_##field(field())

class GSE_TO_GCS_DATA_2 {
 public:
  // Amount of bytes in this payload
  static constexpr ssize_t SIZE = 31;  // 32 including ID and TBC byte
  static constexpr const char *PACKET_NAME = "GSE_TO_GCS_DATA_2";
  static constexpr int8_t ID = 0x07;  // 8 bits reserved in packet

  /// @brief See LoRa packet structure spreadsheet for more information.
  /// @param DATA
  GSE_TO_GCS_DATA_2(const uint8_t *DATA) {
    ByteParser parser(DATA, SIZE);

    // DON'T EXTRACT BITS FOR ID!!!!
    // ID is handled seperatly in main loop for packet type identification

    manual_purge_activated_ =
        static_cast<bool>(parser.extract_unsigned_bits(1));
    o2_fill_activated_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    selector_switch_neutral_position_ =
        static_cast<bool>(parser.extract_unsigned_bits(1));
    n20_fill_activated_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    ignition_fired_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    ignition_selected_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    gas_fill_selected_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    system_activated_ = static_cast<bool>(parser.extract_unsigned_bits(1));

    internal_temp_ = std::bit_cast<float>(parser.extract_unsigned_bits(32));
    wind_speed_ = std::bit_cast<float>(parser.extract_unsigned_bits(32));
    gas_bottle_weight_1_ =
        static_cast<unsigned int>(parser.extract_unsigned_bits(16));
    gas_bottle_weight_2_ =
        static_cast<unsigned int>(parser.extract_unsigned_bits(16));
    analog_voltage_input_1_ =
        std::bit_cast<float>(parser.extract_unsigned_bits(32));
    analog_voltage_input_2_ =
        std::bit_cast<float>(parser.extract_unsigned_bits(32));
    additional_current_input_1_ =
        std::bit_cast<float>(parser.extract_unsigned_bits(32));
    additional_current_input_2_ =
        std::bit_cast<float>(parser.extract_unsigned_bits(32));

    // Note 10
    ignition_error_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    relay_3_error_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    relay_2_error_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    relay_1_error_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    thermocouple_4_error_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    thermocouple_3_error_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    thermocouple_2_error_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    thermocouple_1_error_ = static_cast<bool>(parser.extract_unsigned_bits(1));

    // Note 11
    load_cell_4_error_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    load_cell_3_error_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    load_cell_2_error_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    load_cell_1_error_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    transducer_4_error_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    transducer_3_error_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    transducer_2_error_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    transducer_1_error_ = static_cast<bool>(parser.extract_unsigned_bits(1));
  }

  // Getters for the private members
  constexpr unsigned int id_val() const { return ID; }
  bool manual_purge_activated() const { return manual_purge_activated_; }
  bool o2_fill_activated() const { return o2_fill_activated_; }
  bool selector_switch_neutral_position() const {
    return selector_switch_neutral_position_;
  }
  bool n20_fill_activated() const { return n20_fill_activated_; }
  bool ignition_fired() const { return ignition_fired_; }
  bool ignition_selected() const { return ignition_selected_; }
  bool gas_fill_selected() const { return gas_fill_selected_; }
  bool system_activated() const { return system_activated_; }

  // Protobuf serialization

  payload::GSE_TO_GCS_DATA_2 toProtobuf() const {
    payload::GSE_TO_GCS_DATA_2 proto_data;

    // Use the macro for simple fields with same name
    SET_PROTO_FIELD(proto_data, manual_purge_activated);
    SET_PROTO_FIELD(proto_data, o2_fill_activated);
    SET_PROTO_FIELD(proto_data, selector_switch_neutral_position);
    SET_PROTO_FIELD(proto_data, n20_fill_activated);
    SET_PROTO_FIELD(proto_data, ignition_fired);
    SET_PROTO_FIELD(proto_data, ignition_selected);
    SET_PROTO_FIELD(proto_data, gas_fill_selected);
    SET_PROTO_FIELD(proto_data, system_activated);

    return proto_data;
  }

 private:
  // Static conversion functions here too
  bool manual_purge_activated_;
  bool o2_fill_activated_;
  bool selector_switch_neutral_position_;
  bool n20_fill_activated_;
  bool ignition_fired_;
  bool ignition_selected_;
  bool gas_fill_selected_;
  bool system_activated_;

  float internal_temp_;
  float wind_speed_;
  int gas_bottle_weight_1_;
  int gas_bottle_weight_2_;
  float analog_voltage_input_1_;
  float analog_voltage_input_2_;
  float additional_current_input_1_;
  float additional_current_input_2_;

  // Note 10
  bool ignition_error_;
  bool relay_3_error_;
  bool relay_2_error_;
  bool relay_1_error_;
  bool thermocouple_4_error_;
  bool thermocouple_3_error_;
  bool thermocouple_2_error_;
  bool thermocouple_1_error_;

  // Note 11
  bool load_cell_4_error_;
  bool load_cell_3_error_;
  bool load_cell_2_error_;
  bool load_cell_1_error_;
  bool transducer_4_error_;
  bool transducer_3_error_;
  bool transducer_2_error_;
  bool transducer_1_error_;
};