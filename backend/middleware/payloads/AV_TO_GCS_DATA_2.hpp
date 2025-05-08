#pragma once
#include <bit>
#include <cstdint>
#include <iostream>

#include "AVHelper.hpp"
#include "AVStateFlags.pb.h"
#include "AV_TO_GCS_DATA_2.pb.h"
#include "ByteParser.hpp"
#include "FlightState.pb.h"
#include "PacketMeta.pb.h"
#include "ProtoHelper.hpp"

class AV_TO_GCS_DATA_2 {
 public:
  // Amount of bytes in this payload
  static constexpr ssize_t SIZE = 27;  // 32 including ID and TBC byte
  static constexpr ssize_t INTERNAL_SIZE = SIZE + 8;
  static constexpr const char *PACKET_NAME = "AV_TO_GCS_DATA_2";
  static constexpr int8_t ID = 0x04;  // 8 bits reserved in packet

  /// @brief See LoRa packet structure spreadsheet for more information.
  /// @param DATA
  AV_TO_GCS_DATA_2(const uint8_t *DATA) {
    ByteParser meta_parser(DATA, 8);

    // DON'T EXTRACT BITS FOR ID!!!!
    // ID is handled seperatly in main loop for packet type identification

    rssi_ = std::bit_cast<float>(meta_parser.extract_unsigned_bits(32));
    snr_ = std::bit_cast<float>(meta_parser.extract_unsigned_bits(32));

    ByteParser parser(DATA + 8, SIZE, LITTLE_ENDIAN_ORDER);
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

    GPS_latitude_ = std::bit_cast<float>(parser.extract_unsigned_bits(32));
    GPS_longitude_ = std::bit_cast<float>(parser.extract_unsigned_bits(32));

    try {
      // Skip 2 bytes for nav
      parser.extract_unsigned_bits(16);
      navigation_status_ = "NA";
      // navigation_status_ = parser.extract_string(2);
    } catch (const std::exception &e) {
      slogger::error(e.what());
    }

    qw_ = std::bit_cast<float>(parser.extract_unsigned_bits(32));
    qx_ = std::bit_cast<float>(parser.extract_unsigned_bits(32));
    qy_ = std::bit_cast<float>(parser.extract_unsigned_bits(32));
    qz_ = std::bit_cast<float>(parser.extract_unsigned_bits(32));
  }

  // Getters for the private members
  constexpr unsigned int id_val() const { return ID; }
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

  float gps_latitude() const { return GPS_latitude_; }
  float gps_longitude() const { return GPS_longitude_; }

  std::string navigation_status() const { return navigation_status_; }

  float qw() const { return qw_; }
  float qx() const { return qx_; }
  float qy() const { return qy_; }
  float qz() const { return qz_; }

  // Protobuf serialization

  payload::AV_TO_GCS_DATA_2 toProtobuf(const float TIMESTAMP_S,
                                       const int64_t COUNTER_AV,
                                       const int64_t COUNTER_GCS) const {
    payload::AV_TO_GCS_DATA_2 proto_data;
    common::PacketMeta *packet_meta = new common::PacketMeta();
    SET_SUB_PROTO_FIELD(packet_meta, rssi);
    SET_SUB_PROTO_FIELD(packet_meta, snr);
    packet_meta->set_timestamp_s(TIMESTAMP_S);
    packet_meta->set_total_packet_count_av(COUNTER_AV);
    packet_meta->set_total_packet_count_gse(COUNTER_GCS);
    proto_data.set_allocated_meta(packet_meta);

    // Use the macro for simple fields with same name
    proto_data.set_flightstate(flight_state_);

    common::AVStateFlags *state_flags = new common::AVStateFlags();
    SET_SUB_PROTO_FIELD(state_flags, dual_board_connectivity_state_flag);
    SET_SUB_PROTO_FIELD(state_flags, recovery_checks_complete_and_flight_ready);
    SET_SUB_PROTO_FIELD(state_flags, gps_fix_flag);
    SET_SUB_PROTO_FIELD(state_flags, payload_connection_flag);
    SET_SUB_PROTO_FIELD(state_flags, camera_controller_connection_flag);
    SET_SUB_PROTO_FIELD(state_flags, dual_board_connectivity_state_flag);
    proto_data.set_allocated_state_flags(state_flags);

    SET_PROTO_FIELD(proto_data, gps_latitude);
    SET_PROTO_FIELD(proto_data, gps_longitude);

    try {
      SET_PROTO_FIELD(proto_data, navigation_status);
    } catch (const std::exception &e) {
      slogger::error(e.what());
    }

    SET_PROTO_FIELD(proto_data, qw);
    SET_PROTO_FIELD(proto_data, qx);
    SET_PROTO_FIELD(proto_data, qy);
    SET_PROTO_FIELD(proto_data, qz);

    return proto_data;
  }

 private:
  // Static conversion functions here too
  float rssi_;
  float snr_;
  common::FlightState flight_state_;  // 3 bits all used
  bool dual_board_connectivity_state_flag_;
  bool recovery_checks_complete_and_flight_ready_;
  bool gps_fix_flag_;
  bool payload_connection_flag_;
  bool camera_controller_connection_flag_;

  float GPS_latitude_;
  float GPS_longitude_;

  std::string navigation_status_;

  float qw_;  // Quaternion
  float qx_;  // Quaternion
  float qy_;  // Quaternion
  float qz_;  // Quaternion
};