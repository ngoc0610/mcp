#!/usr/bin/env python3
"""
PBIXRay MCP Server

This MCP server exposes the capabilities of PBIXRay as tools and resources
for LLM clients to interact with Power BI (.pbix) files.
"""

import os
import json
import numpy as np
import argparse
import functools
import sys
from typing import Optional, Dict, Any, List, Union, Callable
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Context, Image
from pbixray import PBIXRay

# Parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description='PBIXRay MCP Server')
    parser.add_argument('--disallow', nargs='+', help='Specify tools to disable', default=[])
    parser.add_argument('--max-rows', type=int, default=10, help='Maximum rows to return for table data (default: 10)')
    parser.add_argument('--page-size', type=int, default=10, help='Default page size for paginated results (default: 10)')
    return parser.parse_args()

# Get command line arguments
args = parse_args()
disallowed_tools = args.disallow
MAX_ROWS = args.max_rows
PAGE_SIZE = args.page_size

# Custom JSON encoder to handle NumPy arrays and other non-serializable types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)

# Initialize the MCP server
mcp = FastMCP("PBIXRay")

# Store the original tool decorator
original_tool_decorator = mcp.tool

# Create a secure wrapper for tool registration
def secure_tool(*args, **kwargs):
    """
    Decorator that wraps the original FastMCP tool decorator to check if a tool
    is allowed to run before executing it.
    """
    # Get the original decorator
    original_decorator = original_tool_decorator(*args, **kwargs)
    
    # Create a new decorator that wraps the original
    def new_decorator(func):
        # Get the tool name from the function name
        tool_name = func.__name__
        
        # Check if this tool is disallowed
        if tool_name in disallowed_tools:
            # Create a replacement function that returns an error message
            @functools.wraps(func)
            def disabled_tool(*f_args, **f_kwargs):
                return f"Error: The tool '{tool_name}' has been disabled by the server administrator."
            
            # Register the disabled tool with the original decorator
            return original_decorator(disabled_tool)
        else:
            # If the tool is allowed, just use the original decorator
            return original_decorator(func)
    
    return new_decorator

# Replace the original tool decorator with our secure version
mcp.tool = secure_tool

# Global variable to store the currently loaded model
current_model: Optional[PBIXRay] = None
current_model_path: Optional[str] = None


@mcp.tool()
def load_pbix_file(file_path: str, ctx: Context) -> str:
    """
    Load a Power BI (.pbix) file for analysis.
    
    Args:
        file_path: Path to the .pbix file to load
    
    Returns:
        A message confirming the file was loaded
    """
    global current_model, current_model_path
    
    file_path = os.path.expanduser(file_path)
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' not found."
    
    if not file_path.lower().endswith('.pbix'):
        return f"Error: File '{file_path}' is not a .pbix file."
    
    try:
        ctx.info(f"Loading PBIX file: {file_path}")
        current_model = PBIXRay(file_path)
        current_model_path = file_path
        return f"Successfully loaded '{os.path.basename(file_path)}'"
    except Exception as e:
        ctx.info(f"Error loading PBIX file: {str(e)}")
        return f"Error loading file: {str(e)}"


@mcp.tool()
def get_tables(ctx: Context) -> str:
    """
    List all tables in the model.
    
    Returns:
        A list of tables in the model
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        tables = current_model.tables
        if isinstance(tables, (list, np.ndarray)):
            return json.dumps(tables.tolist() if isinstance(tables, np.ndarray) else tables, indent=2)
        else:
            return str(tables)
    except Exception as e:
        ctx.info(f"Error retrieving tables: {str(e)}")
        return f"Error retrieving tables: {str(e)}"


@mcp.tool()
def get_metadata(ctx: Context) -> str:
    """
    Get metadata about the Power BI configuration used during model creation.
    
    Returns:
        The metadata as a formatted string
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        metadata = current_model.metadata
        return json.dumps(metadata, indent=2, cls=NumpyEncoder)
    except Exception as e:
        ctx.info(f"Error retrieving metadata: {str(e)}")
        return f"Error retrieving metadata: {str(e)}"


@mcp.tool()
def get_power_query(ctx: Context) -> str:
    """
    Display all M/Power Query code used for data transformation.
    
    Returns:
        A list of all Power Query expressions with their table names
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        # Power query returns a DataFrame with TableName and Expression columns
        power_query = current_model.power_query
        # Convert DataFrame to dict for JSON serialization
        return power_query.to_json(orient="records", indent=2)
    except Exception as e:
        ctx.info(f"Error retrieving Power Query: {str(e)}")
        return f"Error retrieving Power Query: {str(e)}"


@mcp.tool()
def get_m_parameters(ctx: Context) -> str:
    """
    Display all M Parameters values.
    
    Returns:
        A list of parameter info with names, descriptions, and expressions
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        m_parameters = current_model.m_parameters
        return m_parameters.to_json(orient="records", indent=2)
    except Exception as e:
        ctx.info(f"Error retrieving M Parameters: {str(e)}")
        return f"Error retrieving M Parameters: {str(e)}"


