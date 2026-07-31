"""Test anonymous faucet requests with small amounts (page says 2 requests / 8h, no GitHub needed)."""
import json, sys, time, urllib.request, urllib.error

from solders.keypair import Keypair
kp = Keypair()
ADDR = str(kp.pubkey())
print("wallet:", ADDR)

def post(amount, net="devnet"):
    body = json.dumps({"amount": amount, "walletAddress": ADDR, "network": net}).encode()
    req = urllib.request.Request("https://faucet.solana.com/api/request", data=body,
                                 headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
                                          "Origin": "https://faucet.solana.com", "Referer": "https://faucet.solana.com/"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = r.read().decode(errors="replace")
            print(f"amount={amount} -> {r.status} {d[:250]}")
            return r.status, d
    except urllib.error.HTTPError as e:
        d = e.read().decode(errors="replace")[:250]
        print(f"amount={amount} -> HTTP {e.code} {d}")
        return e.code, d
    except Exception as e:
        print(f"amount={amount} -> ERR {str(e)[:100]}")
        return 0, str(e)

for amt in [0.1, 0.05, 0.02, 0.01]:
    st, d = post(amt)
    if st == 200:
        break
    time.sleep(2)

# verify balance
time.sleep(6)
body = json.dumps({"jsonrpc":"2.0","id":1,"method":"getBalance","params":[ADDR]}).encode()
req = urllib.request.Request("https://api.devnet.solana.com", data=body, headers={"Content-Type":"application/json"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("BALANCE:", r.read().decode()[:180])
except Exception as e:
    print("balance err:", str(e)[:60])
