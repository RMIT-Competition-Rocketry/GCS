#pragma once
#include <mutex>
#include <chrono>
#include <atomic>

// This file hosts locking mechanisms to orchestrate the packet sequence

class SequenceLock
{
public:
    SequenceLock();
    ~SequenceLock() = default;
    void lock();
    void unlock();
    bool is_locked();

private:
    std::chrono::steady_clock::time_point getLastLockTime() const;
    bool unlock_if_timed_out_();
    std::mutex mtx_;
    std::chrono::steady_clock::time_point last_lock_time_;
    std::chrono::milliseconds TIMEOUT_{400}; // Time that you wait for a response from other device
    std::atomic<bool> is_locked_{false};
};