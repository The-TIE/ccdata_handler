#!/bin/bash

echo "Starting ingest_futures_exchange_instrument_data.sh script..."

# Navigate to the project directory
cd /home/$USER/repositories/ccdata_handler

echo "Executing ingest_futures_exchange_instrument_data.py..."

# Execute the Python script
/home/$USER/repositories/ccdata_handler/.venv/bin/python -m scripts.ingest_futures_exchange_instrument_data

echo "Script execution completed."