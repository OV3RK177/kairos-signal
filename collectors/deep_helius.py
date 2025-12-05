import os, requests

HELIUS_KEY = os.getenv("HELIUS_API_KEY")
DEPIN_PROGRAMS = {
    "hivemapper": "hmapyHRS9mL9n69sQWEf5RrVnXXhhDMrBX9QbXE2nD8",
    "render": "rndrTKY3S5r8QiYkQ6J4YgTJ2YfT1fJfJmJX"
}

def deep_scan():
    batch = []
    url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_KEY}"
    
    for name, pid in DEPIN_PROGRAMS.items():
        # Get Largest Accounts (Whales)
        payload = {
            "jsonrpc": "2.0", "id": 1, "method": "getProgramAccounts",
            "params": [pid, {"filters": [{"dataSize": 165}], "encoding": "jsonParsed"}] # Token Account Size
        }
        try:
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code == 200:
                accounts = r.json().get('result', [])[:50] # Top 50 only to save DB
                for acc in accounts:
                    lamports = int(acc['account']['lamports'])
                    if lamports > 5000000000: # > 5 SOL balance (Whale Proxy)
                        batch.append(("whale_alert", "account_balance", lamports/1e9, {"wallet": acc['pubkey'], "project": name}))
        except: pass
    return batch
