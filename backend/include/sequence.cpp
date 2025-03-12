#include "sequence.hpp"
#include <cassert>

// Sequence constrcutor.
// This object should be treated like a singleton,
// but passed by refference across threads instead of calling the constructor
// on each new instance
Sequence::Sequence()
{
    assert(singleton_created_ == false);
    current_state_ = LOOP_PRE_LAUNCH;
    singleton_created_ = true;
}

// Are we waiting for a response from the GSE?
bool Sequence::waiting_for_gse() { return !gse_write_lock_.is_locked(); }
void Sequence::await_gse() { gse_write_lock_.lock(); }
void Sequence::recieved_gse() { gse_write_lock_.unlock(); }