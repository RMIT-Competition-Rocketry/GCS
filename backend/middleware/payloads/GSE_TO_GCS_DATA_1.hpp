#pragma once
#include "ByteParser.hpp"
#include <cstdint>
#include <iostream>
#include <bit>
#include <cstdint>
#include "GSE_TO_GCS_DATA_1.pb.h"

#define SET_PROTO_FIELD(proto, field) proto.set_##field(field())

class GSE_TO_GCS_DATA_1
{
public:
    // Amount of bytes in this payload
    static constexpr ssize_t SIZE = 31; // 32 including ID and TBC byte
    static constexpr const char *PACKET_NAME = "GSE_TO_GCS_DATA_1";
    static constexpr int8_t ID = 0x06; // 8 bits reserved in packet

    /// @brief See LoRa packet structure spreadsheet for more information.
    /// @param DATA
    GSE_TO_GCS_DATA_1(const uint8_t *DATA)
    {
        ByteParser parser(DATA, SIZE);

        // DON'T EXTRACT BITS FOR ID!!!!
        // ID is handled seperatly in main loop for packet type identification

        manual_purge_activated_ = static_cast<bool>(parser.extract_bits(1));
        o2_fill_activated_ = static_cast<bool>(parser.extract_bits(1));
        selector_switch_neutral_position_ = static_cast<bool>(parser.extract_bits(1));
        n20_fill_activated_ = static_cast<bool>(parser.extract_bits(1));
        ignition_fired_ = static_cast<bool>(parser.extract_bits(1));
        ignition_selected_ = static_cast<bool>(parser.extract_bits(1));
        gas_fill_selected_ = static_cast<bool>(parser.extract_bits(1));
        system_activated_ = static_cast<bool>(parser.extract_bits(1));

        transducer_1_ = std::bit_cast<float>(parser.extract_bits(32));
        transducer_2_ = std::bit_cast<float>(parser.extract_bits(32));
        transducer_3_ = std::bit_cast<float>(parser.extract_bits(32));

        thermocouple_1_ = std::bit_cast<float>(parser.extract_bits(32));
        thermocouple_2_ = std::bit_cast<float>(parser.extract_bits(32));
        thermocouple_3_ = std::bit_cast<float>(parser.extract_bits(32));
        thermocouple_4_ = std::bit_cast<float>(parser.extract_bits(32));

        // Note 10
        ignition_error_ = static_cast<bool>(parser.extract_bits(1));
        relay_3_error_ = static_cast<bool>(parser.extract_bits(1));
        relay_2_error_ = static_cast<bool>(parser.extract_bits(1));
        relay_1_error_ = static_cast<bool>(parser.extract_bits(1));
        thermocouple_4_error_ = static_cast<bool>(parser.extract_bits(1));
        thermocouple_3_error_ = static_cast<bool>(parser.extract_bits(1));
        thermocouple_2_error_ = static_cast<bool>(parser.extract_bits(1));
        thermocouple_1_error_ = static_cast<bool>(parser.extract_bits(1));

        // Note 11
        load_cell_4_error_ = static_cast<bool>(parser.extract_bits(1));
        load_cell_3_error_ = static_cast<bool>(parser.extract_bits(1));
        load_cell_2_error_ = static_cast<bool>(parser.extract_bits(1));
        load_cell_1_error_ = static_cast<bool>(parser.extract_bits(1));
        transducer_4_error_ = static_cast<bool>(parser.extract_bits(1));
        transducer_3_error_ = static_cast<bool>(parser.extract_bits(1));
        transducer_2_error_ = static_cast<bool>(parser.extract_bits(1));
        transducer_1_error_ = static_cast<bool>(parser.extract_bits(1));
    }

