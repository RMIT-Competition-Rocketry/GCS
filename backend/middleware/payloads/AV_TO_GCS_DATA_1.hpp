#pragma once
#include "ByteParser.hpp"
#include <cstdint>
#include <iostream>
#include <bit>
#include <cstdint>
// TODO add this to import path and make linter happy
#include "../../proto/generated/payloads/AV_TO_GCS_DATA_1.pb.h"

#define SET_PROTO_FIELD(proto, field) proto.set_##field(field())

class AV_TO_GCS_DATA_1
{
public:
    // Amount of bytes in this payload
    static constexpr ssize_t SIZE = 31;      // 32 including ID and TBC byte
    static constexpr unsigned int ID = 0x03; // 8 bits reserved in packet

    /// @brief See LoRa packet structure spreadsheet for more information.
    /// @param DATA
    AV_TO_GCS_DATA_1(const uint8_t *DATA)
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

        apogee_primary_test_compete_ = static_cast<bool>(parser.extract_bits(1));
        apogee_secondary_test_compete_ = static_cast<bool>(parser.extract_bits(1));
        // Skip 4 fixed bits.
        // Come back to this in future if you are working on #16
        parser.extract_bits(4);
        apogee_primary_test_results_ = static_cast<bool>(parser.extract_bits(1));
        apogee_secondary_test_results_ = static_cast<bool>(parser.extract_bits(1));

        main_primary_test_compete_ = static_cast<bool>(parser.extract_bits(1));
        main_secondary_test_compete_ = static_cast<bool>(parser.extract_bits(1));
        // Skip 4 fixed bits.
        // Come back to this in future if you are working on #16
        parser.extract_bits(4);
        main_primary_test_results_ = static_cast<bool>(parser.extract_bits(1));
        main_secondary_test_results_ = static_cast<bool>(parser.extract_bits(1));

        uint8_t broadcast_byte = parser.extract_bits(8);
        if (broadcast_byte == 0b10101010)
        {
            broadcast_flag_ = true;
        }
        else if (broadcast_byte == 0b00000000)
        {
            broadcast_flag_ = false;
        }
        else
        {
            // Future error validation for #16
            std::cerr << "Error: Unexpected parsed value for broadcast_flag_ in AV_TO_GCS_DATA_1: ";
            std::cerr << broadcast_byte << std::endl;
        }

        parser.extract_bits(8); // Discard last byte for now
    }

    // Getters for the private members
    constexpr unsigned int id_val() const { return ID; }
    payload::AV_TO_GCS_DATA_1_FlightState flight_state() const { return flight_state_; }
    bool dual_board_connectivity_state_flag() const { return dual_board_connectivity_state_flag_; }
    bool recovery_checks_complete_and_flight_ready() const { return recovery_checks_complete_and_flight_ready_; }
    bool gps_fix_flag() const { return gps_fix_flag_; }
    bool payload_connection_flag() const { return payload_connection_flag_; }
    bool camera_controller_connection_flag() const { return camera_controller_connection_flag_; }

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

    bool apogee_primary_test_complete() const { return apogee_primary_test_compete_; }
    bool apogee_secondary_test_complete() const { return apogee_secondary_test_compete_; }
    bool apogee_primary_test_results() const { return apogee_primary_test_results_; }
    bool apogee_secondary_test_results() const { return apogee_secondary_test_results_; }

    bool main_primary_test_complete() const { return main_primary_test_compete_; }
    bool main_secondary_test_complete() const { return main_secondary_test_compete_; }
    bool main_primary_test_results() const { return main_primary_test_results_; }
    bool main_secondary_test_results() const { return main_secondary_test_results_; }

    bool broadcast_flag() const { return broadcast_flag_; }

    // Protobuf serialization

    payload::AV_TO_GCS_DATA_1 toProtobuf() const
    {
        payload::AV_TO_GCS_DATA_1 proto_data;

        // Use the macro for simple fields with same name
        proto_data.set_flightstate(flight_state_);
        SET_PROTO_FIELD(proto_data, dual_board_connectivity_state_flag);
        SET_PROTO_FIELD(proto_data, recovery_checks_complete_and_flight_ready);
        SET_PROTO_FIELD(proto_data, gps_fix_flag);
        SET_PROTO_FIELD(proto_data, payload_connection_flag);
        SET_PROTO_FIELD(proto_data, camera_controller_connection_flag);

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
    static payload::AV_TO_GCS_DATA_1_FlightState calc_flight_state(unsigned int val)
    {
        // Also I know this can be returned implicitly, but this is self documenting
        switch (val)
        {
        case 0b000:
            return payload::AV_TO_GCS_DATA_1_FlightState::AV_TO_GCS_DATA_1_FlightState_PRE_FLIGHT_NO_FLIGHT_READY;
        case 0b001:
            return payload::AV_TO_GCS_DATA_1_FlightState::AV_TO_GCS_DATA_1_FlightState_PRE_FLIGHT_FLIGHT_READY;
        case 0b010:
            return payload::AV_TO_GCS_DATA_1_FlightState::AV_TO_GCS_DATA_1_FlightState_LAUNCH;
        case 0b011:
            return payload::AV_TO_GCS_DATA_1_FlightState::AV_TO_GCS_DATA_1_FlightState_COAST;
        case 0b100:
            return payload::AV_TO_GCS_DATA_1_FlightState::AV_TO_GCS_DATA_1_FlightState_APOGEE;
        case 0b101:
            return payload::AV_TO_GCS_DATA_1_FlightState::AV_TO_GCS_DATA_1_FlightState_DECENT;
        case 0b110:
            return payload::AV_TO_GCS_DATA_1_FlightState::AV_TO_GCS_DATA_1_FlightState_LANDED;
        case 0b111:
            return payload::AV_TO_GCS_DATA_1_FlightState::AV_TO_GCS_DATA_1_FlightState_OH_NO;
        default:
            std::cerr << "Error: Unexpected flight state case bits in AV_TO_GCS_DATA_1\n";
            throw std::runtime_error("Unexpected flight state bits");
        }
    }

    static float calc_low_accel_xy_(int16_t val) { return val / 2048.0f; }
    static float calc_low_accel_z_(int16_t val) { return val / -2048.0f; }
    static float calc_high_accel_xy_(int16_t val) { return val / -1024.0f; }
    static float calc_high_accel_z_(int16_t val) { return val / 1024.0f; }
    static float calc_gyro_(int16_t val) { return val * 0.00875f; }

    payload::AV_TO_GCS_DATA_1_FlightState flight_state_; // 3 bits all used
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