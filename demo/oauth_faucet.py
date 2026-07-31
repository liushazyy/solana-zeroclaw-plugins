"""Automated faucet.solana.com OAuth (GitHub) + airdrop via playwright, overseas runner."""
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

    # 1. go to faucet, trigger GitHub sign-in
    page.goto("https://faucet.solana.com", timeout=60000)
    page.wait_for_timeout(3000)
    try:
        # NextAuth: look for sign-in link/button
        signin = page.query_selector('a[href*="/api/auth/signin"], button:has-text("Sign in"), a:has-text("Sign in")')
        if signin:
            print("found signin element, clicking")
            signin.click()
            page.wait_for_timeout(4000)
        else:
            # direct to signin page
            print("no signin element, going direct")
            page.goto("https://faucet.solana.com/api/auth/signin", timeout=60000)
            page.wait_for_timeout(3000)
    except Exception as e:
        print("signin nav err:", str(e)[:100])

    print("URL now:", page.url)

    # 2. GitHub login if redirected to github.com/login
    if "github.com/login" in page.url or page.query_selector('input[name="login"]'):
        print("on github login page")
        page.fill('input[name="login"]', GH_EMAIL)
        page.fill('input[name="password"]', GH_PASS)
        page.click('input[type="submit"]')
        page.wait_for_timeout(6000)
        print("after login URL:", page.url)
        # device verification may appear
        if "verified-device" in page.url or page.query_selector('#otp'):
            print("DEVICE_VERIFICATION_REQUIRED - page:", page.url)
            # wait for user-provided OTP via env (set on re-run) - just report
            otp = os.environ.get("GH_OTP", "")
            if otp:
                page.fill('#otp', otp)
                page.wait_for_timeout(4000)
                print("OTP submitted, URL:", page.url)
            else:
                print("NEED_OTP")
                browser.close()
                sys.exit(3)

    # 3. authorize the app
    if "github.com/login/oauth/authorize" in page.url or page.query_selector('button:has-text("Authorize")'):
        print("on authorize page")
        page.click('button:has-text("Authorize")')
        page.wait_for_timeout(5000)
        print("after authorize URL:", page.url)

    # 4. back on faucet - call /api/request from page context (same cookies)
    page.goto("https://faucet.solana.com", timeout=60000)
    page.wait_for_timeout(3000)
    print("final URL:", page.url)
    body = json.dumps({"amount": 0.5, "walletAddress": ADDR, "network": "devnet"})
    res = page.evaluate("""async (b) => {
        const r = await fetch('/api/request', {method:'POST', headers:{'Content-Type':'application/json'}, body: b});
        return {status: r.status, text: await r.text()};
    }""", body)
    print("AIRDROP:", json.dumps(res))

    # save cookies for a follow-up run if needed
    cookies = ctx.cookies()
    with open("faucet_cookies.json", "w") as f:
        json.dump(cookies, f)
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
