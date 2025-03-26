# Testing the PBIXRay MCP Server

This document provides guidance on how to test the PBIXRay MCP Server using the MCP Inspector and other testing methods.

## Using MCP Inspector

The MCP Inspector is a powerful tool for testing and debugging MCP servers. It provides a web-based interface to interact with your server, call tools, view responses, and debug issues.

### Prerequisites

- Node.js and npm installed on your system
- The MCP Inspector package (installed automatically through npx)
- A sample PBIX file for testing (available in the `demo/` directory)

### Starting the Inspector

To test your PBIXRay server with the MCP Inspector:

```bash
# Navigate to your project directory
cd path/to/pbixray-mcp

# Run the server with MCP Inspector
npx -y @modelcontextprotocol/inspector python src/pbixray_server.py
```

This command will:
1. Download and run the MCP Inspector if it's not already installed
2. Start your PBIXRay server 
3. Open a web interface at http://localhost:5173

### Using the Inspector Interface

Once the Inspector is running, you'll see a web interface with several sections:

1. **Connection Information**: Shows the server name, version, and connection status
2. **Tools**: Lists all tools exposed by your server
3. **Request/Response Panel**: Shows tool calls and their responses

#### Testing Tools

To test a tool in the PBIXRay server:

1. In the tools section, find the tool you want to test (e.g., `load_pbix_file`)
2. Click on the tool to view its parameters
3. Fill in the required parameters
   - For `load_pbix_file`, enter the path to a sample PBIX file (e.g., `demo/AdventureWorks Sales.pbix`)
4. Click "Execute" to call the tool
5. View the response in the response panel

#### Testing Workflow

A typical testing workflow might look like:

1. Call `load_pbix_file` to load a PBIX file for analysis
2. Call `get_model_summary` to see a high-level overview of the model
3. Call `get_tables` to list all tables in the model
4. Call `get_dax_measures` to view all DAX measures
5. Call `get_table_contents` with a specific table name to view its data

### Troubleshooting Inspector Issues

Common issues and their solutions:

1. **Connection Errors**
   - Make sure your PBIXRay server doesn't have syntax errors
   - Check if the path to your server script is correct
   - Ensure all dependencies are installed

2. **Path Issues with PBIX Files**
   - Use absolute paths for PBIX files
   - Verify the file exists at the specified location
   - Make sure file permissions allow reading the file

3. **Inspector Won't Start**
   - Check Node.js and npm versions (Node.js 14+ recommended)
   - Try clearing npm cache: `npm cache clean --force`
   - Check for port conflicts on 5173 or 3000

### Stopping the Inspector

To stop the Inspector:
- Press `Ctrl+C` in the terminal where it's running
- Close the browser window

## Automated Testing

The project includes automated tests in the `tests/` directory. To run them:

```bash
# Run the test with a sample file
python tests/test_with_sample.py
```

This will connect to the server, load a sample PBIX file, and test various tools automatically.

## Interactive Demo

For a more guided testing experience, try the interactive demo:

```bash
python examples/demo.py
```

This will connect to the server and provide a menu-driven interface to test various features.

## Testing with Claude for Desktop

Once your server is working correctly with the MCP Inspector, you can configure it to work with Claude for Desktop:

1. Edit your Claude for Desktop configuration file:
   - On macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - On Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add your server configuration:
   ```json
   {
     "mcpServers": {
       "pbixray": {
         "command": "python",
         "args": ["/path/to/src/pbixray_server.py"]
       }
     }
   }
   ```

3. Restart Claude for Desktop and look for the tools icon to verify connection.

## Logging and Debugging

For more detailed logging during testing:

```bash
# Enable verbose logging
PYTHONVERBOSE=1 python src/pbixray_server.py
```

This will show more detailed logs about tool calls, errors, and server operations.

## Common Testing Issues

1. **Missing Libraries**
   - Ensure `pbixray`, `numpy`, and `mcp` packages are installed
   - Install: `pip install -r requirements.txt`

2. **File Path Issues**
   - Always use absolute paths when testing with PBIX files
   - Check file permissions if you get access denied errors

3. **Data Format Issues**
   - If you see JSON serialization errors, check the `NumpyEncoder` in the server code
   - Large datasets may need limiting with pagination or sampling

## Next Steps

After successful testing, you may want to:

1. Integrate with your preferred MCP client
2. Add additional tools or features to the server
3. Contribute improvements to the project (see CONTRIBUTING.md)

For feature requests or bug reports discovered during testing, please open an issue on the project repository.