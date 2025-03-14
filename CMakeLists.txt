cmake_minimum_required(VERSION 3.12)
project(middleware_server LANGUAGES CXX)

option(BUILD_TESTS "Build the test suite" OFF)

# This fucking thing will raise linker error on my laptop if config is not used.
# But using config on the pi will raise errors because it can't find the .cmake
find_package(Protobuf CONFIG QUIET)

if(NOT Protobuf_FOUND)
    find_package(Protobuf MODULE REQUIRED)
endif()

# Set proto file path correctly
set(PROTO_DIR "${CMAKE_SOURCE_DIR}/backend/proto") # Adjusted path
set(PROTO_FILE "${PROTO_DIR}/AV_TO_GCS_DATA_1.proto")

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Debug CACHE STRING "Build type" FORCE)
endif()

set(CMAKE_CXX_STANDARD 20) # For std::bit_cast
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_CXX_FLAGS_DEBUG "-O0 -g -Wall -Wextra -pthread")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG -Wall -Wextra -pthread")

set(SRC_DIR "${CMAKE_SOURCE_DIR}/backend/middleware")
set(BUILD_DIR ${CMAKE_BINARY_DIR}/build)

file(GLOB SRCS "${SRC_DIR}/*.cpp")

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${BUILD_DIR})

add_executable(middleware_server ${SRCS})

# Protobuf generation #18
# I'm just going to do this manually for now. It's fucked again
# Like this
# protoc --proto_path "${PWD}/backend/proto" --cpp_out="${PWD}/backend/proto/generated/payloads" "${PWD}/backend/proto/payloads/AV_TO_GCS_DATA_1.proto"
# https://github.com/protocolbuffers/protobuf/blob/main/docs/cmake_protobuf_generate.md

# Find all .proto files in the proto directory
file(GLOB_RECURSE PROTO_FILES "${CMAKE_CURRENT_LIST_DIR}/backend/proto/*.proto")
add_library(proto-objects OBJECT ${PROTO_FILES})
target_link_libraries(proto-objects PUBLIC protobuf::libprotobuf)
set(PROTO_BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/backend/proto/generated/payloads")
file(MAKE_DIRECTORY ${PROTO_BINARY_DIR})

target_include_directories(proto-objects PUBLIC "$<BUILD_INTERFACE:${PROTO_BINARY_DIR}>")

protobuf_generate(
    TARGET proto-objects
    IMPORT_DIRS "${CMAKE_CURRENT_LIST_DIR}/backend/proto"
    PROTOC_OUT_DIR "${PROTO_BINARY_DIR}"
    APPEND_PATH
    FILES ${PROTO_FILES}
)

# Add python protobuf generation
# For now just use  4249  protoc --proto_path=./backend/proto/payloads --python_out=./backend/proto/generated ./backend/proto/payloads/AV_TO_GCS_DATA_1.proto

# # Get all generated protobuf source files
# # TODO this might need to be edited after you start using things outside of payloads
# file(GLOB PROTO_SOURCES "${PROTO_BINARY_DIR}/payloads/*.pb.cc")

# Define DEBUG macro in debug builds
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_definitions(middleware_server PRIVATE DEBUG)
endif()

# Add the generated sources to your middleware executable
target_sources(middleware_server PRIVATE ${PROTO_SOURCES})

# Make sure middleware can find the generated headers
target_include_directories(middleware_server PRIVATE
    ${PROTO_BINARY_DIR}
    ${Protobuf_INCLUDE_DIRS}
)

# Find cppzmq
find_path(ZMQ_INCLUDE_DIR zmq.hpp
    HINTS /usr/local/include /opt/local/include /usr/include /opt/homebrew/Cellar/cppzmq/4.10.0/include $HOME/zeromq/zeromq-source/include
)

if(NOT ZMQ_INCLUDE_DIR)
    message(FATAL_ERROR "ZeroMQ headers not found")
endif()

# Find ZMQ library
find_library(ZMQ_LIBRARY NAMES zmq
    HINTS /usr/local/lib /opt/local/lib /usr/lib /opt/homebrew/Cellar/zeromq/4.3.4/lib
)

if(NOT ZMQ_LIBRARY)
    message(FATAL_ERROR "ZeroMQ library not found")
endif()

# Include directories
target_include_directories(middleware_server PRIVATE
    ${CMAKE_SOURCE_DIR}/generated # Protobuf generated headers
    ${Protobuf_INCLUDE_DIRS}
    ${ZMQ_INCLUDE_DIR}
    ${PROTO_DIR} # For proto file imports
    ${CMAKE_SOURCE_DIR}/backend/include # Add backend so that includes like "backend/process_logging.hpp" work
    ${CMAKE_SOURCE_DIR}/backend/middleware/payloads
    ${CMAKE_SOURCE_DIR}/backend/proto/generated/payloads
)

file(GLOB SEQUENCE_SRCS
    ${CMAKE_SOURCE_DIR}/backend/include/*.cpp
)
target_sources(middleware_server PRIVATE ${SEQUENCE_SRCS})

# Link libraries
target_link_libraries(middleware_server PRIVATE
    protobuf::libprotobuf # Modern target-based linking
    $<TARGET_OBJECTS:proto-objects>
    ${ZMQ_LIBRARY}
)

if(CMAKE_BUILD_TYPE STREQUAL "Release")
    set_target_properties(middleware_server PROPERTIES OUTPUT_NAME "middleware_server_release")
endif()

install(TARGETS middleware_server DESTINATION bin)
