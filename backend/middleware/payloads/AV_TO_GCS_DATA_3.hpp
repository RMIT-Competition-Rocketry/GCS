#pragma once
#include <bit>
#include <cstdint>
#include <iostream>

#include "AVStateFlags.pb.h"
#include "AV_TO_GCS_DATA_3.pb.h"
#include "ByteParser.hpp"
#include "PacketMeta.pb.h"
#include "ProtoHelper.hpp"

class AV_TO_GCS_DATA_3 {
 public:
  // Amount of bytes in this payload
  static constexpr ssize_t SIZE = 31;  // 32 including ID and TBC byte
  static constexpr ssize_t INTERNAL_SIZE = SIZE + 8;
  static constexpr const char *PACKET_NAME = "AV_TO_GCS_DATA_3";
  static constexpr int8_t ID = 0x05;  // 8 bits reserved in packet

  /// @brief See LoRa packet structure spreadsheet for more information.
  /// @param DATA
  AV_TO_GCS_DATA_3(const uint8_t *DATA) {
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

    // For TBC bytes if this packet is even seen
    constexpr int BYTES_TO_SKIP = 30;
    for (int i = 0; i < BYTES_TO_SKIP; ++i) {
      parser.extract_unsigned_bits(PROTOCOL_BYTE_SIZE);
    }
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

  // Protobuf serialization

  payload::AV_TO_GCS_DATA_3 toProtobuf(const float TIMESTAMP_S,
                                       const int64_t COUNTER_AV,
                                       const int64_t COUNTER_GCS) const {
    payload::AV_TO_GCS_DATA_3 proto_data;

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
};