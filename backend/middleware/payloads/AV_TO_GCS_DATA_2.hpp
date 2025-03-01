#pragma once
#include "ByteParser.hpp"
#include <cstdint>
#include <iostream>
#include <bit>
#include <cstdint>
#include "../../proto/generated/payloads/AV_TO_GCS_DATA_2.pb.h"

#define SET_PROTO_FIELD(proto, field) proto.set_##field(field())

class AV_TO_GCS_DATA_2
{
public:
    // Amount of bytes in this payload
    static constexpr ssize_t SIZE = 31; // 32 including ID and TBC byte
    static constexpr const char *PACKET_NAME = "AV_TO_GCS_DATA_2";
    static constexpr int8_t ID = 0x04; // 8 bits reserved in packet

    /// @brief See LoRa packet structure spreadsheet for more information.
    /// @param DATA
    AV_TO_GCS_DATA_2(const uint8_t *DATA)
    {
        ByteParser parser(DATA, SIZE);

        // DON'T EXTRACT BITS FOR ID!!!!
        // ID is handled seperatly in main loop for packet type identification

        flight_state_ = calc_flight_state(parser.extract_bits(3));

        dual_board_connectivity_state_flag_ = static_cast<bool>(parser.extract_bits(1));
        recovery_checks_complete_and_flight_ready_ = static_cast<bool>(parser.extract_bits(1));
        gps_fix_flag_ = static_cast<bool>(parser.extract_bits(1));
        payload_connection_flag_ = static_cast<bool>(parser.extract_bits(1));
        camera_controller_connection_flag_ = static_cast<bool>(parser.extract_bits(1));

        GPS_latitude_ = parser.extract_string(15);
        GPS_longitude_ = parser.extract_string(15);
    }

    // Getters for the private members
    constexpr unsigned int id_val() const { return ID; }
    payload::AV_TO_GCS_DATA_2_FlightState flight_state() const { return flight_state_; }
    bool dual_board_connectivity_state_flag() const { return dual_board_connectivity_state_flag_; }
    bool recovery_checks_complete_and_flight_ready() const { return recovery_checks_complete_and_flight_ready_; }
    bool gps_fix_flag() const { return gps_fix_flag_; }
    bool payload_connection_flag() const { return payload_connection_flag_; }
    bool camera_controller_connection_flag() const { return camera_controller_connection_flag_; }

    std::string gps_latitude() const { return GPS_latitude_; }
    std::string gps_longitude() const { return GPS_longitude_; }

    // Protobuf serialization

    payload::AV_TO_GCS_DATA_2 toProtobuf() const
    {
        payload::AV_TO_GCS_DATA_2 proto_data;

        // Use the macro for simple fields with same name
        proto_data.set_flightstate(flight_state_);
        SET_PROTO_FIELD(proto_data, dual_board_connectivity_state_flag);
        SET_PROTO_FIELD(proto_data, recovery_checks_complete_and_flight_ready);
        SET_PROTO_FIELD(proto_data, gps_fix_flag);
        SET_PROTO_FIELD(proto_data, payload_connection_flag);
        SET_PROTO_FIELD(proto_data, camera_controller_connection_flag);

        SET_PROTO_FIELD(proto_data, gps_latitude);
        SET_PROTO_FIELD(proto_data, gps_longitude);

        return proto_data;
    }

private:
    // Static conversion functions here too
    static payload::AV_TO_GCS_DATA_2_FlightState calc_flight_state(unsigned int val)
    {
        // Also I know this can be returned implicitly, but this is self documenting
        switch (val)
        {
        case 0b000:
            return payload::AV_TO_GCS_DATA_2_FlightState::AV_TO_GCS_DATA_2_FlightState_PRE_FLIGHT_NO_FLIGHT_READY;
        case 0b001:
            return payload::AV_TO_GCS_DATA_2_FlightState::AV_TO_GCS_DATA_2_FlightState_PRE_FLIGHT_FLIGHT_READY;
        case 0b010:
            return payload::AV_TO_GCS_DATA_2_FlightState::AV_TO_GCS_DATA_2_FlightState_LAUNCH;
        case 0b011:
            return payload::AV_TO_GCS_DATA_2_FlightState::AV_TO_GCS_DATA_2_FlightState_COAST;
        case 0b100:
            return payload::AV_TO_GCS_DATA_2_FlightState::AV_TO_GCS_DATA_2_FlightState_APOGEE;
        case 0b101:
            return payload::AV_TO_GCS_DATA_2_FlightState::AV_TO_GCS_DATA_2_FlightState_DECENT;
        case 0b110:
            return payload::AV_TO_GCS_DATA_2_FlightState::AV_TO_GCS_DATA_2_FlightState_LANDED;
        case 0b111:
            return payload::AV_TO_GCS_DATA_2_FlightState::AV_TO_GCS_DATA_2_FlightState_OH_NO;
        default:
            process_logging::error("Unexpected flight state case bits in AV_TO_GCS_DATA_2");
            throw std::runtime_error("Unexpected flight state bits");
        }
    }

    payload::AV_TO_GCS_DATA_2_FlightState flight_state_; // 3 bits all used
    bool dual_board_connectivity_state_flag_;
    bool recovery_checks_complete_and_flight_ready_;
    bool gps_fix_flag_;
    bool payload_connection_flag_;
    bool camera_controller_connection_flag_;

    std::string GPS_latitude_;
    std::string GPS_longitude_;
};