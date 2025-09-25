#!/usr/bin/env python3
"""
Web Application for ClickHouse MCP Demo
Provides a web interface to interact with the MCP server and vLLM
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import asyncio
import json
import requests
import subprocess
import os
from typing import Dict, Any, List
import clickhouse_connect

app = Flask(__name__)
CORS(app)

# Configuration
VLLM_URL = os.getenv('VLLM_URL', 'http://localhost:8000')
MCP_SERVER_PATH = '/app/mcp_server.py'

# ClickHouse configuration
CLICKHOUSE_CONFIG = {
    'host': os.getenv('CLICKHOUSE_HOST', 'localhost'),
    'port': int(os.getenv('CLICKHOUSE_PORT', 8123)),
    'username': os.getenv('CLICKHOUSE_USER', 'default'),
    'password': os.getenv('CLICKHOUSE_PASSWORD', ''),
    'database': os.getenv('CLICKHOUSE_DATABASE', 'default')
}

def get_clickhouse_client():
    """Create ClickHouse client connection"""
    try:
        return clickhouse_connect.get_client(
            host=CLICKHOUSE_CONFIG['host'],
            port=CLICKHOUSE_CONFIG['port'],
            username=CLICKHOUSE_CONFIG['username'],
            password=CLICKHOUSE_CONFIG['password'],
            database=CLICKHOUSE_CONFIG['database']
        )
    except Exception as e:
        print(f"ClickHouse connection failed: {e}")
        return None

def get_mock_data(tool_name: str, arguments: dict) -> str:
    """Get mock data for demonstration when ClickHouse is not available"""
    ALLOWED_TABLES = ['users', 'orders', 'products', 'inventory', 'analytics_events']

    if tool_name == "list_tables_with_columns":
        result = """DATABASE TABLES AND COLUMNS:

📋 USERS TABLE:
• user_id (UInt32) - Primary key
• username (String) - User login name
• email (String) - Email address
• first_name (String) - First name
• last_name (String) - Last name
• created_at (DateTime) - Account creation date
• is_active (UInt8) - Active status (0/1)
• account_type (Enum8) - Account type: free, premium, enterprise

📋 ORDERS TABLE:
• order_id (UInt32) - Primary key
• user_id (UInt32) - Foreign key to users
• product_id (UInt32) - Foreign key to products
• quantity (UInt16) - Order quantity
• total_amount (Decimal(10,2)) - Total order amount
• order_date (DateTime) - Order timestamp
• status (Enum8) - Order status: pending, processing, shipped, delivered, cancelled
• shipping_address (String) - Delivery address

📋 PRODUCTS TABLE:
• product_id (UInt32) - Primary key
• product_name (String) - Product name
• category (String) - Product category
• price (Decimal(10,2)) - Product price
• stock_quantity (UInt32) - Available stock
• manufacturer (String) - Manufacturer name
• created_at (DateTime) - Product creation date
• is_available (UInt8) - Availability status (0/1)

📋 INVENTORY TABLE:
• inventory_id (UInt32) - Primary key
• product_id (UInt32) - Foreign key to products
• warehouse_id (UInt16) - Warehouse identifier
• quantity_available (UInt32) - Available quantity
• quantity_reserved (UInt32) - Reserved quantity
• last_restocked (DateTime) - Last restock date
• reorder_level (UInt32) - Minimum stock level
• reorder_quantity (UInt32) - Reorder amount

📋 ANALYTICS_EVENTS TABLE:
• event_id (UUID) - Primary key
• user_id (UInt32) - Foreign key to users
• event_type (String) - Type of event
• event_timestamp (DateTime) - Event time
• page_url (String) - Page URL
• session_id (String) - Session identifier
• device_type (Enum8) - Device: desktop, mobile, tablet
• browser (String) - Browser name
• country (String) - User country
• properties (String) - Additional JSON properties"""

        return result

    elif tool_name == "get_database_schema":
        result = """DATABASE SCHEMA WITH RELATIONSHIPS:

