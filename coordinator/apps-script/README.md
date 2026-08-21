# Multi-PC job coordinator

This Apps Script web application serializes only the short job-claim/update operations. Gemini generation remains concurrent across worker PCs.

1. Create a private Google Sheet for the job ledger and copy its spreadsheet ID.
2. Create a standalone Apps Script project and paste `Code.gs` into it.
3. In **Project Settings → Script properties**, add:
   - `JOB_SPREADSHEET_ID`: the private ledger spreadsheet ID.
   - `BRILLIANT_WORKER_TOKEN`: a long random value used only by the worker processes.
4. Deploy as a web app that executes as the owner. Restrict access as far as the account permits.
5. Copy the `/exec` deployment URL into `coordinator_url`.
6. On every worker PC, set the token only in the PowerShell environment:

   ```powershell
   $env:BRILLIANT_COORDINATOR_TOKEN = "the same long random value"
   ```

Do not place the token, spreadsheet ID, OAuth files, or Gemini session material in Git. The Apps Script uses `LockService` only while it atomically claims or updates a row. A time-limited lease and heartbeat recover jobs abandoned by a failed worker.
