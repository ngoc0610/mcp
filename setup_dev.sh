#!/bin/bash
# setup_dev.sh - One-command setup for development environment with uv

set -e  # Exit on error

# Make sure the script runs from the project root
cd "$(dirname "$0")"

echo "==== Setting Up PBIXRay MCP Development Environment ===="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    # If uv is in ~/.local/bin but not in PATH, add it
    if [ -f ~/.local/bin/uv ]; then
        export PATH="$PATH:$HOME/.local/bin"
        echo "Added ~/.local/bin to PATH"
    else
        echo "uv not found. Installing uv..."
        curl -sSf https://astral.sh/uv/install.sh | bash
        
        # Add uv to PATH for this session
        export PATH="$PATH:$HOME/.local/bin"
        echo "uv installed successfully"
    fi
fi

echo ""
echo "1. Creating Python environment with uv..."
./uv_environment.sh create

echo ""
echo "2. Installing development dependencies..."
./uv_environment.sh dev

echo ""
echo "3. Building the package..."
./package.sh build

echo ""
echo "==== Development Environment Setup Complete ===="
echo ""
echo "To activate your environment, run:"
echo "source pbixray-env/bin/activate"
echo ""
echo "Available commands:"
echo "- ./uv_environment.sh - Manage Python environment"
echo "- ./package.sh - Build and package the project"
echo ""
echo "Happy coding!"
