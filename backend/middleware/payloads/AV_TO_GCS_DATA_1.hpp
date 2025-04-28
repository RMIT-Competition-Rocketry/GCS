#pragma once
#include <bit>
#include <cstdint>
#include <iostream>

#include "AVHelper.hpp"
#include "AVStateFlags.pb.h"
#include "AV_TO_GCS_DATA_1.pb.h"
#include "ByteParser.hpp"
#include "FlightState.pb.h"
#include "PacketMeta.pb.h"
#include "ProtoHelper.hpp"

class AV_TO_GCS_DATA_1 {
 public:
  // Amount of bytes in this payload
  static constexpr ssize_t SIZE = 31;  // 32 including ID and TBC byte
  // Size + Internal additions of RSSI/SNR
  static constexpr ssize_t INTERNAL_SIZE = SIZE + 8;
  static constexpr const char *PACKET_NAME = "AV_TO_GCS_DATA_1";
  static constexpr int8_t ID = 0x03;  // 8 bits reserved in packet

  /// @brief See LoRa packet structure spreadsheet for more information.
  /// @param DATA
  AV_TO_GCS_DATA_1(const uint8_t *DATA) {
    ByteParser parser(DATA, INTERNAL_SIZE);

    // DON'T EXTRACT BITS FOR ID!!!!
    // ID is handled seperatly in main loop for packet type identification

    rssi_ = std::bit_cast<float>(parser.extract_signed_bits(32));
    snr_ = std::bit_cast<float>(parser.extract_signed_bits(32));
    flight_state_ = calc_flight_state(parser.extract_unsigned_bits(3));

    dual_board_connectivity_state_flag_ =
        static_cast<bool>(parser.extract_unsigned_bits(1));
    recovery_checks_complete_and_flight_ready_ =
        static_cast<bool>(parser.extract_unsigned_bits(1));
    gps_fix_flag_ = static_cast<bool>(parser.extract_unsigned_bits(1));
    payload_connection_flag_ =
        static_cast<bool>(parser.extract_unsigned_bits(1));
    camera_controller_connection_flag_ =
        static_cast<bool>(parser.extract_unsigned_bits(1));

    accel_low_x_ = calc_low_accel_xy_(parser.extract_signed_bits(16));
    accel_low_y_ = calc_low_accel_xy_(parser.extract_signed_bits(16));
    accel_low_z_ = calc_low_accel_z_(parser.extract_signed_bits(16));

    accel_high_x_ = calc_high_accel_xy_(parser.extract_signed_bits(16));
    accel_high_y_ = calc_high_accel_xy_(parser.extract_signed_bits(16));
    accel_high_z_ = calc_high_accel_z_(parser.extract_signed_bits(16));

    gyro_x_ = calc_gyro_(parser.extract_signed_bits(16));
    gyro_y_ = calc_gyro_(parser.extract_signed_bits(16));
    gyro_z_ = calc_gyro_(parser.extract_signed_bits(16));

    altitude_ = std::bit_cast<float>(parser.extract_signed_bits(32));
    velocity_ = std::bit_cast<float>(parser.extract_signed_bits(32));

    apogee_primary_test_compete_ =
        static_cast<bool>(parser.extract_unsigned_bits(1));
    apogee_secondary_test_compete_ =
        static_cast<bool>(parser.extract_unsigned_bits(1));
    // Skip 4 fixed bits.
    // Come back to this in future if you are working on #16
    parser.extract_unsigned_bits(4);
    apogee_primary_test_results_ =
        static_cast<bool>(parser.extract_unsigned_bits(1));
    apogee_secondary_test_results_ =
        static_cast<bool>(parser.extract_unsigned_bits(1));

    main_primary_test_compete_ =
        static_cast<bool>(parser.extract_unsigned_bits(1));
    main_secondary_test_compete_ =
        static_cast<bool>(parser.extract_unsigned_bits(1));
    // Skip 4 fixed bits.
    // Come back to this in future if you are working on #16
    parser.extract_unsigned_bits(4);
    main_primary_test_results_ =
        static_cast<bool>(parser.extract_unsigned_bits(1));
    main_secondary_test_results_ =
        static_cast<bool>(parser.extract_unsigned_bits(1));

    uint8_t broadcast_byte = parser.extract_unsigned_bits(8);
    if (broadcast_byte == 0b10101010) {
      broadcast_flag_ = true;
    } else if (broadcast_byte == 0b00000000) {
      broadcast_flag_ = false;
    } else {
      // Future error validation for #16
      slogger::error(
          "Unexpected parsed value for broadcast_flag_ in AV_TO_GCS_DATA_1:");
      slogger::error("broadcast_byte");
    }

    parser.extract_unsigned_bits(8);  // Discard last byte for now
  }

  // Getters for the private members
  constexpr int8_t id_val() const { return ID; }
  float rssi() const { return rssi_; }
  float snr() const { return snr_; }
  common::FlightState flight_state() const { return flight_state_; }
  bool dual_board_connectivity_state_flag() const {
    return dual_board_connectivity_state_flag_;
  }
  bool recovery_checks_complete_and_flight_ready() const {
    return recovery_checks_complete_and_flight_ready_;
  }
  bool gps_fix_flag() const { return gps_fix_flag_; }
  bool payload_connection_flag() const { return payload_connection_flag_; }
  bool camera_controller_connection_flag() const {
    return camera_controller_connection_flag_;
  }

