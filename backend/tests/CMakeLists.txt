# Auto installation and error validation is handled by parent CMake
find_package(GTest REQUIRED)

set(CPP_TEST_DIR "${CMAKE_CURRENT_SOURCE_DIR}/cpp_tests")

add_executable(runC++Tests
    main.cpp
    ${CPP_TEST_DIR}/dummy.cpp
    ${CPP_TEST_DIR}/byteparser.cpp
)

# Link against the middleware library and GTest
target_link_libraries(runC++Tests PRIVATE
    GTest::GTest
    GTest::Main
    middleware_lib
)

# Ensure test executable inherits middleware library's include directories
target_include_directories(runC++Tests PRIVATE
    ${UTF8_RANGE_INCLUDE_DIR}
    ${CMAKE_SOURCE_DIR}/backend/include
    ${CMAKE_SOURCE_DIR}/backend/proto/generated/payloads
)

if(APPLE)
    set_target_properties(runC++Tests PROPERTIES
        BUILD_WITH_INSTALL_RPATH TRUE
        INSTALL_RPATH "@loader_path;@loader_path/../lib;/usr/local/lib"
        MACOSX_RPATH TRUE
    )
endif()

add_test(NAME RunAllC++Tests COMMAND runC++Tests)
set(PYTHON_TEST_SCRIPT_PATH "${CMAKE_SOURCE_DIR}/scripts/test_manual_python.sh")
execute_process(COMMAND chmod +x ${PYTHON_TEST_SCRIPT_PATH})
add_test(NAME PythonTests COMMAND ${PYTHON_TEST_SCRIPT_PATH})
set_tests_properties(PythonTests PROPERTIES
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
)