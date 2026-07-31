"""Local-chain fallback demo: run solana-test-validator, airdrop is built-in, pay + verify."""
import json, os, sys, time, subprocess, base64 as b64, urllib.request

RPC = "http://127.0.0.1:8899"

def rpc(method, params):
    b = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req = urllib.request.Request(RPC, data=b, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode())

# start validator (binary downloaded by workflow)
proc = subprocess.Popen(["solana-test-validator", "--quiet"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(20)
try:
    print("health:", rpc("getHealth", []))

    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from solders.hash import Hash
    from solders.system_program import transfer, TransferParams
    from solders.instruction import Instruction, AccountMeta
    from solders.message import Message
    from solders.transaction import Transaction

    payer = Keypair()
    # local validator: any address can be airdropped via requestAirdrop
    a = rpc("requestAirdrop", [str(payer.pubkey()), 1000000000])
    print("airdrop:", json.dumps(a)[:150])
    time.sleep(3)

    REF = "D3YK5p4uJZQGwXtQv1K9HxNBe2AEVPbo7cQ8qWrS4mTn"
    RECEIVER = "C7YH8TC2MgdQzFFG51RYVhYNCa8jfM6tCcErYaGkTcsB"
    ref = Pubkey.from_string(REF)
    receiver = Pubkey.from_string(RECEIVER)
    bh = Hash.from_string(rpc("getLatestBlockhash", [])["result"]["value"]["blockhash"])
    ix1 = transfer(TransferParams(from_pubkey=payer.pubkey(), to_pubkey=receiver, lamports=int(0.05*1e9)))
    memo_prog = Pubkey.from_string("Memo1UhkJRfHyvLMcVucJwxXeuD728EqVDDwQDxFMNo")  # Memo v2: allows non-signer accounts
    ix2 = Instruction(program_id=memo_prog, data=b"solana-pay-reference", accounts=[AccountMeta(ref, False, False)])
    msg = Message.new_with_blockhash([ix1, ix2], payer.pubkey(), bh)
    tx = Transaction.new_unsigned(msg)
    tx.sign([payer], bh)
    sig = rpc("sendTransaction", [b64.b64encode(bytes(tx)).decode(), {"encoding":"base64", "preflightCommitment":"confirmed"}])
    print("TX:", json.dumps(sig.get("result", sig.get("error"))))

    time.sleep(15)
    chk = rpc("getSignaturesForAddress", [REF, {"limit": 5, "commitment": "confirmed"}])
    print("REF_SIGS:", json.dumps(chk.get("result"), indent=1)[:500])
    payer_sigs = rpc("getSignaturesForAddress", [str(payer.pubkey()), {"limit": 5, "commitment": "confirmed"}])
    print("PAYER_SIGS:", json.dumps(payer_sigs.get("result"), indent=1)[:400])
    print("LOCAL_DEMO_OK" if chk.get("result") else "LOCAL_DEMO_NO_SIG")
finally:
    proc.terminate()
