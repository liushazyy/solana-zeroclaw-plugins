"""Step A: fetch faucet.solana.com NextAuth csrf token + cookie (overseas runner)."""
import json, sys, http.cookiejar, urllib.request

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
req = urllib.request.Request("https://faucet.solana.com/api/auth/csrf", headers={"User-Agent": "Mozilla/5.0"})
resp = opener.open(req, timeout=30)
data = json.loads(resp.read().decode())
print("CSRF:", json.dumps(data))
cookies = [{"name": c.name, "value": c.value, "domain": c.domain, "path": c.path} for c in cj]
print("COOKIES:", json.dumps(cookies))
