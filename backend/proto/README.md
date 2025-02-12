# Proto Files

Please note that the indented structure of the protobuf serialisation is to send a `packet_id` object, then load the next object from the buffer by using the `id` to determine the correct object in `payloads/`. This is the trade off from using a self describing schema in something like JSON when using protobuf which has no self description. 

Each proto definition should be the higher level representation of the data object, and not the lower level unmanipulated bytes. The byte manipulation will be done by the C++ middleware.