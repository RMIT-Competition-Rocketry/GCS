cmake_minimum_required(VERSION 3.12)
project(middleware_server LANGUAGES CXX)

option(BUILD_TESTS "Build the test suite" OFF)

# Find Protobuf
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

file(GLOB_RECURSE LIB_SRCS
    "${SRC_DIR}/*.cpp"
    "${CMAKE_SOURCE_DIR}/backend/include/*.cpp"
)

# Separate main source file from sources (main.cpp)
list(REMOVE_ITEM LIB_SRCS "${SRC_DIR}/main.cpp")
set(MAIN_SRC "${SRC_DIR}/main.cpp")
file(MAKE_DIRECTORY ${BUILD_DIR})

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${BUILD_DIR})

add_library(middleware_lib ${LIB_SRCS})
add_executable(middleware_server ${MAIN_SRC})

# Protobuf generation for cpp and python files
# Docs: https://github.com/protocolbuffers/protobuf/blob/main/docs/cmake_protobuf_generate.md
file(GLOB_RECURSE PROTO_FILES "${CMAKE_CURRENT_LIST_DIR}/backend/proto/*.proto")
add_library(proto-objects OBJECT ${PROTO_FILES})
target_link_libraries(proto-objects PUBLIC protobuf::libprotobuf)
set(PROTO_BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/backend/proto/generated/")
file(MAKE_DIRECTORY ${PROTO_BINARY_DIR})

target_include_directories(proto-objects PUBLIC "$<BUILD_INTERFACE:${PROTO_BINARY_DIR}>")

protobuf_generate(
    LANGUAGE cpp
    TARGET proto-objects
    IMPORT_DIRS "${CMAKE_CURRENT_LIST_DIR}/backend/proto"
    PROTOC_OUT_DIR "${PROTO_BINARY_DIR}"
    APPEND_PATH
    FILES ${PROTO_FILES}
)

protobuf_generate(
    LANGUAGE python
    TARGET proto-objects
    IMPORT_DIRS "${CMAKE_CURRENT_LIST_DIR}/backend/proto"
    PROTOC_OUT_DIR "${PROTO_BINARY_DIR}"
    APPEND_PATH
    FILES ${PROTO_FILES}
)

# Define DEBUG macro in debug builds
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_definitions(middleware_lib PUBLIC DEBUG)
endif()

# Add the generated sources to your middleware executable
target_sources(middleware_server PUBLIC ${PROTO_SOURCES})

# Make sure middleware can find the generated headers
target_include_directories(middleware_server PUBLIC
    ${PROTO_BINARY_DIR}
    ${Protobuf_INCLUDE_DIRS}
)

# Find cppzmq
find_path(ZMQ_INCLUDE_DIR zmq.hpp
    HINTS
    /usr/local/include
    /opt/local/include
    /usr/include
    /opt/homebrew/Cellar/cppzmq/4.10.0/include
    $ENV{HOME}/zeromq/zeromq-source/include
    $ENV{HOME}/cppzmq-install/include
    $ENV{HOME}/cppzmq-install/share/cmake/cppzmq
)

# Find ZeroMQ C headers (zmq.h)
find_path(ZMQ_C_INCLUDE_DIR zmq.h
    HINTS
    /usr/local/include
    /opt/local/include
    /usr/include
    $ENV{HOME}/zeromq/zeromq-source/include
    $ENV{HOME}/zeromq-install/include
)

if(NOT ZMQ_C_INCLUDE_DIR)
    message(FATAL_ERROR "ZeroMQ C headers (zmq.h) not found")
endif()

if(NOT ZMQ_INCLUDE_DIR)
    message(FATAL_ERROR "ZeroMQ headers not found")
endif()

# Find ZMQ library
find_library(ZMQ_LIBRARY NAMES zmq
    HINTS
    /usr/local/lib
    /opt/local/lib
    /usr/lib
    /opt/homebrew/Cellar/zeromq/4.3.4/lib
    $ENV{HOME}/zeromq-install/lib
)

if(NOT ZMQ_LIBRARY)
    message(FATAL_ERROR "ZeroMQ library not found")
endif()

# Include directories
target_include_directories(middleware_lib PUBLIC
    ${CMAKE_SOURCE_DIR}/generated # Protobuf generated headers
    ${Protobuf_INCLUDE_DIRS}
    ${ZMQ_INCLUDE_DIR}
    ${ZMQ_C_INCLUDE_DIR}
    ${PROTO_DIR} # For proto file imports
    ${CMAKE_SOURCE_DIR}/backend/include # Add backend so that includes like "backend/process_logging.hpp" work
    ${CMAKE_SOURCE_DIR}/backend/middleware/payloads
    ${CMAKE_SOURCE_DIR}/backend/proto/generated/payloads
)

# Link libraries
target_link_libraries(middleware_lib PUBLIC
    protobuf::libprotobuf # Modern target-based linking
    $<TARGET_OBJECTS:proto-objects>
    ${ZMQ_LIBRARY}
    m
)

target_link_libraries(middleware_server PUBLIC middleware_lib)

if(CMAKE_BUILD_TYPE STREQUAL "Release")
    set_target_properties(middleware_server PROPERTIES OUTPUT_NAME "middleware_server_release")
endif()

install(TARGETS middleware_server DESTINATION bin)

if(BUILD_TESTS)
    enable_testing() # Enables CTest
    message(STATUS "Building tests")
    find_package(GTest CONFIG QUIET)

    if(NOT GTest_FOUND)
        message(STATUS "Installing GTest")
        include(FetchContent)
        FetchContent_Declare(
            googletest
            URL https://github.com/google/googletest/archive/e7b26b72461e0bfcb5a2a9c1cafd849108f834ae.zip
            DOWNLOAD_EXTRACT_TIMESTAMP TRUE
        )

        FetchContent_MakeAvailable(googletest)
    else()
        message(STATUS "GoogleTest found at: ${GTest_DIR}")
    endif()

    add_subdirectory(backend/tests)
endif()
