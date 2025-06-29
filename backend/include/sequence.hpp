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

  void set_manual_control_mode(bool mode) { manual_control_solenoids_ = mode; }
  bool manual_control_mode() const { return manual_control_solenoids_; }

  long get_packet_count_av() const { return packet_count_av_; }
  long get_packet_count_gse() const { return packet_count_gse_; }

  void increment_packet_count_av() { packet_count_av_++; }
  void increment_packet_count_gse() { packet_count_gse_++; }

  bool start_sending_broadcast_flag() const {
    return start_sending_broadcast_flag_;
  }
  void set_start_sending_broadcast_flag(bool flag) {
    start_sending_broadcast_flag_ = flag;
  }

  bool have_received_broadcast_flag() const { return broadcast_flag_recieved_; }
  void set_broadcast_flag_recieved(bool flag) {
    broadcast_flag_recieved_ = flag;
  }

  bool get_camera_power() const { return camera_power_; }
  void set_camera_power(bool flag) { camera_power_ = flag; }

 private:
  SequenceLock gse_write_lock_{"GSE", "\033[38;5;10m"};
  SequenceLock av_write_lock_{"AV", "\033[38;5;205m"};
  static constexpr std::chrono::milliseconds TIMEOUT = SequenceLock::TIMEOUT;
  bool gse_only_mode_ = false;  // GSE only mode. This is an option from CLI
  bool manual_control_solenoids_ = false;  // Changes based on web data
  // Singleton assertion helper for constructor assertion
  bool singleton_created_ = false;
  long packet_count_av_ = 0;
  long packet_count_gse_ = 0;
  bool start_sending_broadcast_flag_ = false;
  bool broadcast_flag_recieved_ = false;
  bool camera_power_ = false;
};