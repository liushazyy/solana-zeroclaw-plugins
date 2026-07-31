# Payment Watch

Check all pending invoices and confirm payments.

## Steps

1. Load the list of pending invoices from memory (keys: `pending_invoice_*`).
2. For each pending invoice, call `getSignaturesForAddress` on the reference key via `https://devnet.rpcpool.com`.
3. If the result is non-empty, mark the invoice as paid in memory and reply in the channel: "Invoice <message> paid ✓"
4. If the result is empty, leave the invoice pending.
5. Report a compact summary of checked invoices.
