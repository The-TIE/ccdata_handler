#!/bin/bash

echo "Starting ingest_exchanges_general.sh script..."

# Navigate to the project directory
cd /home/$USER/repositories/ccdata_handler

echo "Executing ingest_ingest_exchanges_general.py..."

# Execute the Python script
/home/$USER/repositories/ccdata_handler/.venv/bin/python -m scripts.ingest_ingest_exchanges_general

echo "Script execution completed."