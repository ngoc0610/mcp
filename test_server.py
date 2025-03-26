#!/usr/bin/env python3
"""
Test script to verify the PBIXRay MCP server is working properly
"""

import subprocess
import json
import sys
import os

def main():
    """Test the server by listing available tools"""
    server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pbixray_server.py")
    
    # Prepare the message for tool listing
    message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "0.1.0",
            "implementation": {
                "name": "test-client",
                "version": "1.0.0"
            },
            "capabilities": {}
        }
    }
    
    # Start the server process
    try:
        proc = subprocess.Popen(
            [sys.executable, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Send the initialization message
        print("Sending initialization message...")
        proc.stdin.write(json.dumps(message) + "\n")
        proc.stdin.flush()
        
        # Wait for the response
        response = proc.stdout.readline()
        print("\nServer response:")
        try:
            response_json = json.loads(response)
            print(json.dumps(response_json, indent=2))
            
            # Verify the response has expected fields
            if "result" in response_json and "protocolVersion" in response_json["result"]:
                print("\n✅ Server initialized successfully!")
                
                # Send tools list request
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list"
                }
                print("\nRequesting tool list...")
                proc.stdin.write(json.dumps(tools_request) + "\n")
                proc.stdin.flush()
                
                # Wait for the response
                tools_response = proc.stdout.readline()
                tools_json = json.loads(tools_response)
                print("\nAvailable tools:")
                print(json.dumps(tools_json, indent=2))
                
                if "result" in tools_json and "tools" in tools_json["result"]:
                    print(f"\n✅ Server has {len(tools_json['result']['tools'])} tools available")
                    
                    # Print the tool names
                    for tool in tools_json["result"]["tools"]:
                        print(f"- {tool['name']}: {tool.get('description', 'No description')}")
            else:
                print("❌ Server initialization failed")
        except json.JSONDecodeError:
            print("❌ Server response is not valid JSON")
            print(f"Raw response: {response}")
    except Exception as e:
        print(f"❌ Error running the server: {e}")
    finally:
        # Clean up
        proc.terminate()
        print("\nTest completed")

if __name__ == "__main__":
    main()
