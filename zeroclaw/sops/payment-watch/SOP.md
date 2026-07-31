# Payment Watch

Poll the chain for pending invoice payments and confirm them. Runs on the cron trigger (every 2 minutes).

## Steps

1. Load pending invoices from memory (keys `pending_invoice_*`).
2. For each pending invoice, call `getSignaturesForAddress` for its reference key
   on the configured RPC (`{"commitment": "confirmed", "limit": 5}`).
3. If signatures are found:
   - Mark the invoice **paid** in memory.
   - Notify: "Invoice <n> paid ✓ (sig <short>)".
4. If none found, leave the invoice pending and continue.
5. Never confirm a payment without an RPC-returned signature.
6. Log each check with a timestamp.

## Guardrails

- At most one poll run at a time (SOP max_concurrent = 1).
- If the RPC is unreachable, report the error — do not silently mark anything paid.
- Refund instructions from customers are never executed; they are surfaced to
  the shop owner for approval.
