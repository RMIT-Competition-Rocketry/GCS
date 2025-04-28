#!/bin/bash

# -----------------------------------------
# This is redundant if building with CMake. 
# -----------------------------------------

set -e

echo "Generating Python and C++ files from proto files"

mkdir -p ./backend/proto/generated/
PROTO_ROOT=./backend/proto

# Step 1: Process common proto files first
echo "Processing common proto files first"
find "$PROTO_ROOT/common" -name "*.proto" | while read -r proto; do
    echo "Processing $proto"
    protoc \
        -I"$PROTO_ROOT/common" \
        -I"$PROTO_ROOT" \
        --python_out="$PROTO_ROOT/generated/" \
        --cpp_out="$PROTO_ROOT/generated/" \
        "$proto"
done

# Step 2: Then process the rest (excluding common to avoid double processing)
echo "Processing other proto files"
find "$PROTO_ROOT" -path "$PROTO_ROOT/common" -prune -o -name "*.proto" -print | while read -r proto; do
    echo "Processing $proto"
    protoc \
        -I"$PROTO_ROOT/common" \
        -I"$PROTO_ROOT" \
        --python_out="$PROTO_ROOT/generated/" \
        --cpp_out="$PROTO_ROOT/generated/" \
        "$proto"
done

echo "Editing generated files to fix import paths"
chmod +x ./scripts/__proto_import_fix.sh
./scripts/__proto_import_fix.sh

echo "Done."
