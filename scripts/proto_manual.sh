#!/bin/bash

# protoc --proto_path "${PWD}/backend/proto" --cpp_out="${PWD}/backend/proto/generated/payloads" "${PWD}/backend/proto/payloads/AV_TO_GCS_DATA_1.proto"
set -e

echo "Generating Python and C++ files from proto files in ./backend/proto/payloads/"
mkdir -p ./backend/proto/generated/
for proto in ./backend/proto/payloads/*.proto; do
    echo "Processing $proto"
    # Generate Python files
    protoc --proto_path=./backend/proto/ --python_out=./backend/proto/generated/ "$proto"
    # Generate C++ files
    protoc --proto_path=./backend/proto --cpp_out=./backend/proto/generated/ "$proto"
done

echo "Done."