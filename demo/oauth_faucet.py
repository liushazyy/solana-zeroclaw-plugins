"""Automated faucet.solana.com OAuth (GitHub) + airdrop via playwright, overseas runner. v2"""
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
    print("1 URL:", page.url)

    # find and click GitHub sign-in (NextAuth provider button)
    clicked = False
    for sel in ['a[href*="github"]', 'button:has-text("GitHub")', 'a:has-text("GitHub")',
                'button:has-text("Sign in with")', 'a:has-text("Sign in with")']:
        el = page.query_selector(sel)
        if el:
            print("clicking:", sel)
            el.click()
            clicked = True
            break
    if not clicked:
        # try /api/auth/providers to find github URL
        try:
            prov = page.evaluate("fetch('/api/auth/providers').then(r=>r.json())")
            print("providers:", json.dumps(prov)[:300])
            gh = prov.get("github", {})
            if gh.get("signinUrl"):
                page.goto(gh["signinUrl"], timeout=60000)
                clicked = True
        except Exception as e:
            print("providers err:", str(e)[:100])
    page.wait_for_timeout(4000)
    print("2 URL:", page.url)

    # GitHub login
    if page.query_selector('input[name="login"]'):
        print("github login page")
        page.fill('input[name="login"]', GH_EMAIL)
        page.fill('input[name="password"]', GH_PASS)
        page.click('input[type="submit"]')
        page.wait_for_timeout(6000)
        print("3 URL:", page.url)

    # device verification
    if page.query_selector('#otp') or "verified-device" in page.url:
        print("DEVICE_VERIFICATION_REQUIRED")
        otp = os.environ.get("GH_OTP", "")
        if otp:
            page.fill('#otp', otp)
            page.wait_for_timeout(4000)
            print("4 URL:", page.url)
        else:
            print("NEED_OTP")
            browser.close()
            sys.exit(3)

    # authorize
    if page.query_selector('button:has-text("Authorize")') or "login/oauth/authorize" in page.url:
        print("authorize page")
        page.click('button:has-text("Authorize")')
        page.wait_for_timeout(5000)
        print("5 URL:", page.url)

    # back to faucet, call /api/request
    page.goto("https://faucet.solana.com", timeout=60000)
    page.wait_for_timeout(3000)
    print("6 URL:", page.url)
    body = json.dumps({"amount": 0.5, "walletAddress": ADDR, "network": "devnet"})
    res = page.evaluate("""async (b) => {
        const r = await fetch('/api/request', {method:'POST', headers:{'Content-Type':'application/json'}, body: b});
        return {status: r.status, text: await r.text()};
    }""", body)
    print("AIRDROP:", json.dumps(res))
    browser.close()

# verify balance
import urllib.request
body = json.dumps({"jsonrpc":"2.0","id":1,"method":"getBalance","params":[ADDR]}).encode()
req = urllib.request.Request("https://api.devnet.solana.com", data=body, headers={"Content-Type":"application/json"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("BALANCE:", r.read().decode()[:200])
except Exception as e:
    print("balance err:", str(e)[:80])
