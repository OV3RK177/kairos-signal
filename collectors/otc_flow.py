import os
from web3 import Web3

OTC_DESKS = {"cumberland": "0x1f5A92B5F7b1c03d92fF3Fbf5D7F8bB9f2b5A1c0"}
w3 = Web3(Web3.HTTPProvider("https://eth.llamarpc.com"))

def track_otc_flow():
    batch = []
    for name, wallet in OTC_DESKS.items():
        try:
            bal = w3.eth.get_balance(wallet)
            batch.append(("otc_desk", "eth_balance", w3.from_wei(bal, 'ether'), {"desk": name}))
        except: pass
    return batch
