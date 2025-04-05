#pragma once
#include <atomic>
#include <chrono>
#include <mutex>

// This file hosts locking mechanisms to orchestrate the packet sequence

class SequenceLock {
 public:
  SequenceLock(const std::string NAME);  // Constructor requires a name
  ~SequenceLock() = default;
  void lock();
  void unlock();
  bool is_locked();

  static constexpr std::chrono::milliseconds TIMEOUT{400};

 private:
  std::chrono::steady_clock::time_point getLastLockTime() const;
  bool unlock_if_timed_out_();
  std::mutex mtx_;
  const std::string LOCK_NAME;  // Used for debug only
  std::chrono::steady_clock::time_point last_lock_time_;
  // Time that you wait for a response from other device
  std::atomic<bool> is_locked_{false};
};