# Packaging with uv

This document explains how PBIXRay MCP Server is packaged and distributed using [uv](https://github.com/astral-sh/uv).

## Why uv?

We've chosen to use uv for packaging and distribution because:

1. **Speed**: uv is significantly faster than traditional tools like pip
2. **Reliability**: uv provides improved dependency resolution
3. **Modern**: uv works well with modern Python packaging standards (PEP 517/518)

## Package Structure

The package is built using the following structure:

- `src/` - Contains the source code
- `pyproject.toml` - Modern Python packaging configuration
- `package.sh` - Helper script for common packaging tasks

## Using package.sh

The included `package.sh` script simplifies common tasks:

```bash
# Show all available commands
./package.sh --help

# Build the package (creates dist/ directory with wheel and sdist)
./package.sh build

# Install in development mode
./package.sh install

# Clean build artifacts
./package.sh clean

# Run tests
./package.sh test

# Publish to PyPI (requires PYPI_TOKEN environment variable)
export PYPI_TOKEN=your_token
./package.sh publish
```

## Manual Installation with uv

If you prefer to use uv commands directly:

```bash
# Install uv if needed
curl -sSf https://astral.sh/uv/install.sh | bash

# Build the package
uv build .

# Install the package (from PyPI)
uv pip install pbixray-mcp-server

# Install in development mode
uv pip install -e .
```

## Configuration Files

### pyproject.toml

This is the primary configuration file used for modern Python packaging. Key sections include:

- `[build-system]` - Specifies hatchling as the build backend
- `[project]` - Package metadata and dependencies
- `[tool.hatch.build.targets.wheel]` - Specifies the source directory
- `[project.scripts]` - Defines the entry point

### Dependencies

The package dependencies are defined in pyproject.toml and include:

```
dependencies = [
    "mcp>=1.2.0",
    "pbixray>=0.1.0", 
    "numpy>=1.20.0",
    "pandas>=1.0.0; python_version >= '3.10'",
    "pandas>=1.0.0,<2.0.0; python_version < '3.10'",
]
```

## Publishing Process

To publish a new version:

1. Update the version number in `pyproject.toml`
2. Run tests to ensure everything works correctly
3. Build the package: `./package.sh build`
4. Publish to PyPI: `./package.sh publish`

## Troubleshooting

If you encounter issues with packaging:

1. Ensure you have the latest version of uv
2. Check that the source code is in the correct location (src/)
3. Validate the pyproject.toml file
4. Clear previous build artifacts with `./package.sh clean`
