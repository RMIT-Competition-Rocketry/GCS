cmake_minimum_required(VERSION 3.22) # 3.31 is github runner
project(middleware_server LANGUAGES CXX)

option(BUILD_TESTS "Build the test suite" OFF)
option(FORCE_FETCH_DEPENDENCIES "Force fetching dependencies even if they are found by find_package" OFF)

set(CMAKE_CXX_STANDARD 20) # For std::bit_cast
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(CMAKE_CXX_COMPILER_ID STREQUAL "Clang" OR CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang")
    # For CMake 3.12+
    if(CMAKE_CXX_COMPILER_VERSION VERSION_GREATER_EQUAL "18.0.0")
        message(STATUS "Using Clang compiler (${CMAKE_CXX_COMPILER_VERSION}) - enforcing ABI compatibility with version 17")
        message(STATUS "Clang compiler forcing version 17 compatability")
        add_compile_options(-fclang-abi-compat=17)

        # For older CMake versions
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fclang-abi-compat=17")
    endif()
endif()

include(FetchContent)

# If you need to force an offline state, use set(FETCHCONTENT_FULLY_DISCONNECTED, ON)
# Use this for GCS device to avoid downloading dependencies

# Name is for internal targets, findname is for the find_package command
function(fetch_git_dependency NAME FIND_NAME URL VERSION)
    if(NOT FORCE_FETCH_DEPENDENCIES)
        find_package(${FIND_NAME} CONFIG QUIET)
    endif()

    if(FORCE_FETCH_DEPENDENCIES OR NOT ${FIND_NAME}_FOUND)
        if(NAME STREQUAL "libzmq" AND CMAKE_VERSION VERSION_GREATER_EQUAL "4.0.0")
            # TODO check on this and remove it when the noted pr is merged
            message(WARNING "libzqm auto install is likely to fail until resolution of https://github.com/zeromq/libzmq/pull/4776")
        endif()

        message(STATUS "Fetching ${NAME} from ${URL} (${VERSION})")
        FetchContent_Declare(
            ${NAME}
            GIT_REPOSITORY ${URL}
            GIT_TAG ${VERSION}
        )
        FetchContent_MakeAvailable(${NAME})
        find_package(${FIND_NAME} CONFIG)
        message(STATUS "${NAME} has been fetched and made available")
    else()
        message(STATUS "${FIND_NAME} found at: ${${FIND_NAME}_DIR}")
    endif()
endfunction()

# Abseil libraries for protobuf
fetch_git_dependency(abseil "absl" "https://github.com/abseil/abseil-cpp.git" "20250127.1")
set(protobuf_BUILD_TESTS OFF CACHE BOOL "Disable Protobuf tests" FORCE)

# Prevent Protobuf from exporting abseil-linked targets
set(protobuf_BUILD_EXPORT OFF CACHE BOOL "Disable protobuf target exports" FORCE)
set(protobuf_INSTALL OFF CACHE BOOL "Disable protobuf installation" FORCE)

# Force Protobuf to use our abseil
set(protobuf_ABSL_PROVIDER "package" CACHE STRING "Use existing abseil" FORCE)
set(protobufVersionString "v30.1" CACHE STRING "Protobuf version" FORCE)
fetch_git_dependency(Protobuf "Protobuf" "https://github.com/protocolbuffers/protobuf.git" ${protobufVersionString})

# Force static ZMQ build before fetching
set(BUILD_SHARED_LIBS OFF CACHE BOOL "Build static ZeroMQ libraries" FORCE)
set(BUILD_STATIC_LIBS ON CACHE BOOL "Build static ZeroMQ libraries" FORCE)
fetch_git_dependency(libzmq "ZeroMQ" "https://github.com/zeromq/libzmq.git" "v4.3.5")
set(CPPZMQ_BUILD_TESTS OFF CACHE BOOL "Disable cppzmq tests" FORCE)
fetch_git_dependency(cppzmq "cppzmq" "https://github.com/zeromq/cppzmq.git" "v4.10.0")

if(${Protobuf_DIR} STREQUAL "Protobuf_DIR-NOTFOUND")
    message(AUTHOR_WARNING "This is a manual blocking error to stop CMake from failing on the generate_proto steps for now. ")
    message(FATAL_ERROR "Protobuf not found. Please build from source on ${protobufVersionString} or run setup.sh")
endif()

find_library(UTF8_RANGE_LIBRARY NAMES utf8_range
    HINTS
    ${CMAKE_PREFIX_PATH}/lib
    $ENV{HOME}/protobuf-install/lib
    ${PROTOBUF_ROOT_DIR}/lib
    ${Protobuf_DIR}/../lib
    ${Protobuf_DIR}/../../lib)

find_path(UTF8_RANGE_INCLUDE_DIR NAMES utf8_range.h
    HINTS
    ${CMAKE_PREFIX_PATH}/include
    $ENV{HOME}/protobuf-install/include
    ${PROTOBUF_ROOT_DIR}/include
    ${Protobuf_DIR}/../include
    ${Protobuf_DIR}/../../include
    ${PROTOBUF_SOURCE_DIR}/third_party/utf8_range)
message(STATUS "utf8_range library found at:     ${UTF8_RANGE_LIBRARY}")
message(STATUS "utf8_range include dir found at: ${UTF8_RANGE_INCLUDE_DIR}")

# Set proto file path correctly
set(PROTO_DIR "${CMAKE_SOURCE_DIR}/backend/proto") # Adjusted path
set(PROTO_FILE "${PROTO_DIR}/AV_TO_GCS_DATA_1.proto")

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Debug CACHE STRING "Build type" FORCE)
endif()

