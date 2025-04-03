#!/bin/bash
# uv_environment.sh - Script for managing Python environments with uv

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

# Define environment name and Python version
ENV_NAME="pbixray-env"
PYTHON_VERSION="3.10"  # Change this to your preferred version

# Show help if requested
if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    echo "Usage: ./uv_environment.sh [command]"
    echo ""
    echo "Commands:"
    echo "  create       Create a new virtual environment (default)"
    echo "  update       Update dependencies in the environment"
    echo "  activate     Print command to activate the environment"
    echo "  install      Install project in development mode"
    echo "  dev          Install development dependencies"
    echo "  test         Run tests in the environment"
    echo "  lint         Run linting tools"
    echo "  list         List installed packages"
    echo ""
    echo "Environment: ${ENV_NAME} (Python ${PYTHON_VERSION})"
    exit 0
fi

# Default command is 'create'
COMMAND=${1:-create}

case "$COMMAND" in
    create)
        echo "Creating environment '${ENV_NAME}' with Python ${PYTHON_VERSION}..."
        uv venv ${ENV_NAME} --python=${PYTHON_VERSION}
        
        echo "Installing dependencies..."
        # Activate the environment first
        source ${ENV_NAME}/bin/activate
        uv pip install -e .
        
        echo ""
        echo "Environment created successfully!"
        echo "Activate it with: source ${ENV_NAME}/bin/activate"
        ;;
    
    update)
        echo "Updating dependencies in environment '${ENV_NAME}'..."
        source ${ENV_NAME}/bin/activate
        uv pip install -e .
        echo "Dependencies updated."
        echo ""
        echo "To update development dependencies as well, run: ./uv_environment.sh dev"
        ;;
    
    activate)
        echo "To activate the environment, run:"
        echo ""
        echo "source ${ENV_NAME}/bin/activate"
        echo ""
        echo "You may want to copy and paste this command."
        ;;
    
    install)
        echo "Installing project in development mode..."
        source ${ENV_NAME}/bin/activate
        uv pip install -e .
        echo "Installation complete."
        ;;
    
    dev)
        echo "Installing development dependencies in '${ENV_NAME}'..."
        source ${ENV_NAME}/bin/activate
        uv pip install -r requirements-dev.txt
        echo "Development dependencies installed."
        ;;
    
    test)
        echo "Running tests in environment '${ENV_NAME}'..."
        source ${ENV_NAME}/bin/activate
        uv pip install pytest
        python -m pytest
        echo "Tests complete."
        ;;
        
    lint)
        echo "Running linters in environment '${ENV_NAME}'..."
        
        # Make sure linting tools are installed
        source ${ENV_NAME}/bin/activate
        uv pip install black flake8
        
        echo "Running black..."
        black --check src tests
        
        echo "Running flake8..."
        flake8 src tests
        
        echo "Linting complete."
        ;;
    
    list)
        echo "Packages installed in environment '${ENV_NAME}':"
        source ${ENV_NAME}/bin/activate
        pip list
        ;;
    
    *)
        echo "Error: Unknown command '$COMMAND'"
        echo "Run ./uv_environment.sh --help for usage information."
        exit 1
        ;;
esac

exit 0
