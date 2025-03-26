#!/usr/bin/env python3
"""
PBIXRay MCP Server

This MCP server exposes the capabilities of PBIXRay as tools and resources
for LLM clients like Claude to interact with Power BI (.pbix) files.
"""

import os
import json
import numpy as np
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Context, Image
from pbixray import PBIXRay

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
def get_dax_measures(ctx: Context) -> str:
    """
    Access DAX measures in the model.
    
    Returns:
        A list of DAX measures with names, expressions, and other metadata
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        dax_measures = current_model.dax_measures
        return dax_measures.to_json(orient="records", indent=2)
    except Exception as e:
        ctx.info(f"Error retrieving DAX measures: {str(e)}")
        return f"Error retrieving DAX measures: {str(e)}"


@mcp.tool()
def get_dax_columns(ctx: Context) -> str:
    """
    Access calculated column DAX expressions.
    
    Returns:
        A list of calculated columns with names and expressions
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        dax_columns = current_model.dax_columns
        return dax_columns.to_json(orient="records", indent=2)
    except Exception as e:
        ctx.info(f"Error retrieving DAX columns: {str(e)}")
        return f"Error retrieving DAX columns: {str(e)}"


@mcp.tool()
def get_schema(ctx: Context) -> str:
    """
    Get details about the data model schema and column types.
    
    Returns:
        A description of the schema with table names, column names, and data types
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        schema = current_model.schema
        return schema.to_json(orient="records", indent=2)
    except Exception as e:
        ctx.info(f"Error retrieving schema: {str(e)}")
        return f"Error retrieving schema: {str(e)}"


@mcp.tool()
def get_relationships(ctx: Context) -> str:
    """
    Get the details about the data model relationships.
    
    Returns:
        A description of the relationships between tables in the model
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        relationships = current_model.relationships
        return relationships.to_json(orient="records", indent=2)
    except Exception as e:
        ctx.info(f"Error retrieving relationships: {str(e)}")
        return f"Error retrieving relationships: {str(e)}"


@mcp.tool()
def get_table_contents(table_name: str, ctx: Context) -> str:
    """
    Retrieve the contents of a specified table.
    
    Args:
        table_name: Name of the table to retrieve
    
    Returns:
        The table contents in JSON format
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        table_contents = current_model.get_table(table_name)
        # Limit the number of rows to prevent excessive output
        MAX_ROWS = 100
        if len(table_contents) > MAX_ROWS:
            ctx.info(f"Table has {len(table_contents)} rows. Returning first {MAX_ROWS} rows.")
            table_contents = table_contents.head(MAX_ROWS)
        
        return table_contents.to_json(orient="records", indent=2)
    except Exception as e:
        ctx.info(f"Error retrieving table contents: {str(e)}")
        return f"Error retrieving table contents: {str(e)}"


@mcp.tool()
def get_statistics(ctx: Context) -> str:
    """
    Get statistics about the model.
    
    Returns:
        Statistics about column cardinality and byte sizes
    """
    global current_model
    
    if current_model is None:
        return "Error: No Power BI file loaded. Please use load_pbix_file first."
    
    try:
        statistics = current_model.statistics
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


if __name__ == "__main__":
    # Run the server with stdio transport for MCP
    mcp.run(transport="stdio")
