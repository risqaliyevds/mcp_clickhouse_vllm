#!/usr/bin/env python3
"""
ClickHouse MCP Server
Provides schema information for specific tables via MCP protocol
"""

import asyncio
import os
import sys
import json
from typing import List, Dict, Any
import clickhouse_connect
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# ClickHouse connection configuration
CLICKHOUSE_CONFIG = {
    'host': os.getenv('CLICKHOUSE_HOST', 'localhost'),
    'port': int(os.getenv('CLICKHOUSE_PORT', 8123)),
    'username': os.getenv('CLICKHOUSE_USER', 'default'),
    'password': os.getenv('CLICKHOUSE_PASSWORD', 'password'),
    'database': os.getenv('CLICKHOUSE_DATABASE', 'testdb')
}

# Specify which tables are accessible
ALLOWED_TABLES = [
    'users',
    'orders',
    'products',
    'inventory',
    'analytics_events'
]

app = Server("clickhouse-schema-server")

def get_clickhouse_client():
    """Create ClickHouse client connection"""
    return clickhouse_connect.get_client(
        host=CLICKHOUSE_CONFIG['host'],
        port=CLICKHOUSE_CONFIG['port'],
        username=CLICKHOUSE_CONFIG['username'],
        password=CLICKHOUSE_CONFIG['password'],
        database=CLICKHOUSE_CONFIG['database']
    )

def format_table_as_ascii(headers: List[str], rows: List[List[Any]]) -> str:
    """Format data as ASCII table"""
    if not headers and not rows:
        return "No data available"

    # Calculate column widths
    col_widths = []
    for i, header in enumerate(headers):
        max_width = len(str(header))
        for row in rows:
            if i < len(row):
                max_width = max(max_width, len(str(row[i])))
        col_widths.append(min(max_width, 50))  # Cap at 50 chars

    # Create separator line
    separator = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"

    # Format header
    header_line = "|"
    for i, header in enumerate(headers):
        header_str = str(header)[:col_widths[i]]
        header_line += f" {header_str:<{col_widths[i]}} |"

    # Build table
    table = [separator, header_line, separator]

    # Format rows
    for row in rows:
        row_line = "|"
        for i in range(len(headers)):
            if i < len(row):
                cell = str(row[i])[:col_widths[i]]
            else:
                cell = ""
            row_line += f" {cell:<{col_widths[i]}} |"
        table.append(row_line)

    table.append(separator)
    return "\n".join(table)

def get_table_schema(client, table_name: str) -> Dict[str, Any]:
    """Get detailed schema information for a specific table"""
    try:
        # Get column information
        columns_query = """
        SELECT
            name,
            type,
            default_kind,
            default_expression,
            comment
        FROM system.columns
        WHERE database = %(database)s AND table = %(table)s
        ORDER BY position
        """

        columns = client.query(
            columns_query,
            parameters={
                'database': CLICKHOUSE_CONFIG['database'],
                'table': table_name
            }
        ).result_rows

        # Get table metadata
        table_info_query = """
        SELECT
            engine,
            total_rows,
            formatReadableSize(total_bytes) as size
        FROM system.tables
        WHERE database = %(database)s AND name = %(table)s
        """

        table_info = client.query(
            table_info_query,
            parameters={
                'database': CLICKHOUSE_CONFIG['database'],
                'table': table_name
            }
        ).result_rows

        return {
            'table_name': table_name,
            'database': CLICKHOUSE_CONFIG['database'],
            'columns': columns,
            'engine': table_info[0][0] if table_info else 'Unknown',
            'total_rows': table_info[0][1] if table_info else 0,
            'total_size': table_info[0][2] if table_info else '0B'
        }

    except Exception as e:
        raise Exception(f"Error getting schema for table {table_name}: {str(e)}")

