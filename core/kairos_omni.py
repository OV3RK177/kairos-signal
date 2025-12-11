import clickhouse_connect
import ollama
import pandas as pd
import numpy as np
import os
import json
import time
import requests
from datetime import datetime

# --- CONFIG ---
# Running on HOST, so we use localhost to reach Docker container
CH_HOST = 'localhost' 
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos')
MODEL = "kimi-k2-thinking:cloud"
DISCORD_WEBHOOK = "" 

print(f"// KAIROS OMNI-SCANNER V3 // LEDGER ENABLED")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def send_discord_alert(asset, action, price, rsi, reason):
    if not DISCORD_WEBHOOK: return
    try:
        color = 5763719 if action == "BUY" else 15548997
        payload = {
            "username": "Kairos Signal",
            "embeds": [{
                "title": f"🚨 SIGNAL: {action} {asset}",
                "color": color,
                "fields": [
                    {"name": "Price", "value": f"${price:,.4f}", "inline": True},
                    {"name": "RSI", "value": f"{rsi:.1f}", "inline": True},
                    {"name": "Rationale", "value": reason, "inline": False}
                ],
                "footer": {"text": "Kairos Omni V3"}
            }]
        }
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=5)
    except: pass

# 1. CONNECT
try:
    client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
except Exception as e:
    log(f"❌ DB FAIL: {e}"); exit(1)

log("✅ Connected. Scanning 900+ assets...")

while True:
    try:
        # 2. FETCH HISTORY
        q = """
        SELECT project_slug, groupArray(price_close) as prices, groupArray(volume_total) as volumes
        FROM (
            SELECT project_slug, price_close, volume_total, timestamp 
            FROM candles_10m 
            WHERE timestamp > now() - INTERVAL 4 HOUR
            ORDER BY timestamp ASC
        ) 
        GROUP BY project_slug
        HAVING length(prices) >= 20
        """
        
        df = client.query_df(q)
        if df.empty: time.sleep(60); continue

        signals_found = 0
        
        # 3. SCAN
        for index, row in df.iterrows():
            asset = row['project_slug']
            prices = np.array(row['prices'], dtype=float)
            volumes = np.array(row['volumes'], dtype=float)
            
            # Math Layer
            deltas = np.diff(prices)
            gains = np.maximum(deltas, 0)
            losses = -np.minimum(deltas, 0)
            avg_gain = np.mean(gains[-14:])
            avg_loss = np.mean(losses[-14:])
            if avg_loss == 0: rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            avg_vol = np.mean(volumes[:-1]) if len(volumes) > 1 else 1
            vol_spike = volumes[-1] / avg_vol if avg_vol > 0 else 0
            pct_change = abs((prices[-1] - prices[-2]) / prices[-2]) * 100 if len(prices) > 1 else 0

            # Filter
            trigger = False
            reason = ""
            if rsi < 25: trigger = True; reason = "Oversold"
            elif rsi > 75: trigger = True; reason = "Overbought"
            elif vol_spike > 3.0: trigger = True; reason = "Vol Spike"
            elif pct_change > 3.0: trigger = True; reason = "Price Surge"

            if trigger:
                log(f"⚡ CANDIDATE: {asset} | {reason} | RSI: {rsi:.1f}")
                
                # AI Layer
                success = False
                for attempt in range(1, 4):
                    try:
                        prompt = f"Analyze {asset}. Last 10 Prices: {prices[-10:]}. RSI: {rsi:.1f}. Reason: {reason}. Output JSON: {{'action': 'BUY/SELL', 'confidence': 'high', 'reason': 'short text'}}"
                        response = ollama.generate(model=MODEL, prompt=prompt, stream=False, format='json')
                        decision = json.loads(response['response'])
                        
                        if decision.get('confidence') == 'high' and decision.get('action') in ['BUY', 'SELL']:
                            price = prices[-1]
                            action = decision['action']
                            rationale = decision['reason']
                            
                            log(f"🎯 SIGNAL: {action} {asset} | {rationale}")
                            send_discord_alert(asset, action, price, rsi, rationale)
                            
                            # --- V3 UPGRADE: WRITE TO LEDGER ---
                            try:
                                ledger_data = [[datetime.now(), asset, action, price, rationale]]
                                client.insert('signal_ledger', ledger_data, column_names=['signal_time', 'asset', 'action', 'entry_price', 'reason'])
                                log("📝 Recorded in Ledger.")
                            except Exception as e:
                                log(f"⚠️ Ledger Write Failed: {e}")
                            # -----------------------------------
                            
                            signals_found += 1
                        success = True
                        break 
                        
                    except Exception as e:
                        wait_time = attempt * 10 
                        log(f"⚠️ AI Busy. Yielding {wait_time}s...")
                        time.sleep(wait_time)
                
        log(f"🏁 Scan Finished. Signals: {signals_found}. Cooling down...")
        time.sleep(600) 

    except Exception as e:
        log(f"❌ CRITICAL: {e}"); time.sleep(60)
