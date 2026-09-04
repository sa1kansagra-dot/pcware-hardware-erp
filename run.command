#!/bin/bash
cd "$(dirname "$0")"
echo "============================================================"
echo " Starting PCWARE Hardware E-Commerce & Service ERP"
echo "============================================================"

# Check if port 8080 is free, or open index.html directly
if python3 -c "import socket; s = socket.socket(); s.bind(('127.0.0.1', 8080)); s.close()" 2>/dev/null; then
  echo "Launching Python Backend Server on http://localhost:8080..."
  python3 server.py &
  SERVER_PID=$!
  sleep 1
  open "http://localhost:8080"
  wait $SERVER_PID
else
  echo "Port 8080 already in use or restricted. Opening application directly in browser..."
  open "static/index.html"
fi
