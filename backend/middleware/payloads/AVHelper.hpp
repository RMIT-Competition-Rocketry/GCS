#pragma once

#include "AVStateFlags.pb.h"
#include "FlightState.pb.h"
#include "subprocess_logging.hpp"

common::FlightState calc_flight_state(unsigned int val) {
  // Also I know this can be returned implicitly, but this is self documenting
  switch (val) {
    case 0b000:
      return common::FlightState::PRE_FLIGHT_NO_FLIGHT_READY;
    case 0b001:
      return common::FlightState::PRE_FLIGHT_FLIGHT_READY;
    case 0b010:
      return common::FlightState::LAUNCH;
    case 0b011:
      return common::FlightState::COAST;
    case 0b100:
      return common::FlightState::APOGEE;
    case 0b101:
      return common::FlightState::DECENT;
    case 0b110:
      return common::FlightState::LANDED;
    case 0b111:
      return common::FlightState::OH_NO;
    default:
      slogger::error("Unexpected flight state case bits in AV_TO_GCS_DATA_1");
      throw std::runtime_error("Unexpected flight state bits");
  }
}