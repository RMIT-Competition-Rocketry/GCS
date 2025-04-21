#!/bin/bash

# -----------------------------------------
# This is redundant if building with CMake. 
# -----------------------------------------

# protoc --proto_path "${PWD}/backend/proto" --cpp_out="${PWD}/backend/proto/generated/payloads" "${PWD}/backend/proto/payloads/AV_TO_GCS_DATA_1.proto"
set -e

echo "Generating Python and C++ files from proto files in ./backend/proto/payloads/"
mkdir -p ./backend/proto/generated/
PROTO_ROOT=./backend/proto
find "$PROTO_ROOT" -name "*.proto" | while read -r proto; do
    echo "Processing $proto"
    protoc \
        -I"$PROTO_ROOT" \
        -I"$PROTO_ROOT/common" \
        --python_out="$PROTO_ROOT/generated/" \
        --cpp_out="$PROTO_ROOT/generated/" \
        "$proto"
done

echo "Editing generated files to fix import paths"
chmod +x ./scripts/__proto_import_fix.sh
./scripts/__proto_import_fix.sh

echo "Done."