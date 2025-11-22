# Tasks

## 1. Diagnostics + Messaging
- [x] 1.1 Update `check_ibkr_auth.sh` to treat the `/v1/api/tickle` response as a formal health check, printing explicit instructions when it returns `Access Denied`.
- [x] 1.2 Add a short CLI snippet explaining the `/v1/api/tickle` command and Access Denied meaning to `docs/implementation/IBKR_AUTH_REQUIRED.md`.
- [x] 1.3 Mirror the same troubleshooting blurb in `docs/implementation/GATEWAY_FIX_SUMMARY.md` so both onboarding and fix guides stay aligned.

## 2. Validation
- [x] 2.1 Run/describe the manual `curl -k https://localhost:5055/v1/api/tickle` + login verification steps so readers know how to confirm the fix.
- [x] 2.2 Run `openspec validate fix-ibkr-tickle-cli-instructions --strict`.
