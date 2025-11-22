# Design: Fix IBKR Tickle CLI Instructions

## Overview
We will not modify the upstream IBKR gateway. Instead, we clarify our tooling and documentation so developers consistently probe the supported `/v1/api/tickle` endpoint and understand that `Access Denied` is the expected pre-auth signal.

## Key Points
1. **Diagnostics** – `check_ibkr_auth.sh` already shells out to `curl`. We simply interpret the response text: if it includes `Access Denied`, print an explicit reminder to log in via https://localhost:5055 before treating it as a failure.
2. **Documentation** – Add a troubleshooting subsection that:
   - Provides the exact `curl -k https://localhost:5055/v1/api/tickle` command.
   - Shows the two expected outputs (`Access Denied` before login, `{ "status": "ok" }` after login) and the steps to transition between them.
3. **Validation** – Because we cannot hit the gateway inside the sandbox, we describe the verification cadence (run curl, complete login, rerun) so contributors can follow the checklist locally.

No changes to Docker images or runtime networking are required.
