#pragma once
#include "ByteParser.hpp"
#include <cstdint>
#include <iostream>
#include <bit>
#include <cstdint>
#include "../../proto/generated/payloads/GCS_TO_AV_STATE_CMD.pb.h"

#define SET_PROTO_FIELD(proto, field) proto.set_##field(field())

class GCS_TO_AV_STATE_CMD
{
public:
    // Amount of bytes in this payload
    static constexpr ssize_t SIZE = 3; // 32 including ID and TBC byte
    static constexpr const char *PACKET_NAME = "GCS_TO_AV_STATE_CMD";
    static constexpr int8_t ID = 0x01; // 8 bits reserved in packet

    /// @brief See LoRa packet structure spreadsheet for more information.
    /// @param DATA
    GCS_TO_AV_STATE_CMD(const uint8_t *DATA)
    {
        ByteParser parser(DATA, SIZE);

        // DON'T EXTRACT BITS FOR ID!!!!
        // ID is handled seperatly in main loop for packet type identification

        // 0b1010
        parser.extract_bits(4); // Skip continuity check fixed bytes
        main_secondary_test_ = static_cast<bool>(parser.extract_bits(1));
        main_primary_test_ = static_cast<bool>(parser.extract_bits(1));
        apogee_secondary_test_ = static_cast<bool>(parser.extract_bits(1));
        apogee_primary_test_ = static_cast<bool>(parser.extract_bits(1));

        // 0b0101
        parser.extract_bits(4); // Skip continuity check fixed bytes
        main_secondary_test_inverted_ = static_cast<bool>(parser.extract_bits(1));
        main_primary_test_inverted_ = static_cast<bool>(parser.extract_bits(1));
        apogee_secondary_test_inverted_ = static_cast<bool>(parser.extract_bits(1));
        apogee_primary_test_inverted_ = static_cast<bool>(parser.extract_bits(1));

        // TODO add bit validation here with 3 cases.0xFF, 0x00, else
        broadcast_begin_ = parser.extract_bits(8) == 0xFF;
    }

    // Getters for the private members
    constexpr unsigned int id_val() const { return ID; }

    // Protobuf serialization

    payload::GCS_TO_AV_STATE_CMD toProtobuf() const
    {
        payload::GCS_TO_AV_STATE_CMD proto_data;

        // Use the macro for simple fields with same name

        return proto_data;
    }

private:
    // Static conversion functions here too
    bool main_secondary_test_;
    bool main_primary_test_;
    bool apogee_secondary_test_;
    bool apogee_primary_test_;

    bool main_secondary_test_inverted_;
    bool main_primary_test_inverted_;
    bool apogee_secondary_test_inverted_;
    bool apogee_primary_test_inverted_;

    bool broadcast_begin_;
};