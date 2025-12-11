#!/bin/bash
while true; do
    echo "🔄 Starting Market Feed..."
    python3 core/market_feed.py
    
    echo "⚠️ Process crashed or stopped. Restarting in 5 seconds..."
    sleep 5
done
