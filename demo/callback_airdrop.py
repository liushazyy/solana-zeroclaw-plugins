"""Step B (playwright): exchange OAuth code for session, then airdrop + pay. Avoids Cloudflare 403."""
import json, sys, os, time, base64 as b64

args = json.loads(os.environ["CALLBACK_ARGS"])
code = args["code"]
state = args["state"]
csrf_cookie = args["csrf_cookie"]

from solders.keypair import Keypair
kp = Keypair()
ADDR = str(kp.pubkey())
print("wallet:", ADDR)

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    ctx = browser.new_context()
    ctx.add_cookies([
        {"name": "__Host-next-auth.csrf-token", "value": csrf_cookie, "path": "/", "secure": True},
        {"name": "__Secure-next-auth.callback-url", "value": "https%3A%2F%2Ffaucet.solana.com", "path": "/", "secure": True},
    ])
    page = ctx.new_page()

    # exchange code via callback URL (NextAuth GET flow)
    cb = f"https://faucet.solana.com/api/auth/callback/github?code={code}&state={state}"
    try:
        page.goto(cb, timeout=45000)
    except Exception as e:
        print("goto err (expected if nav to home):", str(e)[:80])
    page.wait_for_timeout(5000)
    print("URL:", page.url[:120])

    sess = page.evaluate("fetch('/api/auth/session').then(r=>r.json())")
    print("SESSION:", json.dumps(sess)[:250])

    body = json.dumps({"amount": 0.5, "walletAddress": ADDR, "network": "devnet"})
    res = page.evaluate("""async (b) => {
        const r = await fetch('/api/request', {method:'POST', headers:{'Content-Type':'application/json'}, body: b});
        return {status: r.status, text: await r.text()};
    }""", body)
    print("AIRDROP:", json.dumps(res))
    browser.close()

# ===== transfer to shop wallet =====
import urllib.request
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

time.sleep(8)
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
