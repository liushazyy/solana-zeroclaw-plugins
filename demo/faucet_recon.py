"""Test faucet.solana.com/api/request with amount in SOL."""
import json, sys, time, urllib.request, urllib.error, urllib.parse

from solders.keypair import Keypair
kp = Keypair()
addr = str(kp.pubkey())
print("wallet:", addr)

def post(payload):
    body = json.dumps(payload).encode()
    req = urllib.request.Request("https://faucet.solana.com/api/request", data=body,
                                 headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0",
                                          "Origin": "https://faucet.solana.com", "Referer": "https://faucet.solana.com/"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read().decode(errors="replace")
            print(f"POST {json.dumps(payload)[:110]} -> {r.status} {data[:250]}")
            return r.status, data
    except urllib.error.HTTPError as e:
        b = e.read().decode(errors="replace")[:250]
        print(f"POST {json.dumps(payload)[:110]} -> HTTP {e.code} {b}")
        return e.code, b
    except Exception as e:
        print(f"POST {json.dumps(payload)[:110]} -> ERR {str(e)[:100]}")
        return 0, str(e)

for amount in [1, 2, 0.5, "1"]:
    for net in ["devnet", "testnet"]:
        for cb in ["", None]:
            p = {"amount": amount, "walletAddress": addr, "network": net}
            if cb is not None:
                p["cloudflareCallback"] = cb
            st, data = post(p)
            if st == 200 and "success" in data.lower():
                print("!!! FAUCET SUCCESS with", json.dumps(p)[:120])
                sys.exit(0)
            time.sleep(1.5)
