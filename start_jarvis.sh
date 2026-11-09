#!/bin/bash
cd "$(dirname "$0")"

echo "=================================================="
echo "🤖 J.A.R.V.I.S. ALEXA BACKEND INITIALIZING..."
echo "=================================================="

# 1. Clean up legacy processes
echo "🧹 Cleaning previous processes..."
pkill -f "ngrok" 2>/dev/null
pkill -f "backend.server:app" 2>/dev/null
sleep 1

# 2. Activate virtual environment if present
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 3. Start Python backend in background
echo "🚀 1/2 Launching Jarvis Backend Engine (Port 8000)..."
python3 run.py > /tmp/jarvis_server.log 2>&1 &
SERVER_PID=$!
sleep 2

# 4. Start HTTPS Tunnel (ngrok or cloudflared)
echo "🌐 2/2 Starting HTTPS Webhook Tunnel..."
echo "--------------------------------------------------"
echo "✅ Jarvis Server is running! Press CTRL+C to shutdown."
echo "--------------------------------------------------"

if [ -f "ngrok.yml" ]; then
    ngrok start --config ngrok.yml --all
elif command -v ngrok &> /dev/null; then
    ngrok http 8000
elif command -v cloudflared &> /dev/null; then
    cloudflared tunnel --url http://localhost:8000
else
    echo "⚠️ Neither ngrok nor cloudflared found in PATH."
    echo "👉 Install ngrok (brew install ngrok) or cloudflared (brew install cloudflared) to expose your webhook to Alexa."
    wait $SERVER_PID
fi

# Cleanup python backend on exit
kill $SERVER_PID 2>/dev/null
