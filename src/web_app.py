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
from typing import Dict, Any

app = Flask(__name__)
CORS(app)

# Configuration
VLLM_URL = os.getenv('MOCK_VLLM_URL', 'http://localhost:8000')
MCP_SERVER_PATH = '/app/mcp_server.py'

async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Call ClickHouse directly instead of via MCP subprocess"""
    try:
        import clickhouse_connect

        # ClickHouse connection configuration
        client = clickhouse_connect.get_client(
            host=os.getenv('CLICKHOUSE_HOST', 'localhost'),
            port=int(os.getenv('CLICKHOUSE_PORT', 8123)),
            username=os.getenv('CLICKHOUSE_USER', 'default'),
            password=os.getenv('CLICKHOUSE_PASSWORD', 'password'),
            database=os.getenv('CLICKHOUSE_DATABASE', 'testdb')
        )

        ALLOWED_TABLES = ['users', 'orders', 'products', 'inventory', 'analytics_events']

        if tool_name == "list_tables":
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
                            'database': os.getenv('CLICKHOUSE_DATABASE', 'testdb'),
                            'table': table
                        }
                    ).result_rows

                    if result:
                        rows.append([table, result[0][0], str(result[0][1]), result[0][2]])
                    else:
                        rows.append([table, 'Not Found', '0', '0B'])
                except:
                    rows.append([table, 'Error', '-', '-'])

            # Format as ASCII table
            table_text = "📊 Available ClickHouse Tables:\\n\\n"
            table_text += format_table_as_ascii(headers, rows)
            return table_text

        elif tool_name == "get_table_schema":
            table_name = arguments.get("table_name")
            if table_name not in ALLOWED_TABLES:
                return f"❌ Table '{table_name}' is not accessible"

            # Get column information
            columns_query = """
            SELECT name, type, default_kind, default_expression, comment
            FROM system.columns
            WHERE database = %(database)s AND table = %(table)s
            ORDER BY position
            """
            columns = client.query(
                columns_query,
                parameters={
                    'database': os.getenv('CLICKHOUSE_DATABASE', 'testdb'),
                    'table': table_name
                }
            ).result_rows

            # Format schema response
            response = f"TABLE: {table_name}\\n"
            response += "=" * 50 + "\\n"
            headers = ['Column Name', 'Type', 'Default', 'Comment']
            rows = []
            for col in columns:
                default = col[3] if col[2] else 'None'
                comment = col[4] if col[4] else ''
                rows.append([col[0], col[1], default[:30], comment[:30]])

            response += format_table_as_ascii(headers, rows)
            return response

        elif tool_name == "get_sample_data":
            table_name = arguments.get("table_name")
            limit = min(arguments.get("limit", 5), 10)

            if table_name not in ALLOWED_TABLES:
                return f"❌ Table '{table_name}' is not accessible"

            # Get column names first
            columns_query = "SELECT name FROM system.columns WHERE database = %(database)s AND table = %(table)s ORDER BY position"
            columns = client.query(
                columns_query,
                parameters={
                    'database': os.getenv('CLICKHOUSE_DATABASE', 'testdb'),
                    'table': table_name
                }
            ).result_rows
            column_names = [col[0] for col in columns]

            # Get sample data with proper column ordering
            sample_query = f"SELECT {', '.join(column_names)} FROM {table_name} LIMIT {limit}"
            result = client.query(sample_query)

            response_text = f"📋 Sample Data from '{table_name}' (first {limit} rows):\\n\\n"
            response_text += format_table_as_ascii(column_names, result.result_rows)
            return response_text

        else:
            return f"Unknown tool: {tool_name}"

    except Exception as e:
        return f"Error: {str(e)}"


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

def query_vllm(prompt: str) -> Dict[str, Any]:
    """Query the vLLM server"""
    try:
        response = requests.post(
            f"{VLLM_URL}/v1/completions",
            json={
                "prompt": prompt,
                "max_tokens": 512,
                "temperature": 0.3,
                "stream": False
            },
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"vLLM error: {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Create prompt for vLLM
    prompt = f"""You are a ClickHouse database assistant with access to schema tools.

Available tools:
- get_table_schema: Get schema for a specific table
- list_tables: List all available tables
- get_sample_data: Get sample data from a table

If you need to use a tool, respond with JSON:
{{"use_tool": true, "tool_name": "tool_name", "arguments": {{"key": "value"}}}}

User: {user_message}
Assistant:"""

    # Query vLLM
    vllm_response = query_vllm(prompt)

    if "error" in vllm_response:
        return jsonify({"response": f"Error: {vllm_response['error']}"})

    # Extract the generated text
    generated_text = vllm_response["choices"][0]["text"].strip()

    # Check if the model wants to use a tool
    try:
        if generated_text.startswith('{') and 'use_tool' in generated_text:
            parsed = json.loads(generated_text)

            if parsed.get("use_tool"):
                tool_name = parsed["tool_name"]
                arguments = parsed["arguments"]

                # Call MCP tool
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                tool_result = loop.run_until_complete(
                    call_mcp_tool(tool_name, arguments)
                )
                loop.close()

                # Generate final response
                final_prompt = f"""Based on this ClickHouse information:

{tool_result}

Provide a helpful response to: "{user_message}"

Response:"""

                final_response = query_vllm(final_prompt)

                if "error" in final_response:
                    return jsonify({"response": tool_result})

                return jsonify({
                    "response": final_response["choices"][0]["text"].strip(),
                    "tool_used": tool_name,
                    "tool_result": tool_result
                })

    except (json.JSONDecodeError, KeyError):
        pass

    # Return the direct response
    return jsonify({"response": generated_text})

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
    print("🌐 Starting Web Application on port 8080...")
    app.run(host='0.0.0.0', port=8080, debug=True)