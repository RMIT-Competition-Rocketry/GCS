#pragma once
#include "ByteParser.hpp"
#include <cstdint>
#include <iostream>
#include <bit>
#include <cstdint>
#include "../../proto/generated/payloads/GCS_TO_GSE_STATE_CMD.pb.h"

#define SET_PROTO_FIELD(proto, field) proto.set_##field(field())

class GCS_TO_GSE_STATE_CMD
{
public:
    // Amount of bytes in this payload
    static constexpr ssize_t SIZE = 3; // 4 including ID and TBC byte
    static constexpr const char *PACKET_NAME = "GCS_TO_GSE_STATE_CMD";
    static constexpr int8_t ID = 0x02; // 8 bits reserved in packet

    /// @brief See LoRa packet structure spreadsheet for more information.
    /// @param DATA
    GCS_TO_GSE_STATE_CMD(const uint8_t *DATA)
    {
        ByteParser parser(DATA, SIZE);

        // DON'T EXTRACT BITS FOR ID!!!!
        // ID is handled seperatly in main loop for packet type identification

        manual_purge_activate_ = static_cast<bool>(parser.extract_bits(1));
        o2_fill_activate_ = static_cast<bool>(parser.extract_bits(1));
        selector_switch_neutral_position_ = static_cast<bool>(parser.extract_bits(1));
        n20_fill_activate_ = static_cast<bool>(parser.extract_bits(1));
        ignition_fire_ = static_cast<bool>(parser.extract_bits(1));
        ignition_selected_ = static_cast<bool>(parser.extract_bits(1));
        gas_fill_selected_ = static_cast<bool>(parser.extract_bits(1));
        system_activate_ = static_cast<bool>(parser.extract_bits(1));

        manual_purge_activate_inverted_ = static_cast<bool>(parser.extract_bits(1));
        o2_fill_activate_inverted_ = static_cast<bool>(parser.extract_bits(1));
        selector_switch_neutral_position_inverted_ = static_cast<bool>(parser.extract_bits(1));
        n20_fill_activate_inverted_ = static_cast<bool>(parser.extract_bits(1));
        ignition_fire_inverted_ = static_cast<bool>(parser.extract_bits(1));
        ignition_selected_inverted_ = static_cast<bool>(parser.extract_bits(1));
        gas_fill_selected_inverted_ = static_cast<bool>(parser.extract_bits(1));
        system_activate_inverted_ = static_cast<bool>(parser.extract_bits(1));

        parser.extract_bits(8); // Skip the TBC byte
    }

    // Getters for the private members
    constexpr unsigned int id_val() const { return ID; }
    bool manual_purge_activate() const { return manual_purge_activate_; }
    bool o2_fill_activate() const { return o2_fill_activate_; }
    bool selector_switch_neutral_position() const { return selector_switch_neutral_position_; }
    bool n20_fill_activate() const { return n20_fill_activate_; }
    bool ignition_fire() const { return ignition_fire_; }
    bool ignition_selected() const { return ignition_selected_; }
    bool gas_fill_selected() const { return gas_fill_selected_; }
    bool system_activate() const { return system_activate_; }

    bool manual_purge_activate_inverted() const { return manual_purge_activate_inverted_; }
    bool o2_fill_activate_inverted() const { return o2_fill_activate_inverted_; }
    bool selector_switch_neutral_position_inverted() const { return selector_switch_neutral_position_inverted_; }
    bool n20_fill_activate_inverted() const { return n20_fill_activate_inverted_; }
    bool ignition_fire_inverted() const { return ignition_fire_inverted_; }
    bool ignition_selected_inverted() const { return ignition_selected_inverted_; }
    bool gas_fill_selected_inverted() const { return gas_fill_selected_inverted_; }
    bool system_activate_inverted() const { return system_activate_inverted_; }

    // Protobuf serialization

    payload::GCS_TO_GSE_STATE_CMD toProtobuf() const
    {
        payload::GCS_TO_GSE_STATE_CMD proto_data;

        // Use the macro for simple fields with same name
        SET_PROTO_FIELD(proto_data, manual_purge_activate);
        SET_PROTO_FIELD(proto_data, o2_fill_activate);
        SET_PROTO_FIELD(proto_data, selector_switch_neutral_position);
        SET_PROTO_FIELD(proto_data, n20_fill_activate);
        SET_PROTO_FIELD(proto_data, ignition_fire);
        SET_PROTO_FIELD(proto_data, ignition_selected);
        SET_PROTO_FIELD(proto_data, gas_fill_selected);
        SET_PROTO_FIELD(proto_data, system_activate);

        SET_PROTO_FIELD(proto_data, manual_purge_activate_inverted);
        SET_PROTO_FIELD(proto_data, o2_fill_activate_inverted);
        SET_PROTO_FIELD(proto_data, selector_switch_neutral_position_inverted);
        SET_PROTO_FIELD(proto_data, n20_fill_activate_inverted);
        SET_PROTO_FIELD(proto_data, ignition_fire_inverted);
        SET_PROTO_FIELD(proto_data, ignition_selected_inverted);
        SET_PROTO_FIELD(proto_data, gas_fill_selected_inverted);
        SET_PROTO_FIELD(proto_data, system_activate_inverted);

        return proto_data;
    }

private:
    // Static conversion functions here too
    bool manual_purge_activate_;
    bool o2_fill_activate_;
    bool selector_switch_neutral_position_;
    bool n20_fill_activate_;
    bool ignition_fire_;
    bool ignition_selected_;
    bool gas_fill_selected_;
    bool system_activate_;

    bool manual_purge_activate_inverted_;
    bool o2_fill_activate_inverted_;
    bool selector_switch_neutral_position_inverted_;
    bool n20_fill_activate_inverted_;
    bool ignition_fire_inverted_;
    bool ignition_selected_inverted_;
    bool gas_fill_selected_inverted_;
    bool system_activate_inverted_;
};