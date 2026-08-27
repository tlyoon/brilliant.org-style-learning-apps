# Multi-PC job coordinator

This Apps Script web application serializes only the short job-claim/update operations. Gemini generation remains concurrent across worker PCs.

1. Create a private Google Sheet for the job ledger and copy its spreadsheet ID.
2. Create a standalone Apps Script project and paste `Code.gs` into it.
3. In **Project Settings → Script properties**, add:
   - `JOB_SPREADSHEET_ID`: the private ledger spreadsheet ID.
   - `PROJECT_NAME`: exactly the `project.project_name` value from `config/project.toml`.
4. Run `initializeCoordinator` once in the Apps Script editor. It creates a random `WORKER_TOKEN` when absent and validates the ledger. Copy that generated property value to each authorized worker; never paste it into Git.
5. Deploy as a web app that executes as the owner. Restrict access as far as the account permits.
6. Copy the `/exec` deployment URL into `coordinator_url`.
7. On every worker PC, set the token only in the project-derived PowerShell environment variable. For the default project:

   ```powershell
   $env:BRILLIANT_CONTENT_GENERATOR_COORDINATOR_TOKEN = "the generated WORKER_TOKEN value"
   ```

Every request carries `project_name`; the coordinator rejects another project, and every ledger key is scoped by project. Do not place the token, spreadsheet ID, OAuth files, or Gemini session material in Git. The Apps Script uses `LockService` only while it atomically claims or updates a row. A time-limited lease and heartbeat recover jobs abandoned by a failed worker.
