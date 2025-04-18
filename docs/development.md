
# Development notes

## Running in dev mode

To start in dev mode, please use:

```terminal
$ rocket dev
```

In comparison to release mode (`run`), dev will additionally:
- Lower log level to `DEBUG`
- Start the pendant emulator (if you're still implimenting this)
- Start the device emulator (fake serial input)
- Turn off logging
- Compile with the DEBUG macro defined

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

- All python subprocess have to have unbuffered output to be logged correctly. Please use the `-u` flag to do this. Note that some print functions to STDOUT may not respect this flag like when using `pprint` for example. 
    - Also I've seen a python subprocces run with the `-u` flag and still run buffered. It required `sys.stdout.flush()`. In the future (https://github.com/RMIT-Competition-Rocketry/GCS/issues/5) the process printer should flush automatically

## Writing a Payload Reader

Payload readers are found in `backend/middleware/payloads/*.hpp` with the excpetion of the `ByteParser.hpp` helper

They follow a typical template of:

```cpp
#pragma once
#include "ByteParser.hpp"
#include <cstdint>
#include <iostream>
#include <bit>
#include <cstdint>
#include "AV_TO_GCS_DATA_1.pb.h" //

#define SET_PROTO_FIELD(proto, field) proto.set_##field(field())

class PacketName
{
public:
    // Amount of bytes in this payload
    static constexpr ssize_t SIZE = 31;      // 32 including ID and TBC byte
    static constexpr const char* PACKET_NAME = "PacketName";
    static constexpr int8_t  ID = 0x03; // 8 bits reserved in packet

    /// @brief See LoRa packet structure spreadsheet for more information.
    /// @param DATA
    PacketName(const uint8_t *DATA)
    {
        ByteParser parser(DATA, SIZE);

        // DON'T EXTRACT BITS FOR ID!!!!
        // ID is handled seperatly in main loop for packet type identification

        bool_field_ = static_cast<bool>(parser.extract_bits(1));
        float_field_ = std::bit_cast<float>(parser.extract_signed_bits(32));
    }

    // Getters for the private members
    constexpr unsigned int id_val() const { return ID; }
    bool bool_field() const { return bool_field_; }
    float float_field() const { return float_field_; }


    // Protobuf serialization

    payload::PacketName toProtobuf() const
    {
        payload::PacketName proto_data;

        // Use the macro for simple fields with same name
        SET_PROTO_FIELD(proto_data, bool_field);
        SET_PROTO_FIELD(proto_data, float_field);

        return proto_data;
    }

private:
    
    // Static conversion functions here too
    bool bool_field_;
    float float_field_;
};
```

## Ports and Sockets

For debug, so far we've only opened temporary `/tmp/gcs_rocket_pub.sock` and `/tmp/gcs_rocket_sub.sock` sockets. They should be formalised with the config.ini file at some point perhaps? or maybe just best to document it here and hard code it into the file. 

- Frontend API  websocket: `ws://localhost:1887`

### Device Emulation 

Example output from `socat` at startup. This shows what the device names are

```terminal
2025/02/06 20:53:44 socat[56067] N PTY is /dev/ttys012
2025/02/06 20:53:44 socat[56067] N PTY is /dev/ttys01
```

And when you write to them

```terminal
$ echo "Hello Serial" > /dev/ttys012
$ echo "Hello Serial" > /dev/ttys01
```
```terminal
2025/02/06 21:08:47 socat[56254] N write(7, 0x126814000, 13) completed
2025/02/06 21:08:53 socat[56254] N write(7, 0x126814000, 13) complete
```

Please note that both fake serial devices are linked, but when you read from one the buffer is cleared. That means that you use one as the 'fake device' and the other can just be for montitoring because nothing will steal the bytes going to it from the other linked device. 

> [!WARNING]
> **However**, at the time of writing I am using both for testing the ZeroMQ server. So you can't attach to either of them. You're better off getting the PUB-SUB sockets working and making something to SUB from that. A debug script?
>
> Anyway, feel free to see the *Reading Bytes* section

### Reading Bytes

> [!WARNING]
> This method is **deprecated**. Now, please use `backend/tools/zeromq_debug...` scripts to check on IPC data. 
> This should only be used for extreme low level debugging and is likely only applicable for ZeroMQ IPC work. You would have to modify socat to make a third paired pseudo terminal as well because the other 2 are in use.

As we're not within the ascii table range, but within the entire range of bytes (0-255) we can't use screen or any ascii rendering method. You need to view the data in hex or binary.

Get the device port as the **second** listed device in the debug logs:

![socat device parsing output](./assets/socatDeviceParse.png)

Then use `xxd` on unix systems (This may need to be installed). Use the `-b` flag for binary instead of hex if needed. The `-c 1` argument will do one byte per line. 

![xxdOutput1](./assets/xxdOutput1.png)
![xxdOutput1binary](./assets/xxdOutput1binary.png)

---

[Home](../README.md)
