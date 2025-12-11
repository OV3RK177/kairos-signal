#!/bin/bash
while true; do
    echo "🌙 Night Watchman: Requesting Intelligence Scan..."
    date
    /root/kairos-signal/venv/bin/python3 /root/kairos-signal/core/neural_link.py >> night_watch.log 2>&1
    echo "💤 Sleeping for 60 minutes..."
    sleep 3600
done
