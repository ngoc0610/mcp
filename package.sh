#!/bin/bash
# package.sh - Script to package and distribute PBIXRay MCP Server using uv

set -e  # Exit on error

# Make sure uv is in the PATH
if ! command -v uv &> /dev/null; then
    # If uv is installed in ~/.local/bin but not in PATH, add it
    if [ -f ~/.local/bin/uv ]; then
        export PATH="$PATH:$HOME/.local/bin"
        echo "Added ~/.local/bin to PATH"
    else
        echo "Error: uv is not installed. Install it with:"
        echo "curl -sSf https://astral.sh/uv/install.sh | bash"
        exit 1
    fi
fi

# Ensure we're in the project directory
cd "$(dirname "$0")"

# Show help if requested
if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    echo "Usage: ./package.sh [command]"
    echo ""
    echo "Commands:"
    echo "  build        Build the package (default)"
    echo "  install      Install the package in development mode"
    echo "  publish      Publish the package to PyPI"
    echo "  clean        Remove build artifacts"
    echo "  test         Run tests"
    echo ""
    exit 0
fi

# Default command is 'build'
COMMAND=${1:-build}

case "$COMMAND" in
    build)
        echo "Building package..."
        # Clean up previous builds
        rm -rf dist/ build/ *.egg-info
        
        # Build the package
        uv build .
        echo "Build complete. Distribution files in ./dist/"
        ls -l dist/
        ;;
    
    install)
        echo "Installing in development mode..."
        uv pip install -e .
        echo "Installation complete."
        ;;
    
    publish)
        echo "Publishing to PyPI..."
        # Build first if dist directory doesn't exist or is empty
        if [ ! -d "dist" ] || [ -z "$(ls -A dist)" ]; then
            echo "No distribution files found. Building first..."
            rm -rf dist/ build/ *.egg-info
            uv build .
        fi
        
        # Check if PyPI token is set
        if [ -z "$PYPI_TOKEN" ]; then
            echo "Error: PYPI_TOKEN environment variable not set."
            echo "Set it with: export PYPI_TOKEN=your_token"
            exit 1
        fi
        
        # Publish to PyPI
        uv publish
        echo "Publication complete."
        ;;
    
    clean)
        echo "Cleaning build artifacts..."
        rm -rf dist/ build/ *.egg-info
        echo "Clean complete."
        ;;
    
    test)
        echo "Running tests..."
        uv pip install pytest
        python -m pytest
        echo "Tests complete."
        ;;
    
    *)
        echo "Error: Unknown command '$COMMAND'"
        echo "Run ./package.sh --help for usage information."
        exit 1
        ;;
esac

exit 0
