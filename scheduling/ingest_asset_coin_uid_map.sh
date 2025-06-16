#!/bin/bash

echo "Starting ingest_asset_coin_uid_map.sh script..."

# Navigate to the project directory
cd /home/$USER/repositories/ccdata_handler

echo "Executing asset_to_coin_uid_mapper.py..."

# Execute the Python script
/home/$USER/repositories/ccdata_handler/.venv/bin/python -m scripts.asset_to_coin_uid_mapper

echo "Script execution completed."