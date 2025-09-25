#!/bin/bash

# ClickHouse Setup Script for Testing
# This script helps you quickly set up ClickHouse for testing the Schema Assistant

echo "🚀 ClickHouse Setup Helper"
echo "========================="
echo ""

# Check if running with Docker or native
echo "Choose your setup method:"
echo "1) Docker (recommended)"
echo "2) Native installation"
echo -n "Enter choice [1-2]: "
read choice

case $choice in
    1)
        echo ""
        echo "📦 Setting up ClickHouse with Docker..."
        echo ""
        echo "Run this command to start ClickHouse:"
        echo ""
        echo "docker run -d \\"
        echo "  --name clickhouse-server \\"
        echo "  -p 8123:8123 \\"
        echo "  -p 9000:9000 \\"
        echo "  -e CLICKHOUSE_DB=testdb \\"
        echo "  -e CLICKHOUSE_USER=default \\"
        echo "  -e CLICKHOUSE_PASSWORD= \\"
        echo "  clickhouse/clickhouse-server:latest"
        echo ""
        echo "Then create some test tables:"
        echo ""
        echo "docker exec -it clickhouse-server clickhouse-client --query \\"
        echo "  \"CREATE TABLE IF NOT EXISTS testdb.users (id UInt32, name String, email String) ENGINE = MergeTree() ORDER BY id\""
        echo ""
        ;;

    2)
        echo ""
        echo "📥 Native ClickHouse Installation..."
        echo ""
        echo "For Ubuntu/Debian:"
        echo "sudo apt-get install -y apt-transport-https ca-certificates dirmngr"
        echo "sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 8919F6BD2B48D754"
        echo "echo \"deb https://packages.clickhouse.com/deb stable main\" | sudo tee /etc/apt/sources.list.d/clickhouse.list"
        echo "sudo apt-get update"
        echo "sudo apt-get install -y clickhouse-server clickhouse-client"
        echo "sudo service clickhouse-server start"
        echo ""
        echo "For macOS:"
        echo "brew install clickhouse"
        echo "clickhouse-server"
        echo ""
        ;;
esac

echo "📝 Environment Variables for the Schema Assistant:"
echo ""
echo "export CLICKHOUSE_HOST=localhost"
echo "export CLICKHOUSE_PORT=8123"
echo "export CLICKHOUSE_USER=default"
echo "export CLICKHOUSE_PASSWORD="
echo "export CLICKHOUSE_DATABASE=testdb"
echo ""
echo "🌐 Start the Schema Assistant:"
echo ""
echo "python src/web_app.py"
echo ""
echo "Then visit: http://localhost:8095"
echo ""
echo "✅ Once ClickHouse is running, the Schema Assistant will automatically detect your tables!"