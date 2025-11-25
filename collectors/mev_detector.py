import requests

# We use GeckoTerminal API as a proxy for "Live DEX Activity" since raw Mempool requires a node
def scan_dex():
    batch = []
    # Render (Solana) Pool
    try:
        r = requests.get("https://api.geckoterminal.com/api/v2/networks/solana/pools/rndrizKT3MK1iimdxRdWabcF7Zg7AR5T4nud4EkHBof_USDC", timeout=5)
        data = r.json().get('data', {}).get('attributes', {})
        
        vol = float(data.get('volume_usd', {}).get('h1', 0))
        txs = data.get('transactions', {}).get('h1', {})
        buys = txs.get('buys', 0)
        sells = txs.get('sells', 0)
        
        batch.append(("dex_scanner", "volume_1h", vol, {"token": "render"}))
        batch.append(("dex_scanner", "buy_pressure", buys, {"token": "render"}))
        
        if buys > sells * 2: # 2x Buy Pressure = Alpha Signal
            batch.append(("alpha_signal", "high_buy_pressure", 1, {"token": "render", "ratio": buys/sells}))
            
    except: pass
    return batch
