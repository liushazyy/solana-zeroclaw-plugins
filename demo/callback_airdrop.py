"""Step B: exchange OAuth code for session cookie, then airdrop + pay (overseas runner)."""
import json, sys, os, time, http.cookiejar, urllib.request, urllib.error

args = json.loads(os.environ["CALLBACK_ARGS"])
code = args["code"]
state = args["state"]
csrf_cookie = args["csrf_cookie"]  # full __Host-next-auth.csrf-token value
cb_url = args.get("cb_url", "https%3A%2F%2Ffaucet.solana.com")

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def set_cookie(name, value, domain="faucet.solana.com"):
    c = http.cookiejar.Cookie(0, name, value, None, False, domain, domain.startswith("."), domain.startswith("."),
                              "/", True, False, None, True, None, None, {})
    cj.set_cookie(c)

set_cookie("__Host-next-auth.csrf-token", csrf_cookie)
set_cookie("__Secure-next-auth.callback-url", cb_url)

def req(path, method="GET", data=None, headers=None):
    r = urllib.request.Request("https://faucet.solana.com" + path, method=method, data=data, headers=headers or {})
    return opener.open(r, timeout=30)

# 1. exchange code via callback
cb_path = f"/api/auth/callback/github?code={code}&state={state}"
try:
    resp = req(cb_path)
    print("CALLBACK:", resp.status, resp.geturl()[:120])
    print(resp.read().decode(errors="replace")[:200])
except urllib.error.HTTPError as e:
    print("CALLBACK HTTP:", e.code)
    print(e.read().decode(errors="replace")[:300])

# 2. verify session
try:
    resp = req("/api/auth/session")
    print("SESSION:", resp.read().decode(errors="replace")[:300])
except Exception as e:
    print("session err:", str(e)[:120])

# 3. airdrop
from solders.keypair import Keypair
kp = Keypair()
ADDR = str(kp.pubkey())
print("wallet:", ADDR)
body = json.dumps({"amount": 0.5, "walletAddress": ADDR, "network": "devnet"}).encode()
try:
    resp = req("/api/request", "POST", body, {"Content-Type": "application/json"})
    print("AIRDROP:", resp.status, resp.read().decode(errors="replace")[:300])
except urllib.error.HTTPError as e:
    print("AIRDROP HTTP:", e.code, e.read().decode(errors="replace")[:300])

time.sleep(10)
# 4. pay the shop URL with the funded wallet
import base64 as b64
from solders.pubkey import Pubkey
from solders.hash import Hash
from solders.system_program import transfer, TransferParams
from solders.instruction import Instruction, AccountMeta
from solders.message import Message
from solders.transaction import Transaction

RPC = "https://api.devnet.solana.com"
def rpc(method, params):
    b = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    rq = urllib.request.Request(RPC, data=b, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(rq, timeout=40) as r:
        return json.loads(r.read().decode())

bal = rpc("getBalance", [ADDR])
print("balance:", bal.get("result", {}).get("value", 0))
if bal.get("result", {}).get("value", 0) < 0.1e9:
    print("BALANCE_TOO_LOW")
    sys.exit(1)

REF = "D3YK5p4uJZQGwXtQv1K9HxNBe2AEVPbo7cQ8qWrS4mTn"
RECEIVER = "C7YH8TC2MgdQzFFG51RYVhYNCa8jfM6tCcErYaGkTcsB"
ref = Pubkey.from_string(REF)
receiver = Pubkey.from_string(RECEIVER)
bh = Hash.from_string(rpc("getLatestBlockhash", [])["result"]["value"]["blockhash"])
ix1 = transfer(TransferParams(from_pubkey=kp.pubkey(), to_pubkey=receiver, lamports=int(0.05*1e9)))
memo_prog = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")
ix2 = Instruction(program_id=memo_prog, data=b"solana-pay-reference", accounts=[AccountMeta(ref, False, False)])
msg = Message.new_with_blockhash([ix1, ix2], kp.pubkey(), bh)
tx = Transaction.new_unsigned(msg)
tx.sign([kp], bh)
sig = rpc("sendTransaction", [b64.b64encode(bytes(tx)).decode(), {"encoding":"base64", "preflightCommitment":"confirmed"}])
print("TX:", json.dumps(sig.get("result", sig.get("error"))))

time.sleep(12)
chk = rpc("getSignaturesForAddress", [REF, {"limit": 5}])
print("REF_SIGS:", json.dumps(chk.get("result"), indent=1)[:600])
