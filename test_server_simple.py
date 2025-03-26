#!/usr/bin/env python3
"""
Simple test for the PBIXRay MCP server
"""

import os
import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters

async def main():
    """Test the PBIXRay MCP server"""
    server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pbixray_server.py")
    
    # Start the server process
    server_params = StdioServerParameters(
        command="python",
        args=[server_path],
        env=None
    )
    
    print("Connecting to PBIXRay server...")
    
    async with stdio_client(server_params) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            # Initialize the session
            await session.initialize()
            
            # List the available tools
            tools_response = await session.list_tools()
            print("\nAvailable tools:")
            for tool in tools_response.tools:
                print(f"- {tool.name}: {tool.description}")
            
            # Test basic connectivity only - no actual PBIX file needed
            print("\nTesting server response:")
            try:
                # Try to call a tool that doesn't require a file
                result = await session.call_tool("get_tables", {})
                print(f"\nResponse from get_tables (with no file loaded):")
                for content in result.content:
                    if hasattr(content, "text") and content.text:
                        print(content.text)
                
                print("\n✅ Server is responding correctly!")
            except Exception as e:
                print(f"\n❌ Error calling tool: {e}")

if __name__ == "__main__":
    asyncio.run(main())
