# Using uv with PBIXRay MCP Server

This guide explains how to use [uv](https://github.com/astral-sh/uv) for Python environment management with the PBIXRay MCP Server project.

## What is uv?

uv is a modern Python toolchain that includes:

- An extremely fast package installer and resolver
- A Python environment manager
- A reliable, reproducible lockfile generator
- A build system for Python packages

uv is designed to be faster and more reliable than traditional tools like pip and virtualenv.

## Quick Start

For the fastest setup, run:

```bash
./setup_dev.sh
```

This will:
1. Install uv if not already installed
2. Create a Python environment with all project dependencies
3. Install development dependencies
4. Build the package

## Manual Setup

### 1. Install uv

If you don't have uv installed:

```bash
curl -sSf https://astral.sh/uv/install.sh | bash
```

This will install uv to `~/.local/bin/uv`. Make sure this directory is in your PATH.

### 2. Create a Python Environment

Create a virtual environment with uv:

```bash
# Using our helper script
./uv_environment.sh create

# Or manually with uv
uv venv pbixray-env --python=3.10
```

### 3. Activate the Environment

```bash
source pbixray-env/bin/activate
```

### 4. Install Development Dependencies

```bash
# Using our helper script
./uv_environment.sh dev

# Or manually with uv
uv pip install -r requirements-dev.txt
```

## Daily Development Tasks

### Managing Dependencies

```bash
# Update project dependencies
./uv_environment.sh update

# Install specific packages
uv pip install package-name

# Install in development mode
./uv_environment.sh install
# or
uv pip install -e .
```

### Running Tests

```bash
# Using our helper script
./uv_environment.sh test

# Or manually
python -m pytest
```

### Linting Code

```bash
# Using our helper script
./uv_environment.sh lint

# Or manually
black src tests
flake8 src tests
```

## Building and Packaging

```bash
# Using our helper script
./package.sh build

# Or manually with uv
uv build .
```

## Advanced uv Features

### Lockfiles

Generate a lockfile for reproducible environments:

```bash
uv lock
```

This creates a `requirements.lock` file that you can commit to version control.

### Exporting Requirements

Export your environment to a requirements.txt file:

```bash
uv pip freeze > requirements.txt
```

### Pip Compatibility

uv is designed to be compatible with pip, so you can use pip commands with uv:

```bash
uv pip install -r requirements.txt
uv pip list
uv pip show package-name
```

## Configuration

uv configuration is stored in `uv.toml` at the project root. Key settings include:

- Default Python version
- Parallelization settings
- Tool configurations
- Virtual environment settings

## Troubleshooting

If you encounter issues:

1. Make sure uv is in your PATH
2. Check that you're using the correct Python version
3. Try deleting and recreating the environment
4. Update uv to the latest version: `uv self update`

## Using with Claude Desktop

To configure Claude Desktop to use the MCP server with your uv-managed environment, add the following to your Claude Desktop configuration file (typically `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "pbixray": {
      "command": "bash",
      "args": [
        "-c",
        "source ~/dev/pbixray-mcp/pbixray-env/bin/activate && python ~/dev/pbixray-mcp/src/pbixray_server.py"
      ],
      "env": {}
    }
  }
}
```

For Windows users with WSL:

```json
{
  "mcpServers": {
    "pbixray": {
      "command": "wsl.exe",
      "args": [
        "bash",
        "-c",
        "source ~/dev/pbixray-mcp/pbixray-env/bin/activate && python ~/dev/pbixray-mcp/src/pbixray_server.py"
      ]
    }
  }
}
```

Add command-line options if needed:

```json
{
  "mcpServers": {
    "pbixray": {
      "command": "bash",
      "args": [
        "-c",
        "source ~/dev/pbixray-mcp/pbixray-env/bin/activate && python ~/dev/pbixray-mcp/src/pbixray_server.py --max-rows 50 --page-size 20"
      ],
      "env": {}
    }
  }
}
```

After saving the configuration file, restart Claude Desktop and select the "pbixray" MCP server when starting a conversation.

## Resources

- [uv Documentation](https://github.com/astral-sh/uv)
- [uv vs pip Comparison](https://astral.sh/blog/uv)
