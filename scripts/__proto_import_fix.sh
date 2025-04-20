#!/bin/bash

# --------------------------------------------
# Do not run unless you know what you're doing
# --------------------------------------------

GENERATED_DIR="./backend/proto/generated"

find "$GENERATED_DIR" -type f -name "*.py" -exec sed -i.bak \
    -e 's/import FlightState_pb2 as FlightState__pb2/import backend.proto.generated.FlightState_pb2 as FlightState__pb2/g' \
    -e 's/import AVStateFlags_pb2 as AVStateFlags__pb2/import backend.proto.generated.AVStateFlags_pb2 as AVStateFlags__pb2/g' \
    -e 's/import GSEStateFlags_pb2 as GSEStateFlags__pb2/import backend.proto.generated.GSEStateFlags_pb2 as GSEStateFlags__pb2/g' \
    -e 's/import GSEErrors_pb2 as GSEErrors__pb2/import backend.proto.generated.GSEErrors_pb2 as GSEErrors__pb2/g' \
    {} +

# Remove backup files created by sed
find "$GENERATED_DIR" -type f -name "*.bak" -delete