@mcp.tool()
def get_model_size(ctx: Context) -> str:
    """
    Get the model size in bytes.
    
    Returns:
        The size of the model in bytes
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        size = current_model.size
        return f"Model size: {size} bytes ({size / (1024 * 1024):.2f} MB)"
    except Exception as e:
        ctx.info(f"Error retrieving model size: {str(e)}")
        return f"Error retrieving model size: {str(e)}"


@mcp.tool()
def get_dax_tables(ctx: Context) -> str:
    """
    View DAX calculated tables.
    
    Returns:
        A list of DAX calculated tables with names and expressions
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        dax_tables = current_model.dax_tables
        return dax_tables.to_json(orient="records", indent=2)
    except Exception as e:
        ctx.info(f"Error retrieving DAX tables: {str(e)}")
        return f"Error retrieving DAX tables: {str(e)}"


@mcp.tool()
def get_dax_measures(ctx: Context, table_name: str = None, measure_name: str = None) -> str:
    """
    Access DAX measures in the model with optional filtering.
    
    Args:
        table_name: Optional filter for measures from a specific table
        measure_name: Optional filter for a specific measure by name
    
    Returns:
        A list of DAX measures with names, expressions, and other metadata
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        # Get all measures
        dax_measures = current_model.dax_measures
        
        # Apply table filter if specified
        if table_name:
            dax_measures = dax_measures[dax_measures['TableName'] == table_name]
            
        # Apply measure name filter if specified
        if measure_name:
            dax_measures = dax_measures[dax_measures['Name'] == measure_name]
            
        # Return message if no measures match the filters
        if len(dax_measures) == 0:
            filters = []
            if table_name:
                filters.append(f"table '{table_name}'")
            if measure_name:
                filters.append(f"name '{measure_name}'")
            filter_text = " and ".join(filters)
            return f"No measures found with {filter_text}."
        
        return dax_measures.to_json(orient="records", indent=2)
    except Exception as e:
        ctx.info(f"Error retrieving DAX measures: {str(e)}")
        return f"Error retrieving DAX measures: {str(e)}"


@mcp.tool()
def get_dax_columns(ctx: Context, table_name: str = None, column_name: str = None) -> str:
    """
    Access calculated column DAX expressions with optional filtering.
    
    Args:
        table_name: Optional filter for columns from a specific table
        column_name: Optional filter for a specific column by name
    
    Returns:
        A list of calculated columns with names and expressions
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        # Get all calculated columns
        dax_columns = current_model.dax_columns
        
        # Apply table filter if specified
        if table_name:
            dax_columns = dax_columns[dax_columns['TableName'] == table_name]
            
        # Apply column name filter if specified
        if column_name:
            dax_columns = dax_columns[dax_columns['ColumnName'] == column_name]
            
        # Return message if no columns match the filters
        if len(dax_columns) == 0:
            filters = []
            if table_name:
                filters.append(f"table '{table_name}'")
            if column_name:
                filters.append(f"name '{column_name}'")
            filter_text = " and ".join(filters)
            return f"No calculated columns found with {filter_text}."
        
        return dax_columns.to_json(orient="records", indent=2)
    except Exception as e:
        ctx.info(f"Error retrieving DAX columns: {str(e)}")
        return f"Error retrieving DAX columns: {str(e)}"


@mcp.tool()
def get_schema(ctx: Context, table_name: str = None, column_name: str = None) -> str:
    """
    Get details about the data model schema and column types with optional filtering.
    
    Args:
        table_name: Optional filter for columns from a specific table
        column_name: Optional filter for a specific column by name
    
    Returns:
        A description of the schema with table names, column names, and data types
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        # Get the complete schema
        schema = current_model.schema
        
        # Apply table filter if specified
        if table_name:
            schema = schema[schema['TableName'] == table_name]
            
        # Apply column filter if specified
        if column_name:
            schema = schema[schema['ColumnName'] == column_name]
            
        # Return message if no columns match the filters
        if len(schema) == 0:
            filters = []
            if table_name:
                filters.append(f"table '{table_name}'")
            if column_name:
                filters.append(f"column '{column_name}'")
            filter_text = " and ".join(filters)
            return f"No schema entries found with {filter_text}."
        
        return schema.to_json(orient="records", indent=2)
    except Exception as e:
        ctx.info(f"Error retrieving schema: {str(e)}")
        return f"Error retrieving schema: {str(e)}"


@mcp.tool()
def get_relationships(ctx: Context, from_table: str = None, to_table: str = None) -> str:
    """
    Get the details about the data model relationships with optional filtering.
    
    Args:
        from_table: Optional filter for relationships from a specific table
        to_table: Optional filter for relationships to a specific table
    
    Returns:
        A description of the relationships between tables in the model
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        # Get all relationships
        relationships = current_model.relationships
        
        # Apply from_table filter if specified
        if from_table:
            relationships = relationships[relationships['FromTableName'] == from_table]
            
        # Apply to_table filter if specified
        if to_table:
            relationships = relationships[relationships['ToTableName'] == to_table]
            
        # Return message if no relationships match the filters
        if len(relationships) == 0:
            filters = []
            if from_table:
                filters.append(f"from table '{from_table}'")
            if to_table:
                filters.append(f"to table '{to_table}'")
            filter_text = " and ".join(filters)
            return f"No relationships found {filter_text}."
        
        return relationships.to_json(orient="records", indent=2)
    except Exception as e:
        ctx.info(f"Error retrieving relationships: {str(e)}")
        return f"Error retrieving relationships: {str(e)}"


