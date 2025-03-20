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

# target_include_directories(runTests PRIVATE
# ${GTEST_INCLUDE_DIRS}
# )

# # Add any other necessary includes
# target_include_directories(runTests PRIVATE
# ${CMAKE_SOURCE_DIR}/backend/include
# ${CMAKE_SOURCE_DIR}/backend/proto/generated
# )
add_test(NAME RunAllTests COMMAND runTests)
