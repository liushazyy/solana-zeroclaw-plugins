"""Automated faucet.solana.com OAuth (GitHub) + airdrop via playwright, overseas runner. v3: proper OTP verify + authorize."""
import json, os, sys, time

GH_EMAIL = os.environ.get("GH_EMAIL", "")
GH_PASS = os.environ.get("GH_PASS", "")

from solders.keypair import Keypair
kp = Keypair()
ADDR = str(kp.pubkey())
print("wallet:", ADDR)

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    ctx = browser.new_context()
    page = ctx.new_page()

    page.goto("https://faucet.solana.com", timeout=60000)
    page.wait_for_timeout(3000)
    print("1:", page.url)

    clicked = False
    for sel in ['a[href*="github"]', 'button:has-text("GitHub")', 'a:has-text("GitHub")',
                'button:has-text("Sign in with")', 'a:has-text("Sign in with")']:
        el = page.query_selector(sel)
        if el:
            print("click:", sel)
            el.click()
            clicked = True
            break
    page.wait_for_timeout(5000)
    print("2:", page.url)

    if page.query_selector('input[name="login"]'):
        print("github login")
        page.fill('input[name="login"]', GH_EMAIL)
        page.fill('input[name="password"]', GH_PASS)
        page.click('input[type="submit"]')
        page.wait_for_timeout(8000)
        print("3:", page.url)

    if page.query_selector('#otp') or "verified-device" in page.url:
        print("device verification page")
        otp = os.environ.get("GH_OTP", "")
        if otp:
            page.fill('#otp', otp)
            page.wait_for_timeout(1000)
            # click Verify button or submit
            btn = page.query_selector('button:has-text("Verify")') or page.query_selector('input[type="submit"]')
            if btn:
                print("clicking verify")
                btn.click()
            else:
                page.keyboard.press("Enter")
            # wait for redirect back to authorize or faucet
            for i in range(10):
                page.wait_for_timeout(3000)
                print(f"  wait{i} url:", page.url[:90])
                if "verified-device" not in page.url:
                    break
        else:
            print("NEED_OTP")
            browser.close()
            sys.exit(3)

    # authorize if presented
    for i in range(5):
        if page.query_selector('button:has-text("Authorize")') or "login/oauth/authorize" in page.url:
            print("authorize page")
            page.click('button:has-text("Authorize")')
            page.wait_for_timeout(6000)
            print("after authorize:", page.url)
            break
        page.wait_for_timeout(3000)

    # confirm session then call /api/request
    sess = page.evaluate("fetch('/api/auth/session').then(r=>r.json())")
    print("SESSION:", json.dumps(sess)[:200])
    page.goto("https://faucet.solana.com", timeout=60000)
    page.wait_for_timeout(3000)
    body = json.dumps({"amount": 0.5, "walletAddress": ADDR, "network": "devnet"})
    res = page.evaluate("""async (b) => {
        const r = await fetch('/api/request', {method:'POST', headers:{'Content-Type':'application/json'}, body: b});
        return {status: r.status, text: await r.text()};
    }""", body)
    print("AIRDROP:", json.dumps(res))
    browser.close()

# ===== now pay the shop's Solana Pay URL with the same funded wallet =====
import urllib.request, urllib.parse, base64 as b64
from solders.pubkey import Pubkey
from solders.hash import Hash
from solders.system_program import transfer, TransferParams
from solders.instruction import Instruction, AccountMeta
from solders.message import Message
from solders.transaction import Transaction

RPC = "https://api.devnet.solana.com"
def rpc(method, params):
    b = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req = urllib.request.Request(RPC, data=b, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode())

# wait for airdrop confirmation
time.sleep(10)
bal = rpc("getBalance", [ADDR])
print("balance:", bal.get("result", {}).get("value", 0))
if bal.get("result", {}).get("value", 0) < 0.1e9:
    print("BALANCE_TOO_LOW - airdrop may not have landed")
    sys.exit(1)

REF = "D3YK5p4uJZQGwXtQv1K9HxNBe2AEVPbo7cQ8qWrS4mTn"
RECEIVER = "C7YH8TC2MgdQzFFG51RYVhYNCa8jfM6tCcErYaGkTcsB"
ref = Pubkey.from_string(REF)
receiver = Pubkey.from_string(RECEIVER)
amount = 0.05
print("paying", amount, "SOL to", RECEIVER, "ref", REF)

bh = Hash.from_string(rpc("getLatestBlockhash", [])["result"]["value"]["blockhash"])
ix1 = transfer(TransferParams(from_pubkey=kp.pubkey(), to_pubkey=receiver, lamports=int(amount*1e9)))
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
