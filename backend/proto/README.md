# Proto Files

Please note that the indented structure of the protobuf serialisation is to send a `packet_id` object, then load the next object from the buffer by using the `id` to determine the correct object in `payloads/`. This is the trade off from using a self describing schema in something like JSON when using protobuf which has no self description. 

Each proto definition should be the higher level representation of the data object, and not the lower level unmanipulated bytes. The byte manipulation will be done by the C++ middleware.

## Generating files

Please refference the [official proto docs](https://protobuf.dev/getting-started/cpptutorial/#compiling-protocol-buffers) which outline a generation command such as 

```terminal
protoc -I=$SRC_DIR --cpp_out=$DST_DIR $SRC_DIR/addressbook.proto
```

which roughly translates to 

```terminal
protoc -I "$PWD"/backend/proto/payloads --cpp_out="$PWD"/backend/proto/generated "$PWD"/backend/proto/payloads/AV_TO_GCS_DATA_1.proto
```

For a single file