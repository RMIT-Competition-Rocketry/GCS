#pragma once
#include <bit>
#include <cstdint>
#include <iostream>

#include "ByteParser.hpp"
#include "GSE_TO_GCS_DATA_2.pb.h"
#include "PacketMeta.pb.h"
#include "ProtoHelper.hpp"

class GSE_TO_GCS_DATA_2 {
 public:
  // Amount of bytes in this payload
  static constexpr ssize_t SIZE = 31;  // 32 including ID and TBC byte
  static constexpr ssize_t INTERNAL_SIZE = SIZE + 8;
  static constexpr const char *PACKET_NAME = "GSE_TO_GCS_DATA_2";
  static constexpr int8_t ID = 0x07;  // 8 bits reserved in packet

  /// @brief See LoRa packet structure spreadsheet for more information.
  /// @param DATA
  GSE_TO_GCS_DATA_2(const uint8_t *DATA) {
    ByteParser parser(DATA, INTERNAL_SIZE);

    // DON'T EXTRACT BITS FOR ID!!!!
    // ID is handled seperatly in main loop for packet type identification
    rssi_ = std::bit_cast<float>(parser.extract_signed_bits(32));
    snr_ = std::bit_cast<float>(parser.extract_signed_bits(32));
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
  float rssi() const { return rssi_; }
  float snr() const { return snr_; }
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

  float internal_temp() const { return internal_temp_; }
  float wind_speed() const { return wind_speed_; }
  int gas_bottle_weight_1() const { return gas_bottle_weight_1_; }
  int gas_bottle_weight_2() const { return gas_bottle_weight_2_; }
  float analog_voltage_input_1() const { return analog_voltage_input_1_; }
  float analog_voltage_input_2() const { return analog_voltage_input_2_; }
  float additional_current_input_1() const {
    return additional_current_input_1_;
  }
  float additional_current_input_2() const {
    return additional_current_input_2_;
  }

  // Note 10
  bool ignition_error() const { return ignition_error_; }
  bool relay_3_error() const { return relay_3_error_; }
  bool relay_2_error() const { return relay_2_error_; }
  bool relay_1_error() const { return relay_1_error_; }
  bool thermocouple_4_error() const { return thermocouple_4_error_; }
  bool thermocouple_3_error() const { return thermocouple_3_error_; }
  bool thermocouple_2_error() const { return thermocouple_2_error_; }
  bool thermocouple_1_error() const { return thermocouple_1_error_; }

  // Note 11
  bool load_cell_4_error() const { return load_cell_4_error_; }
  bool load_cell_3_error() const { return load_cell_3_error_; }
  bool load_cell_2_error() const { return load_cell_2_error_; }
  bool load_cell_1_error() const { return load_cell_1_error_; }
  bool transducer_4_error() const { return transducer_4_error_; }
  bool transducer_3_error() const { return transducer_3_error_; }
  bool transducer_2_error() const { return transducer_2_error_; }
  bool transducer_1_error() const { return transducer_1_error_; }

  // Protobuf serialization

  payload::GSE_TO_GCS_DATA_2 toProtobuf() const {
    payload::GSE_TO_GCS_DATA_2 proto_data;

    common::PacketMeta *packet_meta = new common::PacketMeta();
    SET_SUB_PROTO_FIELD(packet_meta, rssi);
    SET_SUB_PROTO_FIELD(packet_meta, snr);
    proto_data.set_allocated_meta(packet_meta);

    // Use the macro for simple fields with same name
    common::GSEStateFlags *gse_state_flags = new common::GSEStateFlags();
    SET_SUB_PROTO_FIELD(gse_state_flags, manual_purge_activated);
    SET_SUB_PROTO_FIELD(gse_state_flags, o2_fill_activated);
    SET_SUB_PROTO_FIELD(gse_state_flags, selector_switch_neutral_position);
    SET_SUB_PROTO_FIELD(gse_state_flags, n20_fill_activated);
    SET_SUB_PROTO_FIELD(gse_state_flags, ignition_fired);
    SET_SUB_PROTO_FIELD(gse_state_flags, ignition_selected);
    SET_SUB_PROTO_FIELD(gse_state_flags, gas_fill_selected);
    SET_SUB_PROTO_FIELD(gse_state_flags, system_activated);
    proto_data.set_allocated_state_flags(gse_state_flags);

    SET_PROTO_FIELD(proto_data, internal_temp);
    SET_PROTO_FIELD(proto_data, wind_speed);
    SET_PROTO_FIELD(proto_data, gas_bottle_weight_1);
    SET_PROTO_FIELD(proto_data, gas_bottle_weight_2);
    SET_PROTO_FIELD(proto_data, analog_voltage_input_1);
    SET_PROTO_FIELD(proto_data, analog_voltage_input_2);
    SET_PROTO_FIELD(proto_data, additional_current_input_1);
    SET_PROTO_FIELD(proto_data, additional_current_input_2);

    common::GSEErrors *gse_errors = new common::GSEErrors();
    SET_SUB_PROTO_FIELD(gse_errors, ignition_error);
    SET_SUB_PROTO_FIELD(gse_errors, relay_3_error);
    SET_SUB_PROTO_FIELD(gse_errors, relay_2_error);
    SET_SUB_PROTO_FIELD(gse_errors, relay_1_error);
    SET_SUB_PROTO_FIELD(gse_errors, thermocouple_4_error);
    SET_SUB_PROTO_FIELD(gse_errors, thermocouple_3_error);
    SET_SUB_PROTO_FIELD(gse_errors, thermocouple_2_error);
    SET_SUB_PROTO_FIELD(gse_errors, thermocouple_1_error);
    SET_SUB_PROTO_FIELD(gse_errors, load_cell_4_error);
    SET_SUB_PROTO_FIELD(gse_errors, load_cell_3_error);
    SET_SUB_PROTO_FIELD(gse_errors, load_cell_2_error);
    SET_SUB_PROTO_FIELD(gse_errors, load_cell_1_error);
    SET_SUB_PROTO_FIELD(gse_errors, transducer_4_error);
    SET_SUB_PROTO_FIELD(gse_errors, transducer_3_error);
    SET_SUB_PROTO_FIELD(gse_errors, transducer_2_error);
    SET_SUB_PROTO_FIELD(gse_errors, transducer_1_error);
    proto_data.set_allocated_error_flags(gse_errors);

    return proto_data;
  }

 private:
  // Static conversion functions here too
  float rssi_;
  float snr_;
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