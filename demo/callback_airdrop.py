"""Step B v8 (debug): full cookie/response visibility for the OAuth callback."""
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
        {"name": "__Host-next-auth.csrf-token", "value": csrf_cookie, "url": "https://faucet.solana.com"},
        {"name": "__Secure-next-auth.callback-url", "value": "https%3A%2F%2Ffaucet.solana.com", "url": "https://faucet.solana.com"},
    ])
    print("COOKIES_AFTER_SET:", json.dumps(ctx.cookies())[:300])
    page = ctx.new_page()

    # log all responses
    page.on("response", lambda r: print(f"RESP {r.status} {r.url[:120]}"))
    page.on("console", lambda m: print(f"CONSOLE: {m.text[:150]}"))

    page.goto("https://faucet.solana.com", timeout=45000)
    page.wait_for_timeout(4000)
    print("HOME:", page.url[:100])
    print("COOKIES_AT_HOME:", json.dumps(ctx.cookies())[:300])

    cb = f"https://faucet.solana.com/api/auth/callback/github?code={code}&state={state}"
    try:
        page.goto(cb, timeout=45000)
    except Exception as e:
        print("cb goto err:", str(e)[:100])
    page.wait_for_timeout(6000)
    print("URL:", page.url[:150])
    print("BODY:", page.inner_text("body")[:300].replace(chr(10), " | "))
    print("COOKIES_AFTER_CB:", json.dumps(ctx.cookies())[:400])

    sess = page.evaluate("fetch('/api/auth/session').then(r=>r.json()).catch(e=>({err:String(e)}))")
    print("SESSION:", json.dumps(sess)[:250])
    browser.close()

import urllib.request
body = json.dumps({"jsonrpc":"2.0","id":1,"method":"getBalance","params":[ADDR]}).encode()
req = urllib.request.Request("https://api.devnet.solana.com", data=body, headers={"Content-Type":"application/json"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("BALANCE:", r.read().decode()[:150])
except Exception as e:
    print("balance err:", str(e)[:60])
