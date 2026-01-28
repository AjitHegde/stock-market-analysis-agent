#!/bin/bash
# Launcher script for Stock Market AI Agent Web UI

echo "🚀 Starting Stock Market AI Agent Web UI..."
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit is not installed. Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the Streamlit app
streamlit run src/web_ui.py
