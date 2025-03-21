# Auto installation and error validation is handled by parent CMake
find_package(GTest REQUIRED)

add_executable(runTests
    main.cpp
    dummy.cpp

    # test_sequence.cpp
    # test_sequence_lock.cpp
    # test_uart_interface.cpp
    # test_blackbox.cpp
)

target_link_libraries(runTests PRIVATE
    GTest::GTest
    GTest::Main
)

add_test(NAME RunAllTests COMMAND runTests)
