"""Test faucet.solana.com/api/request with the real payload shape from JS."""
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
            print(f"POST {json.dumps(payload)[:100]} -> {r.status} {data[:200]}")
            return r.status, data
    except urllib.error.HTTPError as e:
        b = e.read().decode(errors="replace")[:200]
        print(f"POST {json.dumps(payload)[:100]} -> HTTP {e.code} {b}")
        return e.code, b
    except Exception as e:
        print(f"POST {json.dumps(payload)[:100]} -> ERR {str(e)[:100]}")
        return 0, str(e)

# real shape: amount, walletAddress, cloudflareCallback, network
for cb in ["", "test", None]:
    for net in ["devnet", "testnet"]:
        p = {"amount": 1000000000, "walletAddress": addr, "network": net}
        if cb is not None:
            p["cloudflareCallback"] = cb
        st, _ = post(p)
        if st == 200:
            print("SUCCESS with", json.dumps(p)[:120])
            sys.exit(0)
        time.sleep(2)
