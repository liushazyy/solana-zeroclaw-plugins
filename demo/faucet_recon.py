"""Faust recon v2: dig faucet.solana.com JS for the real API route, try get.solana.com, re-probe RPCs."""
import json, sys, time, re, urllib.request, urllib.error

def probe(name, url, method="GET", body=None, headers=None):
    try:
        req = urllib.request.Request(url, method=method, data=body, headers=headers or {})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = r.read().decode(errors="replace")
            print(f"[{name}] {r.status} | {r.geturl()} | {data[:150]}")
            return r.status, data
    except urllib.error.HTTPError as e:
        b = e.read().decode(errors="replace")[:150]
        print(f"[{name}] HTTP {e.code} | {e.geturl()} | {b}")
        return e.code, b
    except Exception as e:
        print(f"[{name}] ERR {str(e)[:100]}")
        return 0, str(e)[:100]

from solders.keypair import Keypair
kp = Keypair()
addr = str(kp.pubkey())
print("wallet:", addr)

# 1. faucet.solana.com page JS -> find API route
st, html = probe("faucet.solana.com GET", "https://faucet.solana.com", headers={"User-Agent": "Mozilla/5.0"})
if st == 200:
    for m in re.finditer(r'/_next/static/[^"\']+\.js', html):
        js_url = "https://faucet.solana.com" + m.group(0)
        try:
            req = urllib.request.Request(js_url, headers={"User-Agent": "Mozilla/5.0"})
            js = urllib.request.urlopen(req, timeout=25).read().decode(errors="replace")
            routes = set(re.findall(r'["\'](/api/[^"\']+)["\']', js)) | set(re.findall(r'["\'](api/[^"\']+)["\']', js))
            if routes:
                print(f"JS {js_url} routes: {routes}")
        except Exception as e:
            print(f"js err {js_url}: {str(e)[:60]}")

# 2. get.solana.com faucet
probe("get.solana.com", "https://get.solana.com/faucet", headers={"User-Agent": "Mozilla/5.0"})
probe("get.solana.com api", "https://get.solana.com/api/faucet", "POST",
      json.dumps({"address": addr, "amount": 1000000000}).encode(),
      {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})

# 3. RPC airdrop re-probe (fresh wallet)
for u in ["https://api.devnet.solana.com", "https://api.testnet.solana.com"]:
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":"requestAirdrop","params":[addr, 1000000000]}).encode()
    probe(f"rpc {u}", u, "POST", body, {"Content-Type": "application/json"})

# 4. faucet.solana.com common routes
for path in ["/api/faucet", "/api/solana", "/api/airdrop/devnet", "/api/devnet", "/api/v1/airdrop"]:
    probe("fs " + path, "https://faucet.solana.com" + path, "POST",
          json.dumps({"address": addr, "amount": 1000000000}).encode(),
          {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
