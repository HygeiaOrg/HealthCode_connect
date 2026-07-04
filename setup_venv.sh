#!/bin/bash
# Script to setup python virtual environment and install requirements.

set -e

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo "=== Setting up Python Virtual Environment ==="
echo "Backend directory: $BACKEND_DIR"

if [ ! -d "$BACKEND_DIR" ]; then
    echo "Error: Backend directory not found at $BACKEND_DIR"
    exit 1
fi

cd "$BACKEND_DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in PATH."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in $BACKEND_DIR/.venv..."
    python3 -m venv .venv
else
    echo "Virtual environment (.venv) already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip and install requirements
echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing requirements from requirements.txt..."
pip install -r requirements.txt

echo "=== Setup Completed Successfully! ==="
echo "To activate this environment in your shell, run:"
echo "source backend/.venv/bin/activate"
