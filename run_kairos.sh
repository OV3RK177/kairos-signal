#!/bin/bash
echo ">>> Installing/Updating Dependencies..."
pip install -r requirements.txt -q
echo ">>> Launching KAIROS Engine..."
python3 kairos_sensor.py
