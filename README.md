# PBIXRay MCP Server

A [Model Context Protocol][mcp] (MCP) server for PBIXRay.

This MCP server exposes the capabilities of [PBIXRay](https://github.com/Hugoberry/pbixray) as tools and resources for LLM clients to interact with Power BI (.pbix) files.

## Features

- [x] Loading and analyzing PBIX files
- [x] Data model exploration
  - [x] Listing tables in the model
  - [x] Retrieving model metadata
  - [x] Checking model size
  - [x] Getting model statistics
  - [x] Getting comprehensive model summary
- [x] Query language access
  - [x] Viewing Power Query (M) code
  - [x] Accessing M Parameters
  - [x] Exploring DAX calculated tables
  - [x] Viewing DAX measures
  - [x] Examining DAX calculated columns
- [x] Data structure analysis
  - [x] Retrieving schema information
  - [x] Analyzing table relationships
  - [x] Accessing table contents with pagination

The list of tools is configurable, so you can choose which tools you want to make available to the MCP client.
This is useful if you don't use certain functionality or if you don't want to expose sensitive information.

## Tools

| Tool                  | Category  | Description                                                        |
|-----------------------|-----------|--------------------------------------------------------------------|
| `load_pbix_file`      | Core      | Load a Power BI (.pbix) file for analysis                          |
| `get_tables`          | Model     | List all tables in the model                                       |
| `get_metadata`        | Model     | Get metadata about the Power BI configuration                      |
| `get_power_query`     | Query     | Display all M/Power Query code used for data transformation        |
| `get_m_parameters`    | Query     | Display all M Parameters values                                    |
| `get_model_size`      | Model     | Get the model size in bytes                                        |
| `get_dax_tables`      | Query     | View DAX calculated tables                                         |
| `get_dax_measures`    | Query     | Access DAX measures with filtering by table or measure name        |
| `get_dax_columns`     | Query     | Access calculated column DAX expressions with filtering options    |
| `get_schema`          | Structure | Get details about the data model schema and column types           |
| `get_relationships`   | Structure | Get the details about the data model relationships                 |
| `get_table_contents`  | Data      | Retrieve the contents of a specified table with pagination         |
| `get_statistics`      | Model     | Get statistics about the model with optional filtering             |
| `get_model_summary`   | Model     | Get a comprehensive summary of the current Power BI model          |

## Usage

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install mcp pbixray numpy
   ```

2. Run the server:
   ```bash
   # Run the server directly
   python src/pbixray_server.py

   # With disabled tools for security
   python src/pbixray_server.py --disallow get_m_parameters get_power_query

   # Customize pagination and row limits 
   python src/pbixray_server.py --max-rows 500 --page-size 50
   ```

3. Add the server configuration to your client configuration file. For example, for Claude Desktop:

   ```json
   {
     "mcpServers": {
       "pbixray": {
         "command": "python",
         "args": ["path/to/pbixray-mcp/src/pbixray_server.py"],
         "env": {}
       }
     }
   }
   ```

For Windows users with WSL, see the [WSL Configuration](#using-with-windows-subsystem-for-linux-wsl) section below.

### Command Line Options

The server supports several command line options:

* `--disallow [tool_names]`: Disable specific tools for security reasons
* `--max-rows N`: Set maximum number of rows returned (default: 100)
* `--page-size N`: Set default page size for paginated results (default: 20)

### Query Options

Many tools support additional parameters for filtering and pagination:

#### Filtering by Name

Tools like `get_dax_measures`, `get_dax_columns`, `get_schema` and others support filtering by specific names:

```
# Get measures from a specific table
get_dax_measures(table_name="Sales")

# Get a specific measure
get_dax_measures(table_name="Sales", measure_name="Total Sales")
```

#### Pagination for Large Tables

The `get_table_contents` tool supports pagination to handle large tables efficiently:

```
# Get first page of Customer table (default 20 rows per page)
get_table_contents(table_name="Customer")

# Get second page with 50 rows per page
get_table_contents(table_name="Customer", page=2, page_size=50)
```

## Using with Windows Subsystem for Linux (WSL)

When using the PBIXRay MCP Server in WSL with Claude Desktop on Windows, you need to be aware of path differences when loading PBIX files.

When configuring Claude Desktop to use the server from WSL, use a launcher script:


 Configure Claude Desktop with:
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

### Path Conversion Guidelines

Windows paths (like `C:\Users\name\file.pbix`) cannot be directly accessed in WSL. Instead:

| Windows Path | WSL Path |
|--------------|----------|
| `C:\Users\Documents\file.pbix` | `/mnt/c/Users/Documents/file.pbix` |
| `D:\Data\PowerBI\file.pbix` | `/mnt/d/Data/PowerBI/file.pbix` |

## Development

Contributions are welcome! Please see the [ROADMAP.md](docs/ROADMAP.md) for planned improvements and areas where help is needed.

### Testing with Sample Files

The repository includes sample files and test scripts to help you get started:

```bash
# Test with sample AdventureWorks Sales.pbix file in demo/ folder
python tests/test_with_sample.py

# Try the interactive demo
python examples/demo.py

# For isolated tests of specific features
python test_pagination.py
python test_metadata_fix.py
```

The test scripts will help you understand how to interact with the server using the sample PBIX files provided in the `demo/` directory.

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
│   ├── conftest.py
│   ├── test_server.py
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

## Credits

* [Hugoberry](https://github.com/Hugoberry/pbixray) - Original PBIXRay library
* [rusiaaman](https://github.com/rusiaaman/wcgw) - WCGW framework
* This was fully written by Claude using wcgw

## License

[MIT License](LICENSE)

[mcp]: https://modelcontextprotocol.io/