# ClickHouse Schema Assistant

A dynamic web application that provides real-time ClickHouse database schema visualization and exploration with AI-powered chat interface.

## Features

- **Live Database Connection**: Automatically connects to ClickHouse and queries real schema information
- **Smart Fallback**: Falls back to mock data when ClickHouse is unavailable
- **Dynamic Schema Detection**: Reads table structures directly from `system.tables` and `system.columns`
- **Relationship Detection**: Automatically detects foreign key relationships based on naming conventions
- **AI-Powered Chat**: Uses vLLM (Qwen3-4B) for natural language interaction
- **Two View Modes**:
  - **Tables & Columns**: User-friendly view with column types and descriptions
  - **Schema View**: Structured table format with primary/foreign key information

## Quick Start

### 1. Prerequisites

- Python 3.8+
- ClickHouse server (optional - uses mock data if not available)
- vLLM server running Qwen/Qwen3-4B model

### 2. Installation

```bash
git clone <repository-url>
cd mcp_clickhouse_vllm
pip install -r requirements.txt
```

### 3. Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Run

```bash
python src/web_app.py
```

Visit `http://localhost:8095`

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `CLICKHOUSE_HOST` | ClickHouse server host | `localhost` |
| `CLICKHOUSE_PORT` | ClickHouse HTTP port | `8123` |
| `CLICKHOUSE_USER` | Database username | `default` |
| `CLICKHOUSE_PASSWORD` | Database password | `` |
| `CLICKHOUSE_DATABASE` | Target database | `default` |
| `VLLM_URL` | vLLM server URL | `http://localhost:8000` |

## Usage

### Chat Commands

- **"show tables"** or **"list columns"** → Shows all tables with columns and types
- **"database schema"** or **"schema"** → Shows structured schema with relationships
- **"create tables"** → Shows CREATE TABLE statements (mock mode)

### API Endpoints

- `GET /` - Web interface
- `POST /api/chat` - Chat with the assistant
- `GET /api/tools` - List available tools
- `POST /api/direct_tool` - Direct tool execution

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │   Flask App     │    │   ClickHouse    │
│   (HTML/JS)     │◄──►│   (Python)      │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   vLLM Server   │
                       │   (Qwen3-4B)    │
                       └─────────────────┘
```

## Development

### Project Structure

```
mcp_clickhouse_vllm/
├── src/
│   ├── web_app.py              # Main Flask application
│   ├── mcp_server.py           # MCP protocol server
│   └── templates/
│       └── index.html          # Web interface
├── docker/                     # Docker configurations
├── docker-compose.yml          # Docker Compose setup
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
└── README.md                  # This file
```

### Key Functions

- `get_live_tables_with_columns()` - Queries ClickHouse system tables
- `get_live_database_schema()` - Formats schema with relationships
- `detect_relationships()` - Auto-detects foreign key relationships
- `get_clickhouse_client()` - Manages database connections

## Docker Deployment

```bash
docker-compose up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with both live ClickHouse and mock data
5. Submit a pull request

## License

MIT License
