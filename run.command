#!/bin/bash
cd "$(dirname "$0")"
echo "============================================================"
echo " Starting PC WARE Enterprise Website & ERP System"
echo "============================================================"

PORT=8080
if ! python3 -c "import socket; s = socket.socket(); s.bind(('127.0.0.1', $PORT)); s.close()" 2>/dev/null; then
  PORT=8085
fi

echo "Launching Server on http://localhost:$PORT..."
PORT=$PORT python3 server.py &
SERVER_PID=$!
sleep 1
open "http://localhost:$PORT"
wait $SERVER_PID
