#!/bin/bash

echo "Starting ingest_ohlcv_spot_1d_top_pairs.sh script..."

# Navigate to the project directory
cd /home/$USER/repositories/ccdata_handler

echo "Executing ingest_ohlcv_spot_1d_top_pairs.py..."

# Execute the Python script
/home/$USER/repositories/ccdata_handler/.venv/bin/python -m scripts.ingest_ohlcv_spot_1d_top_pairs

echo "Script execution completed."