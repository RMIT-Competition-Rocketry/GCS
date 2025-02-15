cmake_minimum_required(VERSION 3.12)
project(middleware LANGUAGES CXX)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Debug CACHE STRING "Build type" FORCE)
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_CXX_FLAGS_DEBUG "-O0 -g -Wall -Wextra")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG -Wall -Wextra")

set(SRC_DIR "${CMAKE_SOURCE_DIR}/backend/middleware")
set(BUILD_DIR ${CMAKE_BINARY_DIR}/build)
file(GLOB SRCS "${SRC_DIR}/*.cpp")

# This line has to be before add_executable
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${BUILD_DIR})

add_executable(middleware ${SRCS})

# Find cppzmq for this project
# This line will need to be edited on different systems most likely
find_path(ZMQ_INCLUDE_DIR zmq.hpp
    HINTS /usr/local/include /opt/local/include /usr/include /opt/homebrew/Cellar/cppzmq/4.10.0/include
)

if(NOT ZMQ_INCLUDE_DIR OR NOT ZMQ_LIBRARY)
    message(FATAL_ERROR "ZeroMQ not found. Please install ZeroMQ or set ZMQ_INCLUDE_DIR and ZMQ_LIBRARY manually.")
endif()

# Include ZeroMQ headers
target_include_directories(middleware PRIVATE ${ZMQ_INCLUDE_DIR})

# Link against ZeroMQ
target_link_libraries(middleware PRIVATE ${ZMQ_LIBRARY})

install(TARGETS middleware DESTINATION bin)