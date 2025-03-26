#!/usr/bin/env python3
"""
Unit tests for the PBIXRay MCP server
"""

import os
import pytest
import sys
import json
from unittest.mock import patch, MagicMock

# Add the src directory to the path so we can import the server module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Mock the parse_args function before importing the module
with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
    # Create a mock args object with the expected attributes
    mock_args = MagicMock()
    mock_args.disallow = []
    mock_args.max_rows = 100
    mock_args.page_size = 20
    mock_parse_args.return_value = mock_args
    
    # Now import the server module
    import pbixray_server

# Mock PBIXRay class to avoid needing actual PBIX files during tests
class MockPBIXRay:
    def __init__(self, file_path):
        self.file_path = file_path
        self.tables = ["Table1", "Table2"]
        self.metadata = {"version": "1.0"}
        self.size = 1024
        
    def get_table(self, table_name):
        # Return a mock pandas DataFrame
        import pandas as pd
        return pd.DataFrame({"Column1": [1, 2, 3], "Column2": ["A", "B", "C"]})

# Tests for the server functions
def test_load_pbix_file():
    """Test the load_pbix_file function"""
    # Create a mock Context
    mock_context = MagicMock()
    
    # Mock the PBIXRay class
    with patch('pbixray_server.PBIXRay', MockPBIXRay):
        with patch('os.path.exists', return_value=True):
            result = pbixray_server.load_pbix_file("/path/to/test.pbix", mock_context)
            assert "Successfully loaded" in result

def test_get_tables():
    """Test the get_tables function"""
    # Create a mock Context
    mock_context = MagicMock()
    
    # Set up the global state
    pbixray_server.current_model = MockPBIXRay("/path/to/test.pbix")
    
    result = pbixray_server.get_tables(mock_context)
    assert "Table1" in result
    assert "Table2" in result

def test_get_metadata():
    """Test the get_metadata function"""
    # Create a mock Context
    mock_context = MagicMock()
    
    # Set up the global state
    pbixray_server.current_model = MockPBIXRay("/path/to/test.pbix")
    
    result = pbixray_server.get_metadata(mock_context)
    assert "version" in result

def test_get_model_size():
    """Test the get_model_size function"""
    # Create a mock Context
    mock_context = MagicMock()
    
    # Set up the global state
    pbixray_server.current_model = MockPBIXRay("/path/to/test.pbix")
    
    result = pbixray_server.get_model_size(mock_context)
    assert "1024 bytes" in result
