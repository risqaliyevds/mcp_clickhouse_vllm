# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Prerequisites
```bash
# Start vLLM server (run this BEFORE docker-compose)
vllm serve Qwen/Qwen3-4B
# vLLM will run on port 8000
```

### Running the Application
```bash
# Start all services with Docker Compose (after vLLM is running)
docker-compose up --build

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service-name]  # service-name: clickhouse, mcp-server, web-app
```

### Development Commands
```bash
# Run services individually (requires local Python environment)
python src/mcp_server.py    # Start MCP server
python src/web_app.py        # Start Flask web app

# Test ClickHouse connection
docker exec -it clickhouse-test clickhouse-client --query "SHOW DATABASES"

# Check service health
docker-compose ps
curl http://localhost:8123/?query=SELECT%201  # Test ClickHouse
curl http://localhost:8080/health             # Test web app
curl http://localhost:8000/health             # Test vLLM (external)
```

## Architecture

This is a demonstration project integrating ClickHouse database with MCP (Model Context Protocol) server and vLLM for intelligent schema exploration.

### Core Components

1. **ClickHouse Database** (`docker-compose.yml`, `docker/clickhouse/init.sql`)
   - Runs on port 8123 (HTTP) and 9000 (native)
   - Pre-populated with 5 tables: users, orders, products, inventory, analytics_events
   - Tables use MergeTree engine with partitioning for performance

2. **MCP Server** (`src/mcp_server.py`)
   - Provides schema information via MCP protocol using stdio transport
   - Implements three tools: `get_table_schema`, `list_tables`, `get_sample_data`
   - Restricts access to ALLOWED_TABLES list for security
   - Formats responses as ASCII tables for better readability

3. **Web Application** (`src/web_app.py`, `src/templates/index.html`)
   - Flask-based web interface on port 8080
   - Integrates with external vLLM server (Qwen/Qwen3-4B) running on host
   - Uses proper chat completion API with intent analysis and tool orchestration
   - Provides chat interface and direct tool execution endpoints

4. **External vLLM Server** (host system, port 8000)
   - Real vLLM instance serving Qwen/Qwen3-4B model
   - Accessed via OpenAI-compatible chat completions API
   - Connected through Docker's host.docker.internal networking

### Data Flow
1. User sends query through web interface → Flask app
2. Flask app analyzes intent using vLLM chat completions API
3. vLLM determines if tool usage is needed and returns JSON response
4. Flask app executes ClickHouse queries directly (bypassing MCP subprocess)
5. Results fed back to vLLM for natural language response generation
6. Final response returned to user

### Key Implementation Details

- **Intent Analysis**: Two-stage prompting - first analyze intent, then generate response
- **Chat Completions API**: Uses proper OpenAI-compatible chat format with system/user messages
- **Tool Orchestration**: Flask app manages tool execution based on vLLM intent analysis
- **ASCII Table Formatting**: Custom formatting function for consistent table display
- **Container Networking**: Web app connects to host vLLM via `host.docker.internal`
- **Environment Configuration**: vLLM URL configured via `VLLM_URL` environment variable
- **Error Handling**: Comprehensive fallback system with try-catch blocks

### Database Schema Highlights

- **Users Table**: Partitioned by month, includes account type enum
- **Orders Table**: Links users and products, includes status enum
- **Products Table**: Simple product catalog with availability flag
- **Inventory Table**: Tracks stock across multiple warehouses
- **Analytics Events**: UUID-based event tracking with JSON properties field