def format_schema_response(schema_info: Dict[str, Any]) -> str:
    """Format schema information as a nice ASCII table"""
    response = f"""
╔════════════════════════════════════════════════════════════╗
║ TABLE: {schema_info['table_name']:<52} ║
║ Database: {schema_info['database']:<49} ║
║ Engine: {schema_info['engine']:<51} ║
║ Total Rows: {str(schema_info['total_rows']):<47} ║
║ Total Size: {schema_info['total_size']:<47} ║
╚════════════════════════════════════════════════════════════╝

SCHEMA STRUCTURE:
"""

    # Format columns as table
    headers = ['Column Name', 'Type', 'Default', 'Comment']
    rows = []
    for col in schema_info['columns']:
        default = col[3] if col[2] else 'None'
        comment = col[4] if col[4] else ''
        rows.append([col[0], col[1], default[:30], comment[:30]])

    response += format_table_as_ascii(headers, rows)
    return response

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_table_schema",
            description=f"Get schema structure for a ClickHouse table. Available: {', '.join(ALLOWED_TABLES)}",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": f"Table name (one of: {', '.join(ALLOWED_TABLES)})",
                        "enum": ALLOWED_TABLES
                    }
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="list_tables",
            description="List all available tables with their sizes",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_sample_data",
            description="Get sample rows from a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "enum": ALLOWED_TABLES
                    },
                    "limit": {
                        "type": "integer",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["table_name"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        client = get_clickhouse_client()

        if name == "get_table_schema":
            table_name = arguments.get("table_name")

            if table_name not in ALLOWED_TABLES:
                return [TextContent(
                    type="text",
                    text=f"❌ Table '{table_name}' is not accessible. Available: {', '.join(ALLOWED_TABLES)}"
                )]

            schema_info = get_table_schema(client, table_name)
            response_text = format_schema_response(schema_info)

            return [TextContent(type="text", text=response_text)]

        elif name == "list_tables":
            # Get info for all allowed tables
            headers = ['Table Name', 'Engine', 'Rows', 'Size']
            rows = []

            for table in ALLOWED_TABLES:
                try:
                    query = """
                    SELECT
                        engine,
                        total_rows,
                        formatReadableSize(total_bytes) as size
                    FROM system.tables
                    WHERE database = %(database)s AND name = %(table)s
                    """
                    result = client.query(
                        query,
                        parameters={
                            'database': CLICKHOUSE_CONFIG['database'],
                            'table': table
                        }
                    ).result_rows

                    if result:
                        rows.append([table, result[0][0], str(result[0][1]), result[0][2]])
                    else:
                        rows.append([table, 'Not Found', '0', '0B'])
                except:
                    rows.append([table, 'Error', '-', '-'])

            table_text = "📊 Available ClickHouse Tables:\n\n"
            table_text += format_table_as_ascii(headers, rows)

            return [TextContent(type="text", text=table_text)]

        elif name == "get_sample_data":
            table_name = arguments.get("table_name")
            limit = min(arguments.get("limit", 5), 10)

            if table_name not in ALLOWED_TABLES:
                return [TextContent(
                    type="text",
                    text=f"❌ Table '{table_name}' is not accessible"
                )]

            # Get columns first
            columns_query = "SELECT name FROM system.columns WHERE database = %(database)s AND table = %(table)s ORDER BY position LIMIT 10"
            columns = client.query(
                columns_query,
                parameters={
                    'database': CLICKHOUSE_CONFIG['database'],
                    'table': table_name
                }
            ).result_rows

            column_names = [col[0] for col in columns]

            # Get sample data
            sample_query = f"SELECT * FROM {table_name} LIMIT {limit}"
            result = client.query(sample_query)

            response_text = f"📋 Sample Data from '{table_name}' (first {limit} rows):\n\n"
            response_text += format_table_as_ascii(column_names, result.result_rows)

            return [TextContent(type="text", text=response_text)]

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Error: {str(e)}"
        )]
    finally:
        try:
            client.close()
        except:
            pass

async def main():
    print("🚀 Starting ClickHouse MCP Server...")
    print(f"📊 Database: {CLICKHOUSE_CONFIG['database']}")
    print(f"📋 Available tables: {', '.join(ALLOWED_TABLES)}")

    # Test connection
    try:
        client = get_clickhouse_client()
        client.query("SELECT 1")
        client.close()
        print("✅ ClickHouse connection successful")
    except Exception as e:
        print(f"❌ ClickHouse connection failed: {e}")
        sys.exit(1)

    # Run the MCP server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())