    // Getters for the private members
    constexpr unsigned int id_val() const { return ID; }
    bool manual_purge_activated() const { return manual_purge_activated_; }
    bool o2_fill_activated() const { return o2_fill_activated_; }
    bool selector_switch_neutral_position() const { return selector_switch_neutral_position_; }
    bool n20_fill_activated() const { return n20_fill_activated_; }
    bool ignition_fired() const { return ignition_fired_; }
    bool ignition_selected() const { return ignition_selected_; }
    bool gas_fill_selected() const { return gas_fill_selected_; }
    bool system_activated() const { return system_activated_; }

    float transducer_1() const { return transducer_1_; }
    float transducer_2() const { return transducer_2_; }
    float transducer_3() const { return transducer_3_; }

    float thermocouple_1() const { return thermocouple_1_; }
    float thermocouple_2() const { return thermocouple_2_; }
    float thermocouple_3() const { return thermocouple_3_; }
    float thermocouple_4() const { return thermocouple_4_; }

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
    bool load_cell_3_error() const { return load_cell_2_error_; }
    bool load_cell_2_error() const { return load_cell_3_error_; }
    bool load_cell_1_error() const { return load_cell_1_error_; }
    bool transducer_4_error() const { return transducer_4_error_; }
    bool transducer_3_error() const { return transducer_3_error_; }
    bool transducer_2_error() const { return transducer_2_error_; }
    bool transducer_1_error() const { return transducer_1_error_; }

    // Protobuf serialization

    payload::GSE_TO_GCS_DATA_1 toProtobuf() const
    {
        payload::GSE_TO_GCS_DATA_1 proto_data;

        // Use the macro for simple fields with same name
        SET_PROTO_FIELD(proto_data, manual_purge_activated);
        SET_PROTO_FIELD(proto_data, o2_fill_activated);
        SET_PROTO_FIELD(proto_data, selector_switch_neutral_position);
        SET_PROTO_FIELD(proto_data, n20_fill_activated);
        SET_PROTO_FIELD(proto_data, ignition_fired);
        SET_PROTO_FIELD(proto_data, ignition_selected);
        SET_PROTO_FIELD(proto_data, gas_fill_selected);
        SET_PROTO_FIELD(proto_data, system_activated);

        SET_PROTO_FIELD(proto_data, transducer_1);
        SET_PROTO_FIELD(proto_data, transducer_2);
        SET_PROTO_FIELD(proto_data, transducer_3);

        SET_PROTO_FIELD(proto_data, thermocouple_1);
        SET_PROTO_FIELD(proto_data, thermocouple_2);
        SET_PROTO_FIELD(proto_data, thermocouple_3);
        SET_PROTO_FIELD(proto_data, thermocouple_4);

        // Note 10
        SET_PROTO_FIELD(proto_data, ignition_error);
        SET_PROTO_FIELD(proto_data, relay_3_error);
        SET_PROTO_FIELD(proto_data, relay_2_error);
        SET_PROTO_FIELD(proto_data, relay_1_error);
        SET_PROTO_FIELD(proto_data, thermocouple_4_error);
        SET_PROTO_FIELD(proto_data, thermocouple_3_error);
        SET_PROTO_FIELD(proto_data, thermocouple_2_error);
        SET_PROTO_FIELD(proto_data, thermocouple_1_error);

        // Note 11
        SET_PROTO_FIELD(proto_data, load_cell_4_error);
        SET_PROTO_FIELD(proto_data, load_cell_3_error);
        SET_PROTO_FIELD(proto_data, load_cell_2_error);
        SET_PROTO_FIELD(proto_data, load_cell_1_error);
        SET_PROTO_FIELD(proto_data, transducer_4_error);
        SET_PROTO_FIELD(proto_data, transducer_3_error);
        SET_PROTO_FIELD(proto_data, transducer_2_error);
        SET_PROTO_FIELD(proto_data, transducer_1_error);

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

    float transducer_1_;
    float transducer_2_;
    float transducer_3_;

    float thermocouple_1_;
    float thermocouple_2_;
    float thermocouple_3_;
    float thermocouple_4_;

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