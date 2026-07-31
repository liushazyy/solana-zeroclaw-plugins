"""Test faucet.solana.com/api/request with GitHub PAT auth."""
import json, sys, os, time, urllib.request, urllib.error

from solders.keypair import Keypair
kp = Keypair()
addr = str(kp.pubkey())
print("wallet:", addr)

token = os.environ.get("GH_USER_TOKEN", "")
print("token len:", len(token))

def post(payload, auth_token=None):
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0",
               "Origin": "https://faucet.solana.com", "Referer": "https://faucet.solana.com/"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    req = urllib.request.Request("https://faucet.solana.com/api/request", data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read().decode(errors="replace")
            print(f"AUTH={bool(auth_token)} -> {r.status} {data[:300]}")
            return r.status, data
    except urllib.error.HTTPError as e:
        b = e.read().decode(errors="replace")[:300]
        print(f"AUTH={bool(auth_token)} -> HTTP {e.code} {b}")
        return e.code, b
    except Exception as e:
        print(f"ERR {str(e)[:100]}")
        return 0, str(e)

p = {"amount": 0.5, "walletAddress": addr, "network": "devnet"}
post(p, token)
time.sleep(2)
post(p)  # no auth
time.sleep(2)
p2 = {"amount": 1, "walletAddress": addr, "network": "testnet"}
post(p2, token)
