"""Faust recon: probe every known Solana devnet/testnet faucet endpoint from overseas network."""
import json, sys, time, urllib.request, urllib.error

def probe(name, url, method="GET", body=None, headers=None):
    try:
        req = urllib.request.Request(url, method=method, data=body, headers=headers or {})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = r.read().decode(errors="replace")
            print(f"[{name}] {r.status} | {r.geturl()} | {data[:200]}")
            return r.status, data
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:150]
        print(f"[{name}] HTTP {e.code} | {e.geturl()} | {body}")
        return e.code, body
    except Exception as e:
        print(f"[{name}] ERR {str(e)[:100]}")
        return 0, str(e)[:100]

from solders.keypair import Keypair
kp = Keypair()
addr = str(kp.pubkey())
print("probe wallet:", addr)

# 1. faucet.solana.com - where does it redirect?
probe("faucet.solana.com GET", "https://faucet.solana.com", headers={"User-Agent": "Mozilla/5.0"})
probe("faucet.solana.com/api/airdrop", "https://faucet.solana.com/api/airdrop", "POST",
      json.dumps({"address": addr, "amount": 1000000000}).encode(),
      {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})

# 2. quicknode faucet variants
for u in ["https://faucet.quicknode.com/solana/devnet", "https://faucet.quicknode.com/api/solana/devnet/airdrop"]:
    probe("quicknode " + u, u, "POST", json.dumps({"address": addr}).encode(), {"Content-Type": "application/json"})

# 3. RPC requestAirdrop on every endpoint with FRESH wallet
for u in ["https://api.devnet.solana.com", "https://api.testnet.solana.com", "https://devnet.rpcpool.com",
          "https://api.devnet.rpcpool.com", "https://solana-devnet.rpcpool.com", "https://api.testnet.rpcpool.com"]:
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":"requestAirdrop","params":[addr, 1000000000]}).encode()
    probe(f"rpc {u}", u, "POST", body, {"Content-Type": "application/json"})

# 4. other faucet services
probe("solfaucet.com", "https://solfaucet.com", headers={"User-Agent": "Mozilla/5.0"})
probe("faucet.metaplex.com", "https://faucet.metaplex.com", headers={"User-Agent": "Mozilla/5.0"})
probe("otter faucet", "https://faucet.otter.tech", headers={"User-Agent": "Mozilla/5.0"})
