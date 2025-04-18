#pragma once
#include "sequence_lock.hpp"

// Used for handling position in the sequence diagram.
// This should be treated as a singleton, passed by `std::ref` through threads
class Sequence {
 public:
  Sequence();
  ~Sequence() = default;

  // Current state in the sequence diagram
  enum State {
    LOOP_PRE_LAUNCH,
    LOOP_IGNITION,
    ONCE_AV_DETERMINING_LAUNCH,
    LOOP_AV_DATA_TRANSMISSION_BURN,    // For motor burn and coasting
    LOOP_AV_DATA_TRANSMISSION_APOGEE,  // During and post apogee
    LOOP_AV_DATA_TRANSMISSION_LANDED   // Landed / recovery
  };

  void set_state(State state) { current_state = state; }
  State get_state() const { return current_state; }

  bool waiting_for_gse();
  bool sit_and_wait_for_gse();
  void start_await_gse();
  void received_gse();

  bool waiting_for_av();
  bool sit_and_wait_for_av();
  void start_await_av();
  void received_av();

  State current_state;

  void set_gse_only_mode(bool mode) { gse_only_mode_ = mode; }
  bool gse_only_mode() const { return gse_only_mode_; }

 private:
  SequenceLock gse_write_lock_{"GSE"};
  SequenceLock av_write_lock_{"AV"};
  static constexpr std::chrono::milliseconds TIMEOUT = SequenceLock::TIMEOUT;
  bool gse_only_mode_ = false;  // GSE only mode. This is an option from CLI
  // Singleton assertion helper for constructor assertion
  bool singleton_created_ = false;
};