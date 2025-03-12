#include "sequence_lock.hpp"
#ifdef DEBUG
#include <fstream>
#include "process_logging.hpp"
#endif

// This file hosts locking mechanisms to orchestrate the packet sequence

/// @brief Thread save mutex lock with timeout features for sequence diagram
SequenceLock::SequenceLock()
{
    // Set last lock time as little as possible so timeout initially works instantly
    last_lock_time_ = std::chrono::steady_clock::time_point::min();
}

void SequenceLock::lock()
{
    mtx_.lock();
    is_locked_ = true;
    last_lock_time_ = std::chrono::steady_clock::now();
#ifdef DEBUG
    // Create a lock file for device emulator to use
    std::ofstream lock_file("/tmp/gcs_await_gse.lock");
    if (lock_file.is_open())
    {
        lock_file << "server_lock";
        lock_file.close();
    }
    else
    {
        process_logging::error("Unable to create lock file /tmp/gcs_await_gse.lock");
    }
#endif
}

void SequenceLock::unlock()
{
    is_locked_ = false;
    mtx_.unlock();
}

/// @brief Unlocks and returns true if the lock is timed out
/// @return true if unlocked. False otherwise
bool SequenceLock::unlock_if_timed_out_()
{
    // If lock is already open, just return true
    if (!is_locked_.load())
    {
        return true;
    }
    // If lock is timed out for more than TIMEOUT_ ms, unlock it
    if (std::chrono::steady_clock::now() - getLastLockTime() > TIMEOUT_)
    {
        unlock();
        return true;
    }
    else
    {
        return false;
    }
}

std::chrono::steady_clock::time_point SequenceLock::getLastLockTime() const
{
    return last_lock_time_;
}

/// @brief Applies timeout logic and returns lock status
/// @return
bool SequenceLock::is_locked()
{
    return unlock_if_timed_out_();
}
