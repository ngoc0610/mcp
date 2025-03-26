#!/usr/bin/env python3
"""
Test the PBIXRay MCP server with a sample PBIX file
"""

import os
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters

async def main():
    """Test the PBIXRay MCP server with a sample file"""
    server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pbixray_server.py")
    sample_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo", "AdventureWorks Sales.pbix")
    
    # Make sure the sample file exists
    if not os.path.exists(sample_file_path):
        print(f"Error: Sample file not found at {sample_file_path}")
        return
    
    # Start the server process
    server_params = StdioServerParameters(
        command="python",
        args=[server_path],
        env=None
    )
    
    print(f"Connecting to PBIXRay server and testing with file: {os.path.basename(sample_file_path)}")
    
    async with stdio_client(server_params) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            # Initialize the session
            await session.initialize()
            
            # Load the sample PBIX file
            print("\n1. Loading PBIX file...")
            load_result = await session.call_tool("load_pbix_file", {"file_path": sample_file_path})
            for content in load_result.content:
                if hasattr(content, "text") and content.text:
                    print(f"   Response: {content.text}")
            
            # Get model summary
            print("\n2. Getting model summary...")
            summary_result = await session.call_tool("get_model_summary", {})
            for content in summary_result.content:
                if hasattr(content, "text") and content.text:
                    try:
                        summary_data = json.loads(content.text)
                        print(f"   File: {summary_data.get('file_name', 'Unknown')}")
                        print(f"   Size: {summary_data.get('size_mb', 'Unknown')} MB")
                        print(f"   Tables: {summary_data.get('tables_count', 'Unknown')}")
                        print("   Table names:")
                        for table in summary_data.get('tables', []):
                            print(f"     - {table}")
                    except json.JSONDecodeError:
                        print(f"   Response: {content.text}")
            
            # Get tables
            print("\n3. Getting tables...")
            tables_result = await session.call_tool("get_tables", {})
            for content in tables_result.content:
                if hasattr(content, "text") and content.text:
                    try:
                        tables_data = json.loads(content.text)
                        print(f"   Found {len(tables_data)} tables.")
                    except json.JSONDecodeError:
                        print(f"   Response: {content.text}")
            
            # Get measures
            print("\n4. Getting DAX measures...")
            measures_result = await session.call_tool("get_dax_measures", {})
            for content in measures_result.content:
                if hasattr(content, "text") and content.text:
                    try:
                        measures_data = json.loads(content.text)
                        print(f"   Found {len(measures_data)} DAX measures.")
                        if len(measures_data) > 0:
                            print("   Sample measures:")
                            for measure in measures_data[:3]:  # Show first 3 measures
                                print(f"     - {measure.get('Name', 'Unknown')}: {measure.get('TableName', 'Unknown')}")
                    except json.JSONDecodeError:
                        print(f"   Response: {content.text}")
            
            # Get relationships
            print("\n5. Getting relationships...")
            relations_result = await session.call_tool("get_relationships", {})
            for content in relations_result.content:
                if hasattr(content, "text") and content.text:
                    try:
                        relations_data = json.loads(content.text)
                        print(f"   Found {len(relations_data)} relationships.")
                        if len(relations_data) > 0:
                            print("   Sample relationships:")
                            for relation in relations_data[:3]:  # Show first 3 relationships
                                print(f"     - {relation.get('FromTableName', 'Unknown')}" +
                                      f" → {relation.get('ToTableName', 'Unknown')}")
                    except json.JSONDecodeError:
                        print(f"   Response: {content.text}")
            
            print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