┌─────────────────────────────────────────────────────┐
│                    USERS TABLE                      │
├──────────────────┬─────────────────┬────────────────┤
│ Column Name      │ Type            │ Key            │
├──────────────────┼─────────────────┼────────────────┤
│ user_id          │ UInt32          │ PRIMARY        │
│ username         │ String          │                │
│ email            │ String          │                │
│ first_name       │ String          │                │
│ last_name        │ String          │                │
│ created_at       │ DateTime        │                │
│ is_active        │ UInt8           │                │
│ account_type     │ Enum8           │                │
└──────────────────┴─────────────────┴────────────────┘

┌─────────────────────────────────────────────────────┐
│                    ORDERS TABLE                     │
├──────────────────┬─────────────────┬────────────────┤
│ Column Name      │ Type            │ Key            │
├──────────────────┼─────────────────┼────────────────┤
│ order_id         │ UInt32          │ PRIMARY        │
│ user_id          │ UInt32          │ FOREIGN        │
│ product_id       │ UInt32          │ FOREIGN        │
│ quantity         │ UInt16          │                │
│ total_amount     │ Decimal(10,2)   │                │
│ order_date       │ DateTime        │                │
│ status           │ Enum8           │                │
│ shipping_address │ String          │                │
└──────────────────┴─────────────────┴────────────────┘

┌─────────────────────────────────────────────────────┐
│                   PRODUCTS TABLE                    │
├──────────────────┬─────────────────┬────────────────┤
│ Column Name      │ Type            │ Key            │
├──────────────────┼─────────────────┼────────────────┤
│ product_id       │ UInt32          │ PRIMARY        │
│ product_name     │ String          │                │
│ category         │ String          │                │
│ price            │ Decimal(10,2)   │                │
│ stock_quantity   │ UInt32          │                │
│ manufacturer     │ String          │                │
│ created_at       │ DateTime        │                │
│ is_available     │ UInt8           │                │
└──────────────────┴─────────────────┴────────────────┘

┌─────────────────────────────────────────────────────┐
│                  INVENTORY TABLE                    │
├──────────────────┬─────────────────┬────────────────┤
│ Column Name      │ Type            │ Key            │
├──────────────────┼─────────────────┼────────────────┤
│ inventory_id     │ UInt32          │ PRIMARY        │
│ product_id       │ UInt32          │ FOREIGN        │
│ warehouse_id     │ UInt16          │                │
│ quantity_available│ UInt32         │                │
│ quantity_reserved│ UInt32          │                │
│ last_restocked   │ DateTime        │                │
│ reorder_level    │ UInt32          │                │
│ reorder_quantity │ UInt32          │                │
└──────────────────┴─────────────────┴────────────────┘

┌─────────────────────────────────────────────────────┐
│                ANALYTICS_EVENTS TABLE              │
├──────────────────┬─────────────────┬────────────────┤
│ Column Name      │ Type            │ Key            │
├──────────────────┼─────────────────┼────────────────┤
│ event_id         │ UUID            │ PRIMARY        │
│ user_id          │ UInt32          │ FOREIGN        │
│ event_type       │ String          │                │
│ event_timestamp  │ DateTime        │                │
│ page_url         │ String          │                │
│ session_id       │ String          │                │
│ device_type      │ Enum8           │                │
│ browser          │ String          │                │
│ country          │ String          │                │
│ properties       │ String          │                │
└──────────────────┴─────────────────┴────────────────┘

