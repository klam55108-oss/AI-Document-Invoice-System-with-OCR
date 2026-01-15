#!/bin/bash

source venv/bin/activate

echo ""
echo "Starting Streamlit dashboard on port 8501..."
echo ""

streamlit run interface/dashboard/app.py --server.port 8501