@mcp.tool()
def get_table_contents(ctx: Context, table_name: str, page: int = 1, page_size: int = None) -> str:
    """
    Retrieve the contents of a specified table with pagination.
    
    Args:
        table_name: Name of the table to retrieve
        page: Page number to retrieve (starting from 1)
        page_size: Number of rows per page (defaults to value from --page-size)
    
    Returns:
        The table contents in JSON format with pagination metadata
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        import time
        start_time = time.time()
        
        # Use command-line page size if not specified
        if page_size is None:
            page_size = PAGE_SIZE
            
        # Validate pagination parameters
        if page < 1:
            return "Error: Page number must be 1 or greater."
        if page_size < 1:
            return "Error: Page size must be 1 or greater."
        
        # Log for large tables
        ctx.info(f"Retrieving page {page} from table '{table_name}'...")
            
        table_contents = current_model.get_table(table_name)
        total_rows = len(table_contents)
        total_pages = (total_rows + page_size - 1) // page_size
        
        if total_rows > 10000:
            ctx.info(f"Large table detected: '{table_name}' has {total_rows} rows")
        
        # Calculate indices for requested page
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_rows)
        
        # Check if requested page exists
        if start_idx >= total_rows:
            return f"Error: Page {page} does not exist. The table has {total_pages} page(s)."
        
        # Get the requested page of data
        page_data = table_contents.iloc[start_idx:end_idx]
        
        # Create response with pagination metadata
        response = {
            "pagination": {
                "total_rows": total_rows,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
                "showing_rows": len(page_data)
            },
            "data": json.loads(page_data.to_json(orient="records"))
        }
        
        elapsed_time = time.time() - start_time
        if elapsed_time > 1.0:  # Only log if it took more than a second
            ctx.info(f"Retrieved data from '{table_name}' ({total_rows} rows) in {elapsed_time:.2f} seconds")
        
        return json.dumps(response, indent=2)
    except Exception as e:
        ctx.info(f"Error retrieving table contents: {str(e)}")
        return f"Error retrieving table contents: {str(e)}"


@mcp.tool()
def get_statistics(ctx: Context, table_name: str = None, column_name: str = None) -> str:
    """
    Get statistics about the model with optional filtering.
    
    Args:
        table_name: Optional filter for statistics from a specific table
        column_name: Optional filter for statistics of a specific column
    
    Returns:
        Statistics about column cardinality and byte sizes
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        # Get all statistics
        statistics = current_model.statistics
        
        # Apply table filter if specified
        if table_name:
            statistics = statistics[statistics['TableName'] == table_name]
            
        # Apply column filter if specified
        if column_name:
            statistics = statistics[statistics['ColumnName'] == column_name]
            
        # Return message if no statistics match the filters
        if len(statistics) == 0:
            filters = []
            if table_name:
                filters.append(f"table '{table_name}'")
            if column_name:
                filters.append(f"column '{column_name}'")
            filter_text = " and ".join(filters)
            return f"No statistics found with {filter_text}."
        
        return statistics.to_json(orient="records", indent=2)
    except Exception as e:
        ctx.info(f"Error retrieving statistics: {str(e)}")
        return f"Error retrieving statistics: {str(e)}"


@mcp.tool()
def get_model_summary(ctx: Context) -> str:
    """
    Get a comprehensive summary of the current Power BI model.
    
    Returns:
        A summary of the model with key metrics and information
    """
    global current_model, current_model_path
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        # Collect information from various methods
        summary = {
            "file_path": current_model_path,
            "file_name": os.path.basename(current_model_path),
            "size_bytes": current_model.size,
            "size_mb": round(current_model.size / (1024 * 1024), 2),
            "tables_count": len(current_model.tables),
            "tables": current_model.tables.tolist() if isinstance(current_model.tables, np.ndarray) else current_model.tables,
            "measures_count": len(current_model.dax_measures) if hasattr(current_model.dax_measures, "__len__") else "Unknown",
            "relationships_count": len(current_model.relationships) if hasattr(current_model.relationships, "__len__") else "Unknown",
        }
        
        return json.dumps(summary, indent=2, cls=NumpyEncoder)
    except Exception as e:
        ctx.info(f"Error creating model summary: {str(e)}")
        return f"Error creating model summary: {str(e)}"


def main():
    """
    Run the PBIXRay MCP server.
    
    This function is the entry point for the package and
    can be called from command line after installation.
    """
    # Use stderr for logging messages to avoid interfering with JSON-RPC over stdout
    print("Starting PBIXRay MCP Server...", file=sys.stderr)
    
    if disallowed_tools:
        print(f"Security: Disallowed tools: {', '.join(disallowed_tools)}", file=sys.stderr)
    
    mcp.run(transport="stdio")

if __name__ == "__main__":
    # Run the server with stdio transport for MCP
    main()
