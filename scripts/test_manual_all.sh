set -e;
mkdir -p build
cd build;

cmake -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTS=ON  ..;
make;

echo "Running C++ and python tests with default compiler in Debug mode";
ctest --output-on-failure  --test-dir backend/tests --verbose;