  float accel_low_x() const { return accel_low_x_; }
  float accel_low_y() const { return accel_low_y_; }
  float accel_low_z() const { return accel_low_z_; }

  float accel_high_x() const { return accel_high_x_; }
  float accel_high_y() const { return accel_high_y_; }
  float accel_high_z() const { return accel_high_z_; }

  float gyro_x() const { return gyro_x_; }
  float gyro_y() const { return gyro_y_; }
  float gyro_z() const { return gyro_z_; }

  float altitude() const { return altitude_; }
  float velocity() const { return velocity_; }

  bool apogee_primary_test_complete() const {
    return apogee_primary_test_compete_;
  }
  bool apogee_secondary_test_complete() const {
    return apogee_secondary_test_compete_;
  }
  bool apogee_primary_test_results() const {
    return apogee_primary_test_results_;
  }
  bool apogee_secondary_test_results() const {
    return apogee_secondary_test_results_;
  }

  bool main_primary_test_complete() const { return main_primary_test_compete_; }
  bool main_secondary_test_complete() const {
    return main_secondary_test_compete_;
  }
  bool main_primary_test_results() const { return main_primary_test_results_; }
  bool main_secondary_test_results() const {
    return main_secondary_test_results_;
  }

  bool broadcast_flag() const { return broadcast_flag_; }

  // Protobuf serialization

  payload::AV_TO_GCS_DATA_1 toProtobuf() const {
    payload::AV_TO_GCS_DATA_1 proto_data;

    common::PacketMeta *packet_meta = new common::PacketMeta();
    SET_SUB_PROTO_FIELD(packet_meta, rssi);
    SET_SUB_PROTO_FIELD(packet_meta, snr);
    proto_data.set_allocated_meta(packet_meta);

    proto_data.set_flightstate(flight_state_);

    common::AVStateFlags *state_flags = new common::AVStateFlags();
    SET_SUB_PROTO_FIELD(state_flags, dual_board_connectivity_state_flag);
    SET_SUB_PROTO_FIELD(state_flags, recovery_checks_complete_and_flight_ready);
    SET_SUB_PROTO_FIELD(state_flags, gps_fix_flag);
    SET_SUB_PROTO_FIELD(state_flags, payload_connection_flag);
    SET_SUB_PROTO_FIELD(state_flags, camera_controller_connection_flag);
    SET_SUB_PROTO_FIELD(state_flags, dual_board_connectivity_state_flag);
    proto_data.set_allocated_state_flags(state_flags);

    // Use the macro for simple fields with same name
    SET_PROTO_FIELD(proto_data, accel_low_x);
    SET_PROTO_FIELD(proto_data, accel_low_y);
    SET_PROTO_FIELD(proto_data, accel_low_z);

    SET_PROTO_FIELD(proto_data, accel_high_x);
    SET_PROTO_FIELD(proto_data, accel_high_y);
    SET_PROTO_FIELD(proto_data, accel_high_z);

    SET_PROTO_FIELD(proto_data, gyro_x);
    SET_PROTO_FIELD(proto_data, gyro_y);
    SET_PROTO_FIELD(proto_data, gyro_z);

    SET_PROTO_FIELD(proto_data, altitude);
    SET_PROTO_FIELD(proto_data, velocity);

    SET_PROTO_FIELD(proto_data, apogee_primary_test_complete);
    SET_PROTO_FIELD(proto_data, apogee_secondary_test_complete);
    SET_PROTO_FIELD(proto_data, apogee_primary_test_results);
    SET_PROTO_FIELD(proto_data, apogee_secondary_test_results);

    SET_PROTO_FIELD(proto_data, main_primary_test_complete);
    SET_PROTO_FIELD(proto_data, main_secondary_test_complete);
    SET_PROTO_FIELD(proto_data, main_primary_test_results);
    SET_PROTO_FIELD(proto_data, main_secondary_test_results);

    SET_PROTO_FIELD(proto_data, broadcast_flag);

    return proto_data;
  }

 private:
  static float calc_low_accel_xy_(int16_t val) { return val / 2048.0f; }
  static float calc_low_accel_z_(int16_t val) { return val / -2048.0f; }
  static float calc_high_accel_xy_(int16_t val) { return val / -1024.0f; }
  static float calc_high_accel_z_(int16_t val) { return val / 1024.0f; }
  static float calc_gyro_(int16_t val) { return val * 0.00875f; }

  float rssi_;
  float snr_;
  common::FlightState flight_state_;  // 3 bits all used
  bool dual_board_connectivity_state_flag_;
  bool recovery_checks_complete_and_flight_ready_;
  bool gps_fix_flag_;
  bool payload_connection_flag_;
  bool camera_controller_connection_flag_;

  float accel_low_x_;
  float accel_low_y_;
  float accel_low_z_;
  float accel_high_x_;
  float accel_high_y_;
  float accel_high_z_;

  float gyro_x_;
  float gyro_y_;
  float gyro_z_;

  float altitude_;
  float velocity_;

  bool apogee_primary_test_compete_;
  bool apogee_secondary_test_compete_;
  bool apogee_primary_test_results_;
  bool apogee_secondary_test_results_;

  bool main_primary_test_compete_;
  bool main_secondary_test_compete_;
  bool main_primary_test_results_;
  bool main_secondary_test_results_;

  bool broadcast_flag_;
};