#!/bin/bash

echo "======================================"
echo "  SmartFridge - Starting Application"
echo "======================================"
echo ""

# Check if requirements are installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

echo "Starting Flask backend on http://localhost:5000"
echo ""
echo "To use the app:"
echo "1. Keep this terminal window open"
echo "2. Open frontend/index.html in your browser"
echo "   OR run: cd frontend && python3 -m http.server 8080"
echo "   Then visit http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop the server"
echo "======================================"
echo ""

python3 api.py