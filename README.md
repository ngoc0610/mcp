# Setting Up PBIXRay with Claude

## Configure Claude Desktop

1. Clone the repository:
   ```bash
   git clone https://github.com/Hugoberry/pbixray-mcp.git
   ```

2. In Claude Desktop settings, add this configuration:
   ```json
   ...
     "pbixray": {
       "command": "wsl.exe",
       "args": [
         "bash",
         "-c",
         "/path/to/pbixray-mcp/run_server.sh"
       ]
   
   ```
   Replace `/path/to/pbixray-mcp` with your actual WSL path

3. When using file paths with WSL:
   - Windows: `C:\Users\name\file.pbix`
   - WSL: `/mnt/c/Users/name/file.pbix`

## Configure Claude Web

1. Clone the repository and start server:
   ```bash
   git clone https://github.com/Hugoberry/pbixray-mcp.git
   cd pbixray-mcp
   python src/pbixray_server.py
   ```

2. In Claude settings → Integrations → Add tool:
   - Name: `PBIXRay`
   - URL: `http://localhost:8000`

## Example Queries
- "Load the Power BI file at /path/to/sales.pbix"
- "List all tables in my model"
- "Show me the DAX measures in the Sales table"
- "What relationships exist between tables?"

## Credits
* Hugoberry https://github.com/Hugoberry/pbixray
* rusiaaman https://github.com/rusiaaman/wcgw
* Based on PBIXRay MCP Server
