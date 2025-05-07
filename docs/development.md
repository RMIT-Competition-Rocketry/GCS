
# Development notes

See [usage](./usage.md)

### Debugging in dev mode

See launch options in `.vscode/` for pre-conifgured debug setups. Note that the cli option will start the ENTIRE system in dev mode and attach a python debugger to all procceses except the pendant emulator. Other launch options may require manual injection or manual monitoring depending on what the subsystem is. If you're starting the server by itself, you'll need to specify it's command arguments and read the ZeroMQ socket

## Semantic Versioning

For this project, changes made before our first release can all just be 0.x.x-dev. But after first release, which will the White Cliffs test, use this methodology below.

If you're still developing internally and the product is not considered to be in 'publicly usable' or 'finished' state, use:

- `MAJOR`: Major semver 
- `MINOR`: Minor semver. Consider internal breaking changes pre `1.x.x` to be on this level
- `PATCH`: Patch semver
- `PR_I`: Pre release identifier. This program is not designed to be used by anyone but our internal team. So semver suffixes like this can be restrained to: `dev` or nothing. Where `dev` is development and field testing focused, and final release with no suffix can be presentable packages for competition or when the repo is at a good state for a stable release of course.
- `PR_IV` Pre release identifier version. If multiple versions are being used for the same pre release. For example, this would increment between test flights when on field test if changes are made on the day or something.
- `METADATA`: Just a relevant optional note. Can be used to name tests

```txt
MAJOR.MINOR.PATCH-PR_I.PR_IV+METADATA
```

For example:

```txt
0.1.0-dev.1+whitecliffs
```

Would be the first release, as it's the first internal test. If the code changes in White Cliffs, you would go to `0.1.0-dev.2+whitecliffs` and then next field test in Serpentine would probably be `0.2.0-dev.1+serpentine`


## Writing a subprocess

Important requirements for each subproccess you spawn from the CLI:

- All python subprocess have to have unbuffered output to be logged correctly. 

Please use the `-u` flag to do this. Note that some print functions to STDOUT may not respect this flag like when using `pprint` for example. 

Also I've seen a python subprocces run with the `-u` flag and still run buffered. It required `sys.stdout.flush()`.

If you're using `subprocess_logging.py`, this is already handled for you.

- You must support signal handling at a minimum. Graceful shutdown prefferably

Graceful shutdown in python can be done by including this line in any of your python modules in your process

```python
import backend.includes_python.service_helper as service_helper
```

Then you can see when a signal has been requested to shutdown with

```python
service_helper.time_to_stop()
```

If that returns true, break out of loops and perform cleanup.

Example:

```python
import time
import backend.includes_python.service_helper as service_helper

while True:
    time.sleep(1) # Slow function
    if service_helper.time_to_stop():
        break
cleanup_code()
```


## Writing a Payload Reader

Payload readers are found in `backend/middleware/payloads/*.hpp` with the excpetion of the helper headers. 

They follow a typical template of:

```cpp
#pragma once
#include <bit>
#include <cstdint>
#include <iostream>

#include "AVHelper.hpp"
#include "AVStateFlags.pb.h"
#include "AV_TO_GCS_DATA_1.pb.h"
#include "ByteParser.hpp"
#include "FlightState.pb.h"
#include "ProtoHelper.hpp"

class AV_TO_GCS_DATA_1 {
 public:
  // Amount of bytes in this payload
  static constexpr ssize_t SIZE = 31;  // 32 including ID and TBC byte
  static constexpr const char *PACKET_NAME = "AV_TO_GCS_DATA_1";
  static constexpr int8_t ID = 0x03;  // 8 bits reserved in packet

  /// @brief See LoRa packet structure spreadsheet for more information.
  /// @param DATA
  AV_TO_GCS_DATA_1(const uint8_t *DATA) {
    ByteParser parser(DATA, SIZE);

    // DON'T EXTRACT BITS FOR ID!!!!
    // ID is handled seperatly in main loop for packet type identification
    accel_low_x_ = calc_low_accel_xy_(parser.extract_signed_bits(16));
  }

  // Getters for the private members
  float accel_low_x() const { return accel_low_x_; }

  // Protobuf serialization
  payload::AV_TO_GCS_DATA_1 toProtobuf(const float timestamp_s, const long counter_av, const long counter_gcs) const {
    payload::AV_TO_GCS_DATA_1 proto_data;

    // Use the macro for simple fields with same name
    SET_PROTO_FIELD(proto_data, accel_low_x);

    return proto_data;
  }

 private:
  static float calc_low_accel_xy_(int16_t val) { return val / 2048.0f; }
  float accel_low_x_;
};
```

## Ports and Sockets

For debug, so far we've only opened temporary `/tmp/gcs_rocket_pub.sock` and `/tmp/gcs_rocket_sub.sock` sockets. They should be formalised with the config.ini file at some point perhaps? or maybe just best to document it here and hard code it into the file. 

- Frontend API websocket: `ws://localhost:1887`
- Frontend HTTP server: `http://localhost:8008` (in config.ini)

## Device emulation / packet mocking

TODO ^

---

[Home](../README.md)