🔗 TABLE RELATIONSHIPS:
• orders.user_id        → users.user_id
• orders.product_id     → products.product_id
• inventory.product_id  → products.product_id
• analytics_events.user_id → users.user_id"""

        return result

    return "Tool result"

def get_live_tables_with_columns(client) -> str:
    """Get live tables and columns from ClickHouse system tables"""
    try:
        # Get all tables with their columns
        query = """
        SELECT
            table AS table_name,
            name AS column_name,
            type AS column_type
        FROM system.columns
        WHERE database = %(database)s
        ORDER BY table, position
        """

        result = client.query(query, parameters={'database': CLICKHOUSE_CONFIG['database']})

        if not result.result_rows:
            return "No tables found in database"

        # Group by table
        tables = {}
        for row in result.result_rows:
            table_name, column_name, column_type = row
            if table_name not in tables:
                tables[table_name] = []
            tables[table_name].append((column_name, column_type))

        # Format output
        output = "DATABASE TABLES AND COLUMNS:\n\n"
        for table_name, columns in tables.items():
            output += f"📋 {table_name.upper()} TABLE:\n"
            for column_name, column_type in columns:
                output += f"• {column_name} ({column_type})\n"
            output += "\n"

        return output

    except Exception as e:
        return f"Error getting live tables: {e}"

def get_live_database_schema(client) -> str:
    """Get live database schema in table format from ClickHouse system tables"""
    try:
        # Get all tables with their columns
        query = """
        SELECT
            table AS table_name,
            name AS column_name,
            type AS column_type,
            is_in_primary_key
        FROM system.columns
        WHERE database = %(database)s
        ORDER BY table, position
        """

        result = client.query(query, parameters={'database': CLICKHOUSE_CONFIG['database']})

        if not result.result_rows:
            return "No tables found in database"

        # Group by table
        tables = {}
        for row in result.result_rows:
            table_name, column_name, column_type, is_primary = row
            if table_name not in tables:
                tables[table_name] = []

            key_type = "PRIMARY" if is_primary else ""
            tables[table_name].append((column_name, column_type, key_type))

        # Format output in table format
        output = "DATABASE SCHEMA WITH RELATIONSHIPS:\n\n"

        for table_name, columns in tables.items():
            # Table header
            output += "┌─────────────────────────────────────────────────────┐\n"
            output += f"│{table_name.upper().center(53)}│\n"
            output += "├──────────────────┬─────────────────┬────────────────┤\n"
            output += "│ Column Name      │ Type            │ Key            │\n"
            output += "├──────────────────┼─────────────────┼────────────────┤\n"

            for column_name, column_type, key_type in columns:
                output += f"│ {column_name:<16} │ {column_type:<15} │ {key_type:<14} │\n"

            output += "└──────────────────┴─────────────────┴────────────────┘\n\n"

        # Try to detect relationships by foreign key naming convention
        relationships = detect_relationships(tables)
        if relationships:
            output += "🔗 TABLE RELATIONSHIPS:\n"
            for rel in relationships:
                output += f"• {rel}\n"

        return output

    except Exception as e:
        return f"Error getting live schema: {e}"

def detect_relationships(tables) -> List[str]:
    """Detect relationships based on column naming conventions"""
    relationships = []

    for table_name, columns in tables.items():
        for column_name, column_type, key_type in columns:
            # Look for foreign key patterns like user_id, product_id, etc.
            if column_name.endswith('_id') and key_type != "PRIMARY":
                # Try to find the referenced table
                referenced_table = column_name[:-3]  # Remove "_id"
                if referenced_table in tables or f"{referenced_table}s" in tables:
                    target_table = referenced_table if referenced_table in tables else f"{referenced_table}s"
                    relationships.append(f"{table_name}.{column_name} → {target_table}.{column_name}")

    return relationships

async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Call ClickHouse or return mock data if not available"""
    client = get_clickhouse_client()

    if client is None:
        # Fallback to mock data if ClickHouse is not available
        return get_mock_data(tool_name, arguments)

    try:
        if tool_name == "list_tables_with_columns":
            return get_live_tables_with_columns(client)
        elif tool_name == "get_database_schema":
            return get_live_database_schema(client)
        else:
            return get_mock_data(tool_name, arguments)
    except Exception as e:
        return f"Error querying ClickHouse: {e}"
    finally:
        try:
            client.close()
        except:
            pass


def format_table_as_ascii(headers, rows):
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
    return "\\n".join(table)

def query_vllm(messages: List[Dict[str, str]], max_tokens: int = 512) -> Dict[str, Any]:
    """Query the vLLM server using chat completions"""
    try:
        response = requests.post(
            f"{VLLM_URL}/v1/chat/completions",
            json={
                "model": "Qwen/Qwen3-4B",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.2,
                "top_p": 0.9,
                "stream": False
            },
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"vLLM error: {response.status_code} - {response.text}"}

    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

