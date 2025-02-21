#!/bin/bash

CLI_PYTHON_FILE="rocket.py"
EXEC_NAME="rocket"

# Check if Python3 is installed and meets the required version (>= 3.10)
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.10"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    echo "Error: Python3 version $python_version is less than the required version $required_version. Please install >= Python3.10 and add it to your PATH to proceed." >&2
    exit 1
fi

if [ ! -f "$CLI_PYTHON_FILE" ]; then
    echo "Error: $CLI_PYTHON_FILE not found." >&2
    exit 1
fi

if [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "darwin"* ]]; then
    # Make the CLI script executable 
    chmod +x "$CLI_PYTHON_FILE"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to make $SCRIPT_NAME executable." >&2
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
