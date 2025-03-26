# PBIXRay MCP Server

## Credits
* Hugoberry https://github.com/Hugoberry/pbixray
* rusiaaman https://github.com/rusiaaman/wcgw
* This was fully written by Claude using wcgw

A Model Context Protocol (MCP) server that exposes the capabilities of [PBIXRay](https://github.com/Hugoberry/pbixray) for LLM clients.

## Overview

This server allows language models to analyze Power BI (.pbix) files by exposing PBIXRay's functionality as MCP tools. It enables querying and extracting metadata, DAX expressions, tables, relationships, and other valuable information from Power BI models.

## Features

The server exposes all the major features of PBIXRay as MCP tools:

- Loading and analyzing PBIX files
- Listing tables in the model
- Retrieving model metadata
- Viewing Power Query (M) code
- Accessing M Parameters
- Checking model size
- Exploring DAX calculated tables
- Viewing DAX measures
- Examining DAX calculated columns
- Retrieving schema information
- Analyzing table relationships
- Accessing table contents
- Getting model statistics

## Installation

### Quick Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install mcp pbixray numpy
   ```

3. Run the server:
   ```bash
   python src/pbixray_server.py
   ```

For detailed installation instructions, including configuration with various MCP clients, see [INSTALLATION.md](INSTALLATION.md).

## Usage

### Running the Server

```bash
# Run the server directly
python src/pbixray_server.py

# OR use the MCP CLI
mcp run src/pbixray_server.py
```

### Testing with Sample Files

The repository includes a test script that demonstrates how to interact with the server using a sample PBIX file:

```bash
python tests/test_with_sample.py
```

This will load and analyze an AdventureWorks sample PBIX file, showing how to retrieve tables, measures, relationships, and other metadata.

### Interactive Demo

Try the interactive demo to explore all features:

```bash
python examples/demo.py
```

## Tool Overview

The server provides the following tools:

1. **load_pbix_file** - Load a Power BI file for analysis
2. **get_tables** - List all tables in the model
3. **get_metadata** - Get model metadata
4. **get_power_query** - Display Power Query (M) code
5. **get_m_parameters** - Display M Parameters values
6. **get_model_size** - Get the model size in bytes
7. **get_dax_tables** - View DAX calculated tables
8. **get_dax_measures** - Access DAX measures
9. **get_dax_columns** - Access calculated column DAX expressions
10. **get_schema** - Get model schema details
11. **get_relationships** - View table relationships
12. **get_table_contents** - Retrieve contents of a specified table
13. **get_statistics** - Get model statistics
14. **get_model_summary** - Get a comprehensive model summary

## Example Interactions

With the server running in an MCP client, you can ask questions like:

- "Can you help me load and analyze my Power BI file at /path/to/report.pbix?"
- "What tables are in my Power BI model?"
- "Show me all the DAX measures in my model."
- "What relationships exist between tables in my Power BI file?"
- "How large is my Power BI model?"
- "What Power Query transformations are used in this model?"

Your LLM client will use the appropriate tools to retrieve and present the information.

## Using with Windows Subsystem for Linux (WSL)

When using the PBIXRay MCP Server in WSL with Claude Desktop on Windows, you need to be aware of path differences when loading PBIX files.

### Path Conversion Guidelines

Windows paths (like `C:\Users\name\file.pbix`) cannot be directly accessed in WSL. Instead:

1. **Use WSL paths** when referencing files:
   - Windows: `C:\Users\name\Downloads\file.pbix`
   - WSL: `/mnt/c/Users/name/Downloads/file.pbix`

2. **Copy files to WSL** for easier access:
   ```bash
   mkdir -p ~/dev/pbixray-mcp/data
   cp /mnt/c/Users/name/Downloads/file.pbix ~/dev/pbixray-mcp/data/
   ```
   Then use: `/home/username/dev/pbixray-mcp/data/file.pbix`

3. **Example conversion table**:
   | Windows Path | WSL Path |
   |--------------|----------|
   | `C:\Users\Documents\file.pbix` | `/mnt/c/Users/Documents/file.pbix` |
   | `D:\Data\PowerBI\file.pbix` | `/mnt/d/Data/PowerBI/file.pbix` |

### Configuring Claude Desktop with WSL

When configuring Claude Desktop to use the server from WSL, use a launcher script:

1. Create a `run_server.sh` script in your project root:
   ```bash
   #!/bin/bash
   cd "$(dirname "$0")"
   source venv/bin/activate
   python src/pbixray_server.py
   ```

2. Make it executable:
   ```bash
   chmod +x run_server.sh
   ```

3. Configure Claude Desktop with:
   ```json
   "pbixray": {
     "command": "wsl.exe",
     "args": [
       "bash",
       "-c",
       "/home/username/dev/pbixray-mcp/run_server.sh"
     ]
   }
   ```

## Development

### Development Mode

To test the server during development, use the MCP Inspector:

```bash
mcp dev src/pbixray_server.py
```

This starts an interactive session where you can call tools and test responses.

### Project Structure

```
pbixray-mcp/
├── README.md            - This file
├── INSTALLATION.md      - Detailed installation instructions
├── src/                 - Source code
│   ├── __init__.py
│   └── pbixray_server.py
├── tests/               - Test scripts
│   ├── __init__.py
│   └── test_with_sample.py
├── examples/            - Example scripts and configs
│   ├── demo.py
│   └── config/
├── demo/                - Sample PBIX files
│   ├── README.md
│   └── AdventureWorks Sales.pbix
└── docs/                - Additional documentation
    └── ROADMAP.md
```

## Contributing

Contributions are welcome! Please see the [ROADMAP.md](docs/ROADMAP.md) for planned improvements and areas where help is needed.

## License

[MIT License](LICENSE)
