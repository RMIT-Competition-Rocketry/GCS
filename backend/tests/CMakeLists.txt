# Auto installation and error validation is handled by parent CMake
find_package(GTest REQUIRED)

add_executable(runTests
    main.cpp
    dummy.cpp
    byteparser.cpp

    # test_sequence.cpp
    # test_sequence_lock.cpp
    # test_sequence.cpp
    # test_uart_interface.cpp
    # test_blackbox.cpp
)

# Link against the middleware library and GTest
target_link_libraries(runTests PRIVATE
    GTest::GTest
    GTest::Main
    middleware_lib
)

# Ensure test executable inherits middleware library's include directories
target_include_directories(runTests PRIVATE
    ${CMAKE_SOURCE_DIR}/backend/include
    ${CMAKE_SOURCE_DIR}/backend/proto/generated/payloads
)

add_test(NAME RunAllTests COMMAND runTests)