set(SRC_DIR "${CMAKE_SOURCE_DIR}/backend/middleware")

file(GLOB_RECURSE LIB_SRCS
    "${SRC_DIR}/*.cpp"
    "${CMAKE_SOURCE_DIR}/backend/include/*.cpp"
)

# Separate main source file from sources (main.cpp)
list(REMOVE_ITEM LIB_SRCS "${SRC_DIR}/main.cpp")
set(MAIN_SRC "${SRC_DIR}/main.cpp")
file(MAKE_DIRECTORY ${CMAKE_BINARY_DIR})

add_library(middleware_lib ${LIB_SRCS})
add_executable(middleware_server ${MAIN_SRC})

target_compile_options(middleware_lib PRIVATE
    $<$<CONFIG:Debug>:-O0 -g -Wall -Wextra -pthread>
    $<$<CONFIG:Release>:-O3 -DNDEBUG -Wall -Wextra -pthread>
)

# Protobuf generation for cpp and python files
# Docs: https://github.com/protocolbuffers/protobuf/blob/main/docs/cmake_protobuf_generate.md
file(GLOB_RECURSE PROTO_FILES "${CMAKE_CURRENT_LIST_DIR}/backend/proto/*.proto")
add_library(proto-objects OBJECT ${PROTO_FILES})
target_link_libraries(proto-objects PUBLIC
    protobuf::libprotobuf
    ${UTF8_RANGE_LIBRARY}
    absl::base
    absl::log
    absl::strings
    absl::log_internal_check_op
    absl::log_internal_message
    absl::cord_internal
    absl::cord
    absl::raw_logging_internal
    absl::spinlock_wait
    absl::synchronization
    absl::hash
    absl::status
    absl::statusor
    absl::flat_hash_map
)
set(PROTO_BINARY_DIR "${CMAKE_SOURCE_DIR}/backend/proto/generated/")
file(MAKE_DIRECTORY ${PROTO_BINARY_DIR})

target_include_directories(proto-objects PUBLIC "$<BUILD_INTERFACE:${PROTO_BINARY_DIR}>")

set(FIX_IMPORT_SCRIPT "${CMAKE_CURRENT_SOURCE_DIR}/scripts/__proto_import_fix.sh")

# Make script executable
configure_file(
    ${FIX_IMPORT_SCRIPT}
    ${CMAKE_CURRENT_BINARY_DIR}/fix_imports.sh
    FILE_PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE
)

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

add_custom_target(fix-proto-imports ALL
    COMMAND ${CMAKE_CURRENT_BINARY_DIR}/fix_imports.sh
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMENT "Fixing Python proto imports"
    VERBATIM
)

add_dependencies(fix-proto-imports proto-objects)
add_dependencies(middleware_server fix-proto-imports)

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
    ${UTF8_RANGE_INCLUDE_DIR}
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
# Absl libaries do not link themselves. Fuck you absl
target_link_libraries(middleware_lib PUBLIC
    protobuf::libprotobuf
    $<TARGET_OBJECTS:proto-objects>
    ${UTF8_RANGE_LIBRARY}
    absl::base
    absl::strings
    absl::log
    absl::log_internal_check_op
    absl::log_internal_message
    absl::cord_internal
    absl::cord
    absl::raw_logging_internal
    absl::spinlock_wait
    absl::synchronization
    absl::hash
    absl::status
    absl::statusor
    absl::flat_hash_map
    cppzmq
    libzmq
    m
)

target_link_libraries(middleware_server PUBLIC middleware_lib)

# Add RPATH settings for the middleware server executable as well
if(APPLE)
    set_target_properties(middleware_server PROPERTIES
        BUILD_WITH_INSTALL_RPATH TRUE
        INSTALL_RPATH "@loader_path;@loader_path/../lib;/usr/local/lib"
        MACOSX_RPATH TRUE
    )
endif()

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
file(GLOB OLD_BINARIES "${CMAKE_BINARY_DIR}/middleware_*")

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
