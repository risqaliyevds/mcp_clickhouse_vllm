# ClickHouse MCP Schema Assistant

A complete demonstration project that integrates ClickHouse database with MCP (Model Context Protocol) server and vLLM to provide intelligent table schema exploration through a web interface.

## Features

- **ClickHouse Integration**: Pre-configured ClickHouse database with sample tables
- **MCP Server**: Provides schema information via MCP protocol
- **Mock vLLM Server**: Simulates vLLM API for testing (easily replaceable with real vLLM)
- **Web Interface**: Beautiful interactive UI to explore database schemas
- **Docker Containerized**: Everything runs in Docker containers

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   Web Browser   │────▶│   Web App    │────▶│  Mock vLLM  │
│  (Port 8080)    │     │  (Flask)     │     │ (Port 8000) │
└─────────────────┘     └──────────────┘     └─────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  MCP Server  │
                        │   (Python)   │
                        └──────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  ClickHouse  │
                        │ (Port 8123)  │
                        └──────────────┘
```

## Available Tables

The demo includes 5 pre-configured tables with sample data:

1. **users** - User account information
2. **orders** - Customer orders
3. **products** - Product catalog
4. **inventory** - Warehouse inventory tracking
5. **analytics_events** - User interaction events

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- 4GB RAM minimum
- Ports 8000, 8080, 8123 available

### Installation

1. Clone or navigate to the project directory:
```bash
cd clickhouse-mcp-project
```

2. Start all services:
```bash
docker-compose up --build
```

3. Wait for services to initialize (about 30 seconds)

4. Open your browser and navigate to:
```
http://localhost:8080
```

## Using the Application

### Web Interface (http://localhost:8080)

The web interface provides:
- **Chat Interface**: Ask questions about your database schemas
- **Quick Actions**: One-click access to common operations
- **Table Browser**: Click on any table to view its schema
- **Example Queries**: Pre-defined queries to get you started

### Sample Queries

Try these queries in the chat interface:
- "Show me the schema for the users table"
- "What columns does the orders table have?"
- "List all available tables"
- "Get sample data from the products table"
- "Show me the inventory table structure"

### Direct API Access

You can also directly access the services:

- **Mock vLLM API**: http://localhost:8000
- **ClickHouse HTTP**: http://localhost:8123
- **Web App API**: http://localhost:8080/api/tools

## Integration with Real vLLM

To connect to your actual vLLM server:

1. Stop the mock vLLM container:
```bash
docker-compose stop mock-vllm
```

2. Update the `MOCK_VLLM_URL` in `docker-compose.yml`:
```yaml
environment:
  MOCK_VLLM_URL: http://your-vllm-server:8000  # Change to your vLLM server
```

3. Restart the web app:
```bash
docker-compose up web-app
```

## Project Structure

```
clickhouse-mcp-project/
├── docker-compose.yml           # Docker orchestration
├── requirements.txt             # Python dependencies
├── src/
│   ├── mcp_server.py           # MCP server implementation
│   ├── mock_vllm.py            # Mock vLLM for testing
│   ├── web_app.py              # Flask web application
│   └── templates/
│       └── index.html          # Web interface
├── docker/
│   ├── Dockerfile.mcp          # MCP server container
│   ├── Dockerfile.vllm         # Mock vLLM container
│   ├── Dockerfile.app          # Web app container
│   └── clickhouse/
│       └── init.sql            # Database initialization
└── data/
    └── clickhouse/             # ClickHouse data volume
```

## Configuration

### Environment Variables

You can customize the following in `docker-compose.yml`:

```yaml
CLICKHOUSE_HOST: clickhouse
CLICKHOUSE_PORT: 8123
CLICKHOUSE_USER: default
CLICKHOUSE_PASSWORD: password
CLICKHOUSE_DATABASE: testdb
```

### Adding New Tables

1. Edit `docker/clickhouse/init.sql` to add your table definitions
2. Update `ALLOWED_TABLES` in `src/mcp_server.py`
3. Rebuild and restart:
```bash
docker-compose down
docker-compose up --build
```

## Testing

### Check Service Health

```bash
# Check if all containers are running
docker-compose ps

# View logs
docker-compose logs -f

# Test MCP server
docker exec -it mcp-server python -c "print('MCP Server OK')"

# Test ClickHouse
curl http://localhost:8123/?query=SELECT%201
```

### Manual MCP Tool Testing

```bash
# Enter MCP container
docker exec -it mcp-server bash

# Test tool directly
python -c "
import asyncio
from mcp_server import app, get_clickhouse_client
# Test connection
client = get_clickhouse_client()
print(client.query('SELECT count() FROM users').result_rows)
"
```

## Troubleshooting

### Services not starting

```bash
# Check logs for errors
docker-compose logs clickhouse
docker-compose logs mcp-server
docker-compose logs web-app

# Reset everything
docker-compose down -v
docker-compose up --build
```

### ClickHouse connection issues

```bash
# Test ClickHouse directly
docker exec -it clickhouse-test clickhouse-client --query "SHOW DATABASES"
```

### Port conflicts

If ports are already in use, modify `docker-compose.yml`:
```yaml
ports:
  - "8081:8080"  # Change external port
```

## Production Deployment

For production use:

1. **Security**: Update default passwords in `docker-compose.yml`
2. **vLLM**: Replace mock with real vLLM server endpoint
3. **Persistence**: Configure proper volume mounts for ClickHouse data
4. **Scaling**: Consider using Kubernetes for orchestration
5. **Monitoring**: Add logging and monitoring solutions

## Development

### Running locally without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Start ClickHouse (use official installation)
# Update connection settings in environment

# Run MCP server
python src/mcp_server.py

# Run mock vLLM
python src/mock_vllm.py

# Run web app
python src/web_app.py
```

## License

This is a demonstration project for educational purposes.

## Support

For issues or questions about:
- **MCP Protocol**: See [MCP documentation](https://github.com/anthropics/mcp)
- **ClickHouse**: Visit [ClickHouse docs](https://clickhouse.com/docs)
- **vLLM**: Check [vLLM documentation](https://docs.vllm.ai)

---

Built with ❤️ for demonstrating ClickHouse + MCP + vLLM integration