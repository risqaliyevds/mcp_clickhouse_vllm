#!/usr/bin/env python3
"""
FastAPI Web Application for ClickHouse Schema Assistant
Provides live ClickHouse database schema visualization with AI-powered chat interface
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import clickhouse_connect
import requests
import json
import os
import uvicorn
import asyncio

# Initialize FastAPI app
app = FastAPI(title="ClickHouse Schema Assistant", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory="src/templates")

# Configuration from environment variables
VLLM_URL = os.getenv('VLLM_URL', 'http://localhost:8000')
CLICKHOUSE_CONFIG = {
    'host': os.getenv('CLICKHOUSE_HOST', 'localhost'),
    'port': int(os.getenv('CLICKHOUSE_PORT', 8123)),
    'username': os.getenv('CLICKHOUSE_USER', 'default'),
    'password': os.getenv('CLICKHOUSE_PASSWORD', ''),
    'database': os.getenv('CLICKHOUSE_DATABASE', 'default')
}

# Pydantic models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    tool_result: Optional[str] = None
    tool_used: Optional[str] = None

class ToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = {}

# ClickHouse client management
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

# Live data functions - NO MOCK DATA
def get_live_tables_with_columns(client) -> str:
    """Get live tables and columns from ClickHouse system tables"""
    if not client:
        raise HTTPException(status_code=503, detail="ClickHouse database not available")

    try:
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
        raise HTTPException(status_code=500, detail=f"Error querying ClickHouse: {e}")

def get_live_database_schema(client) -> str:
    """Get live database schema in table format from ClickHouse system tables"""
    if not client:
        raise HTTPException(status_code=503, detail="ClickHouse database not available")

    try:
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

        # Detect relationships by foreign key naming convention
        relationships = detect_relationships(tables)
        if relationships:
            output += "🔗 TABLE RELATIONSHIPS:\n"
            for rel in relationships:
                output += f"• {rel}\n"

        return output

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying ClickHouse: {e}")

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

async def execute_clickhouse_tool(tool_name: str, arguments: dict) -> str:
    """Execute ClickHouse tool - NO MOCK DATA FALLBACK"""
    client = get_clickhouse_client()

    if not client:
        raise HTTPException(
            status_code=503,
            detail="ClickHouse database is not available. Please check your database connection."
        )

    try:
        if tool_name == "list_tables_with_columns":
            return get_live_tables_with_columns(client)
        elif tool_name == "get_database_schema":
            return get_live_database_schema(client)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")
    finally:
        try:
            client.close()
        except:
            pass

async def query_vllm(messages: List[Dict[str, str]]) -> str:
    """Query vLLM server with chat completion"""
    try:
        response = requests.post(
            f"{VLLM_URL}/v1/chat/completions",
            json={
                "messages": messages,
                "max_tokens": 512,
                "temperature": 0.7
            },
            timeout=30
        )

        if response.status_code != 200:
            raise HTTPException(status_code=503, detail="vLLM server not available")

        data = response.json()
        content = data['choices'][0]['message']['content']

        # Remove thinking tokens if present
        if '<think>' in content:
            content = content.split('</think>')[-1].strip()

        return content

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"vLLM server not available: {e}")

# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """Handle chat messages with ClickHouse integration"""
    try:
        # Detect intent
        tool_name, arguments = detect_intent(chat_request.message)

        if tool_name != "none":
            try:
                # Execute ClickHouse tool
                tool_result = await execute_clickhouse_tool(tool_name, arguments or {})

                # Generate natural language response using vLLM
                messages = [
                    {"role": "system", "content": "You are a ClickHouse database assistant. Provide helpful responses about database schemas."},
                    {"role": "user", "content": f"Based on this ClickHouse schema information:\n\n{tool_result}\n\nUser asked: {chat_request.message}"}
                ]

                response = await query_vllm(messages)

                return ChatResponse(
                    response=response,
                    tool_result=tool_result,
                    tool_used=tool_name
                )

            except HTTPException as e:
                if e.status_code == 503:
                    # ClickHouse is not available - provide helpful message
                    error_message = """❌ ClickHouse Database Not Available

To use the ClickHouse Schema Assistant, you need:

1. **Start ClickHouse Server**:
   - Install ClickHouse server locally
   - Or configure connection to remote ClickHouse

2. **Set Environment Variables**:
   ```bash
   export CLICKHOUSE_HOST=localhost
   export CLICKHOUSE_PORT=8123
   export CLICKHOUSE_USER=default
   export CLICKHOUSE_PASSWORD=your_password
   export CLICKHOUSE_DATABASE=your_database
   ```

3. **Verify Connection**:
   - Check `/health` endpoint
   - Ensure ClickHouse is running on configured port

Once connected, I can show you real-time database schemas!"""

                    return ChatResponse(
                        response=error_message,
                        tool_result="ClickHouse database connection failed",
                        tool_used="error_handler"
                    )
                else:
                    raise
        else:
            # Regular chat without tools
            try:
                messages = [
                    {"role": "system", "content": "You are a ClickHouse database assistant. Help users with database questions and setup."},
                    {"role": "user", "content": chat_request.message}
                ]

                response = await query_vllm(messages)
                return ChatResponse(response=response)

            except HTTPException:
                # vLLM not available - provide basic response
                return ChatResponse(
                    response="I'm a ClickHouse database assistant. I can help you explore database schemas when ClickHouse is connected. To get started, please ensure ClickHouse server is running and properly configured."
                )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.post("/api/direct_tool")
async def direct_tool(tool_request: ToolRequest):
    """Direct tool execution endpoint"""
    try:
        result = await execute_clickhouse_tool(tool_request.tool_name, tool_request.arguments)
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {e}")

@app.get("/api/tools")
async def list_tools():
    """List available tools"""
    return {
        "tools": [
            {
                "name": "list_tables_with_columns",
                "description": "List all tables with their columns and types",
                "parameters": {}
            },
            {
                "name": "get_database_schema",
                "description": "Get database schema in structured table format",
                "parameters": {}
            }
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Test ClickHouse connection
    client = get_clickhouse_client()
    clickhouse_status = "healthy" if client else "unavailable"
    if client:
        try:
            client.close()
        except:
            pass

    # Test vLLM connection
    try:
        response = requests.get(f"{VLLM_URL}/health", timeout=5)
        vllm_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        vllm_status = "unavailable"

    return {
        "status": "healthy",
        "clickhouse": clickhouse_status,
        "vllm": vllm_status,
        "database": CLICKHOUSE_CONFIG['database']
    }

if __name__ == "__main__":
    port = int(os.getenv('WEB_APP_PORT', 8095))
    host = os.getenv('WEB_APP_HOST', '0.0.0.0')

    print(f"🌐 Starting ClickHouse Schema Assistant on {host}:{port}...")
    print(f"📊 ClickHouse: {CLICKHOUSE_CONFIG['host']}:{CLICKHOUSE_CONFIG['port']}")
    print(f"🤖 vLLM: {VLLM_URL}")

    uvicorn.run(app, host=host, port=port)