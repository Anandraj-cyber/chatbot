#!/bin/bash
echo "========================================"
echo "  Marine Engine AI Chatbot - Setup"
echo "========================================"

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed!"
    exit 1
fi

echo "[1/4] Python found: $(python3 --version)"

if [ ! -d "venv" ]; then
    echo "[2/4] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[2/4] Virtual environment already exists."
fi

echo "[3/4] Activating virtual environment..."
source venv/bin/activate

echo "[4/4] Installing dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "========================================"
echo "  Starting Chatbot..."
echo "========================================"
echo ""
echo "Access the chatbot at: http://localhost:8000"
echo "Press CTRL+C to stop the server"
echo ""

cd src/templates
python botmarch11.py