def detect_intent(message: str):
    """Simple keyword-based intent detection"""
    message_lower = message.lower()

    # Check if user wants database schema (CREATE statements)
    if any(word in message_lower for word in ['schema', 'create', 'ddl', 'definition']):
        return "get_database_schema", None
    # Check if user wants to see tables and columns
    elif any(word in message_lower for word in ['list', 'show', 'tables', 'columns', 'structure', 'database']):
        return "list_tables_with_columns", None
    else:
        return "none", None

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with simple keyword matching"""
    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Use simple keyword detection instead of AI
    tool_name, table_name = detect_intent(user_message)

    if tool_name != "none":
        # Execute the tool
        arguments = {}

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tool_result = loop.run_until_complete(call_mcp_tool(tool_name, arguments))
        loop.close()

        # Use vLLM to generate a nice explanation
        final_messages = [
            {
                "role": "system",
                "content": "You are a helpful ClickHouse database assistant. Explain the database information clearly and concisely. Do not include thinking text."
            },
            {
                "role": "user",
                "content": f"User asked: '{user_message}'\n\nDatabase result:\n{tool_result}\n\nExplain this briefly:"
            }
        ]

        final_response = query_vllm(final_messages, max_tokens=200)

        if "error" in final_response:
            return jsonify({"response": tool_result, "tool_used": tool_name})

        response_text = final_response["choices"][0]["message"]["content"].strip()

        # Remove thinking tokens if present
        if response_text.startswith("<think>"):
            # Extract content after </think>
            end_think = response_text.find("</think>")
            if end_think != -1:
                response_text = response_text[end_think + 8:].strip()
            else:
                # If no closing tag, remove everything before first paragraph
                response_text = response_text.split('\n\n', 1)[-1] if '\n\n' in response_text else response_text

        return jsonify({
            "response": response_text,
            "tool_used": tool_name,
            "tool_result": tool_result
        })

    else:
        # Direct chat response
        chat_messages = [
            {
                "role": "system",
                "content": "You are a helpful ClickHouse database assistant. Be brief and helpful. Available tables: users, orders, products, inventory, analytics_events."
            },
            {
                "role": "user",
                "content": user_message
            }
        ]

        chat_response = query_vllm(chat_messages, max_tokens=150)

        if "error" in chat_response:
            return jsonify({"response": "I can help you explore ClickHouse tables. Try asking about table schemas or sample data!"})

        response_text = chat_response["choices"][0]["message"]["content"].strip()

        # Remove thinking tokens if present
        if response_text.startswith("<think>"):
            end_think = response_text.find("</think>")
            if end_think != -1:
                response_text = response_text[end_think + 8:].strip()
            else:
                response_text = response_text.split('\n\n', 1)[-1] if '\n\n' in response_text else response_text

        return jsonify({
            "response": response_text
        })

@app.route('/api/tools', methods=['GET'])
def list_tools():
    """List available MCP tools"""
    return jsonify({
        "tools": [
            {
                "name": "get_table_schema",
                "description": "Get schema structure for a ClickHouse table",
                "tables": ["users", "orders", "products", "inventory", "analytics_events"]
            },
            {
                "name": "list_tables",
                "description": "List all available tables with their sizes"
            },
            {
                "name": "get_sample_data",
                "description": "Get sample rows from a table"
            }
        ]
    })

@app.route('/api/direct_tool', methods=['POST'])
def direct_tool():
    """Direct tool execution endpoint"""
    data = request.json
    tool_name = data.get('tool_name')
    arguments = data.get('arguments', {})

    if not tool_name:
        return jsonify({"error": "No tool name provided"}), 400

    # Execute the tool
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(call_mcp_tool(tool_name, arguments))
    loop.close()

    return jsonify({"result": result})

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    print("🌐 Starting Web Application on port 8095...")
    app.run(host='0.0.0.0', port=8095, debug=False)