# Fix IBKR Tickle CLI Instructions

## Why
Developers keep running `curl -k https://localhost:5055/tickle` and interpreting the `Access Denied` response as a gateway failure. The Client Portal Gateway only exposes the supported `/v1/api/tickle` health endpoint and intentionally returns `Access Denied` until the user logs in through https://localhost:5055. Without explicit guidance in the troubleshooting docs and tooling, engineers waste time chasing a non-issue and think the gateway is broken.

## What Changes
- Document the correct versioned tickle endpoint and explicitly describe that `Access Denied` indicates "gateway up but not authenticated".
- Update the `check_ibkr_auth.sh` diagnostics so the tickle probe surfaces actionable messaging instead of silently printing the raw Access Denied string.
- Ensure our gateway verification guides reference the updated command and remediation steps.

## Impact
- Specs: `ibkr-auth`
- Code/docs: `check_ibkr_auth.sh`, `docs/implementation/IBKR_AUTH_REQUIRED.md`, `docs/implementation/GATEWAY_FIX_SUMMARY.md`
