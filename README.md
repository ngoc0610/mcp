# PBIXRay MCP Server

A Model Context Protocol (MCP) server that exposes the capabilities of [PBIXRay](https://github.com/Hugoberry/pbixray) for LLM clients like Claude.

![PBIXRay MCP Server](https://github.com/Hugoberry/pbixray/raw/master/docs/img/logo.png)

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

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install mcp pbixray numpy
   ```

## Usage

### Running the server

```bash
# Run the server directly
python pbixray_server.py

# OR use the MCP CLI
mcp run pbixray_server.py
```

### Testing with sample files

The repository includes a test script that demonstrates how to interact with the server using a sample PBIX file:

```bash
python test_with_sample.py
```

This will load and analyze an AdventureWorks sample PBIX file, showing how to retrieve tables, measures, relationships, and other metadata.

### Installing in Claude Desktop

To use this server with Claude Desktop, edit the Claude configuration file:

On macOS:
```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "pbixray": {
      "command": "python",
      "args": ["/path/to/pbixray_server.py"]
    }
  }
}
```

On Windows:
```json
// %APPDATA%\Claude\claude_desktop_config.json
{
  "mcpServers": {
    "pbixray": {
      "command": "python",
      "args": ["C:\\path\\to\\pbixray_server.py"]
    }
  }
}
```

### Example interactions

With the server running in Claude, you can ask questions like:

- "Can you help me load and analyze my Power BI file at /path/to/report.pbix?"
- "What tables are in my Power BI model?"
- "Show me all the DAX measures in my model."
- "What relationships exist between tables in my Power BI file?"
- "How large is my Power BI model?"
- "What Power Query transformations are used in this model?"

Claude will use the appropriate tools to retrieve and present the information.

## Development

To test the server during development, use the MCP Inspector:

```bash
mcp dev pbixray_server.py
```

This starts an interactive session where you can call tools and test responses.