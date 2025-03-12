#pragma once
#include "sequence_lock.hpp"

// Used for handling position in the sequence diagram.
// This should be treated as a singleton, passed by `std::ref` through threads
class Sequence
{
public:
    Sequence();
    ~Sequence() = default;
    bool waiting_for_gse();
    void await_gse();
    void recieved_gse();

private:
    // Current state in the sequence diagram
    enum State_
    {
        LOOP_PRE_LAUNCH,
        LOOP_IGNITION,
        ONCE_AV_DETERMINING_LAUNCH,
        LOOP_AV_DATA_TRANSMISSION_BURN,   // For motor burn and coasting
        LOOP_AV_DATA_TRANSMISSION_APOGEE, // During and post apogee
        LOOP_AV_DATA_TRANSMISSION_LANDED  // Landed / recovery
    };
    State_ current_state_;
    SequenceLock gse_write_lock_;
    // SequenceLock wait_for_av_;
    // ...

    // Singleton assertion helper for constructor assertion
    bool singleton_created_ = false;
};