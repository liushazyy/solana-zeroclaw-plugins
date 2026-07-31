"""Deep-dig faucet.solana.com/api/request: extract payload shape from page JS, then test."""
import json, sys, re, time, urllib.request, urllib.error

from solders.keypair import Keypair
kp = Keypair()
addr = str(kp.pubkey())
print("wallet:", addr)

# 1. fetch page JS and extract /api/request context
try:
    req = urllib.request.Request("https://faucet.solana.com/_next/static/chunks/app/page-566151c6f19b04eb.js",
                                 headers={"User-Agent": "Mozilla/5.0"})
    js = urllib.request.urlopen(req, timeout=30).read().decode(errors="replace")
    print("JS len:", len(js))
    for m in re.finditer(r'[^;{}]{0,200}/api/request[^;{}]{0,400}', js):
        print("CTX:", m.group(0)[:550])
        print("===")
    # find field names near 'request' or 'body'
    for kw in ["walletAddress", "wallet_address", "recipient", "JSON.stringify({", "body: JSON"]:
        idx = js.find(kw)
        if idx >= 0:
            print(f"[{kw}] @{idx}:", js[max(0,idx-120):idx+300][:400])
            print("---")
except Exception as e:
    print("JS fetch err:", str(e)[:100])

# 2. test payloads
def post(payload, form=False):
    if form:
        import urllib.parse
        body = urllib.parse.urlencode(payload).encode()
        headers = {"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"}
    else:
        body = json.dumps(payload).encode()
        headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request("https://faucet.solana.com/api/request", data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read().decode(errors="replace")
            print(f"POST {payload} -> {r.status} {data[:200]}")
            return r.status, data
    except urllib.error.HTTPError as e:
        b = e.read().decode(errors="replace")[:200]
        print(f"POST {payload} -> HTTP {e.code} {b}")
        return e.code, b
    except Exception as e:
        print(f"POST {payload} -> ERR {str(e)[:100]}")
        return 0, str(e)

for p in [
    {"walletAddress": addr, "amount": 1000000000},
    {"wallet_address": addr, "amount": 1000000000},
    {"recipient": addr, "amount": 1000000000},
    {"address": addr, "amount": 1000000000, "network": "devnet"},
    {"wallet": addr, "network": "devnet"},
]:
    post(p)
    time.sleep(2)
post({"wallet": addr, "amount": "1"}, form=True)
