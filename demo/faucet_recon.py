"""Test faucet.solana.com/api/request with several payload shapes."""
import json, sys, time, urllib.request, urllib.error

from solders.keypair import Keypair
kp = Keypair()
addr = str(kp.pubkey())
print("wallet:", addr)

def post(payload, path="/api/request"):
    body = json.dumps(payload).encode()
    req = urllib.request.Request("https://faucet.solana.com" + path, data=body,
                                 headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Origin": "https://faucet.solana.com", "Referer": "https://faucet.solana.com/"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read().decode(errors="replace")
            print(f"POST {path} {payload} -> {r.status} {data[:250]}")
            return r.status, data
    except urllib.error.HTTPError as e:
        b = e.read().decode(errors="replace")[:250]
        print(f"POST {path} {payload} -> HTTP {e.code} {b}")
        return e.code, b
    except Exception as e:
        print(f"POST {path} {payload} -> ERR {str(e)[:120]}")
        return 0, str(e)

payloads = [
    {"address": addr, "amount": 1000000000},
    {"address": addr, "amount": 1},
    {"wallet": addr, "amount": 1000000000},
    {"address": addr, "lamports": 1000000000},
    {"address": addr},
]
for p in payloads:
    post(p)
    time.sleep(2)
