#include "sequence_lock.hpp"

#include "subprocess_logging.hpp"

#ifdef DEBUG
#include <fstream>
#endif

// This file hosts locking mechanisms to orchestrate the packet sequence

/// @brief Thread save mutex lock with timeout features for sequence diagram
SequenceLock::SequenceLock(const std::string NAME, const std::string ANS_COLOR)
    : LOCK_NAME(NAME), ANS_COLOR(ANS_COLOR) {
  // Set last lock time as little as possible so timeout initially works
  // instantly
  last_lock_time_ = std::chrono::steady_clock::time_point::min();
}

void SequenceLock::lock() {
  mtx_.lock();
  is_locked_ = true;
  last_lock_time_ = std::chrono::steady_clock::now();
#ifdef DEBUG
  // Create a lock file for device emulator to use
  const std::string LOCK_PATH = "/tmp/gcs_await_" + LOCK_NAME + ".lock";
  std::ofstream lock_file(LOCK_PATH);
  if (lock_file.is_open()) {
    lock_file << "server_seqeunce_lock";
    lock_file.close();
  } else {
    slogger::error("Unable to create lock file: " + LOCK_PATH);
  }
#endif
}

void SequenceLock::unlock() {
  is_locked_ = false;
  mtx_.unlock();
}

/// @brief Check if timed out and return the final lock status
/// @return true if unlocked. False otherwise
bool SequenceLock::unlock_if_timed_out_() {
  // If lock is already open, just return true
  if (!is_locked_.load()) {
    return true;
  }
  // If lock is timed out for more than TIMEOUT ms, unlock it
  if (std::chrono::steady_clock::now() - getLastLockTime() > TIMEOUT) {
    unlock();
    slogger::warning("(NO SIGNAL: " + ANS_COLOR + "\033[1m" + LOCK_NAME +
                     "\033[0m" + slogger::WARNING_COLOUR + ") Timeout on " +
                     LOCK_NAME + " sequence lock");
    return true;
  } else {
    return false;
  }
}

std::chrono::steady_clock::time_point SequenceLock::getLastLockTime() const {
  return last_lock_time_;
}

/// @brief Applies timeout logic and returns lock status
/// @return
bool SequenceLock::is_locked() { return unlock_if_timed_out_(); }
