#!/bin/bash

CLI_PYTHON_FILE="rocket.py"
EXEC_NAME="rocket"
PROTOBUF_VERSION="30.1"
PROTOBUF_MAJOR_VERSION="30"

# Check if Python3 is installed and meets the required version (>= 3.11)
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    echo "Error: Python3 version $python_version is less than the required version $required_version. Please install >= Python3.11 and add it to your PATH to proceed." >&2
    exit 1
fi

if [ ! -f "$CLI_PYTHON_FILE" ]; then
    echo "Error: $CLI_PYTHON_FILE not found." >&2
    exit 1
fi

check_protobuf_installed() {
    if command -v protoc &> /dev/null; then
        protoc_version=$(protoc --version | awk '{print $2}')
        protoc_major_version=$(echo $protoc_version | cut -d. -f1)
        echo "Found protobuf version $protoc_version"
        if [[ $protoc_major_version == "$PROTOBUF_MAJOR_VERSION" ]]; then
            echo "Required protobuf major version $PROTOBUF_MAJOR_VERSION is already installed (found $protoc_version)."
            return 0
        else
            echo "Warning: Found protobuf version $protoc_version, but major version $PROTOBUF_MAJOR_VERSION is required."
            read -p "Do you want to install protobuf v$PROTOBUF_VERSION? (y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Skipping protobuf installation. Note that this might cause compatibility issues."
                return 0
            fi
        fi
    fi
    return 1
}

install_protobuf() {
    if ! command -v git &> /dev/null; then
        echo "Error: git is not installed. Please install git to proceed with protobuf installation." >&2
        return 1
    fi

    if ! command -v cmake &> /dev/null; then
        echo "Error: cmake is not installed. Please install cmake to proceed with protobuf installation." >&2
        return 1
    fi

    if ! command -v make &> /dev/null; then
        echo "Error: make is not installed. Please install make to proceed with protobuf installation." >&2
        return 1
    fi

    echo "Installing protobuf v$PROTOBUF_VERSION..."
    
    # Create temp directory for protobuf if it doesn't exist
    if [ -d "$HOME/protobuf" ]; then
        echo "Warning: $HOME/protobuf directory already exists."
        read -p "Do you want to remove it and continue with installation? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$HOME/protobuf"
        else
            echo "Skipping protobuf installation."
            return 1
        fi
    fi
    
    git clone https://github.com/protocolbuffers/protobuf.git "$HOME/protobuf"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to clone protobuf repository." >&2
        return 1
    fi
    
    cd "$HOME/protobuf"
    git checkout "v$PROTOBUF_VERSION"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to checkout protobuf v$PROTOBUF_VERSION." >&2
        cd - > /dev/null
        return 1
    fi
    
    git submodule update --init --recursive
    if [ $? -ne 0 ]; then
        echo "Error: Failed to update protobuf submodules." >&2
        cd - > /dev/null
        return 1
    fi
    
    mkdir -p build && cd build
    cmake -Dprotobuf_BUILD_TESTS=OFF ..
    if [ $? -ne 0 ]; then
        echo "Error: CMAKE configuration failed." >&2
        cd - > /dev/null
        return 1
    fi
    
    sudo make install
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install protobuf. Make sure you have sudo privileges." >&2
        cd - > /dev/null
        return 1
    fi
    
    sudo ldconfig
    echo "Protobuf v$PROTOBUF_VERSION installation completed successfully."
    
    # Return to original directory
    cd - > /dev/null
    return 0
}

# Check and install protobuf if needed
if ! check_protobuf_installed; then
    install_protobuf
    if [ $? -ne 0 ]; then
        echo "Warning: Protobuf installation failed. Some features may not work correctly."
    fi
fi

if [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "darwin"* ]]; then
    # Make the CLI script executable 
    chmod +x "$CLI_PYTHON_FILE"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to make $CLI_PYTHON_FILE executable." >&2
        exit 1
    fi
    
    # NOTE: Using relative paths for now. No need to add this to PATH

    # Create a symbolic link in /usr/local/bin (or another directory in $PATH)
    if [ -d "/usr/local/bin" ]; then
        echo "Creating symbolic link"
        sudo ln -sf "$(pwd)/$CLI_PYTHON_FILE" /usr/local/bin/$EXEC_NAME
        if [ $? -ne 0 ]; then
            echo "Error: Failed to create symlink. Please ensure you have the correct privileges" >&2
            exit 1
        fi
        echo "Unix setup completed."
    else
        echo "Warning: /usr/local/bin not found. You may need to add the script manually to your $PATH."
    fi
fi

# Windows setup 
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    BATCH_FILE="rocket.bat"
    chmod +x "$BATCH_FILE"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to add execution privileges to $BATCH_FILE" >&2
        exit 1
    fi
    # Add to path here in future if needed
    echo "Windows setup completed."
fi