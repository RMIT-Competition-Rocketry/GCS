#pragma once
#include <atomic>
#include <chrono>
#include <mutex>

// This file hosts locking mechanisms to orchestrate the packet sequence

class SequenceLock {
 public:
  SequenceLock(const std::string NAME, const std::string ANS_COLOR);
  ~SequenceLock() = default;
  void lock();
  void unlock();
  bool is_locked();

  static constexpr std::chrono::milliseconds TIMEOUT{1000};

 private:
  std::chrono::steady_clock::time_point getLastLockTime() const;
  bool unlock_if_timed_out_();
  std::mutex mtx_;
  const std::string LOCK_NAME;  // Appears in timeout message
  const std::string ANS_COLOR;  // Colors the timeout message
  std::chrono::steady_clock::time_point last_lock_time_;
  // Time that you wait for a response from other device
  std::atomic<bool> is_locked_{false};
};