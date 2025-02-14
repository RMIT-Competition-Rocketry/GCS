CXX := g++
CXXFLAGS := -Wall -Wextra -std=c++17
LDFLAGS :=  # Add linker flags if needed

SRC_DIR := backend/middleware
# Build is gitignored by default. Will have to make this dir
BUILD_DIR := build

# Find all .cpp files in /backend/middleware
SRCS := $(wildcard $(SRC_DIR)/*.cpp)
OBJS := $(patsubst $(SRC_DIR)/%.cpp, $(BUILD_DIR)/%.o, $(SRCS))

MAIN_SRC := $(SRC_DIR)/middleware.cpp
MAIN_OBJ := $(BUILD_DIR)/middleware.o

# Executable output name. This goes in root
TARGET := $(BUILD_DIR)/middleware

.DEFAULT_GOAL := build-dev

# Debug print 
# $(info SRC_DIR: $(SRC_DIR))
# $(info SRCS: $(SRCS))
# $(info OBJS: $(OBJS))

# Development build (with debugging symbols)
# Enforce level 0 optimisation so all variables are visible in dev
build-dev: CXXFLAGS += -O0 -g 
build-dev: $(TARGET)
	@echo "Development build complete"

build-release: CXXFLAGS += -O3 -DNDEBUG
build-release: $(TARGET)
	@echo "Release build complete"

# Rule to link the final executable
$(TARGET): $(OBJS)
	@echo "Linking $@"
	$(CXX) $(CXXFLAGS) $(OBJS) -o $(TARGET) $(LDFLAGS)

# Rule to compile .cpp files into .o files
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp
	mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -rf $(BUILD_DIR)