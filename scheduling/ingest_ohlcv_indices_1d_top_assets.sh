#!/bin/bash

echo "Starting ingest_ohlcv_indices_1d_top_assets.sh script..."

# Navigate to the project directory
cd /home/$USER/repositories/ccdata_handler

echo "Executing ingest_ohlcv_indices_1d_top_assets.py..."

# Execute the Python script
/home/$USER/repositories/ccdata_handler/.venv/bin/python -m scripts.ingest_ohlcv_indices_1d_top_assets

echo "Script execution completed."