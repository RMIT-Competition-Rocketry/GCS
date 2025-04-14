cmake_minimum_required(VERSION 3.12)
project(middleware_server LANGUAGES CXX)

option(BUILD_TESTS "Build the test suite" OFF)

set(CMAKE_CXX_STANDARD 20) # For std::bit_cast
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)

# If you need to force an offline state, use set(FETCHCONTENT_FULLY_DISCONNECTED, ON)
# Use this for GCS device to avoid downloading dependencies

# Abseil libraries for protobuf
find_package(abseil QUIET)
if(NOT abseil_FOUND)
    message(STATUS "Fetching abseil")
    FetchContent_Declare(
    abseil
    GIT_REPOSITORY https://github.com/abseil/abseil-cpp.git
    GIT_TAG 20250127.0
    )  
    FetchContent_MakeAvailable(abseil)
endif()

find_package(Protobuf QUIET)
if(NOT Protobuf_FOUND)
    message(STATUS "Fetching protobuf")
    FetchContent_Declare(
    Protobuf
    GIT_REPOSITORY https://github.com/protocolbuffers/protobuf.git
    GIT_TAG v29.3
    )  
    FetchContent_MakeAvailable(Protobuf)
endif()
 
find_package(libzmq QUIET)
if(NOT libzmq_FOUND)
    message(STATUS "Fetching libzmq")
    FetchContent_Declare(
        libzmq
        GIT_REPOSITORY https://github.com/zeromq/libzmq.git
        GIT_TAG v4.3.5
    )
    FetchContent_MakeAvailable(libzmq)
endif()

find_package(cppzmq QUIET)
if(NOT cppzmq_FOUND)
    message(STATUS "Fetching cppzmq")
    FetchContent_Declare(
        cppzmq
        GIT_REPOSITORY https://github.com/zeromq/cppzmq.git
        GIT_TAG v4.10.0
    )
    FetchContent_MakeAvailable(cppzmq)
endif()


# Set proto file path correctly
set(PROTO_DIR "${CMAKE_SOURCE_DIR}/backend/proto") # Adjusted path
set(PROTO_FILE "${PROTO_DIR}/AV_TO_GCS_DATA_1.proto")

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Debug CACHE STRING "Build type" FORCE)
endif()

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
target_link_libraries(proto-objects PUBLIC 
    protobuf::libprotobuf
    absl::base
    absl::log
    absl::strings
    absl::log_internal_check_op
    absl::log_internal_message
)
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
    protobuf::libprotobuf 
    absl::base
    absl::log
    absl::strings
    absl::log_internal_check_op
    absl::log_internal_message
    $<TARGET_OBJECTS:proto-objects>
    cppzmq
    m
)

target_link_libraries(middleware_server PUBLIC middleware_lib)

file(STRINGS VERSION PROJECT_VERSION)

# Get current git commit hash
execute_process(
    COMMAND git rev-parse --short HEAD
    OUTPUT_VARIABLE GIT_COMMIT
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

# Same as $ uname -m -> "arm64"
set(TARGET_ARCH ${CMAKE_SYSTEM_PROCESSOR})

# Clean up old binaries with different names before building
file(GLOB OLD_BINARIES "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/middleware_*")

if(OLD_BINARIES)
    message(STATUS "Cleaning up old binaries: ${OLD_BINARIES}")
    file(REMOVE ${OLD_BINARIES})
endif()

if(CMAKE_BUILD_TYPE STREQUAL "Release")
    set_target_properties(middleware_server PROPERTIES OUTPUT_NAME "middleware_release_${TARGET_ARCH}_${PROJECT_VERSION}+${GIT_COMMIT}")
else()
    set_target_properties(middleware_server PROPERTIES OUTPUT_NAME "middleware_debug_${TARGET_ARCH}_${PROJECT_VERSION}+${GIT_COMMIT}")
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
            GIT_REPOSITORY https://github.com/google/googletest.git
            GIT_TAG v1.16.0
        )
        FetchContent_MakeAvailable(googletest)
    else()
        message(STATUS "GoogleTest found at: ${GTest_DIR}")
    endif()

    add_subdirectory(backend/tests)
endif()
