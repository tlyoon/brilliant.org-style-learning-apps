# Multi-PC job coordinator

This Apps Script web application serializes only the short job-claim/update operations. Gemini generation remains concurrent across worker PCs.

1. Create a private Google Sheet for the job ledger and copy its spreadsheet ID.
2. Create a standalone Apps Script project and paste `Code.gs` into it.
3. In **Project Settings → Script properties**, add:
   - `JOB_SPREADSHEET_ID`: the private ledger spreadsheet ID.
   - `PROJECT_NAME`: exactly the `project.project_name` value from the tracked project configuration.
   - `CHECKPOINT_FOLDER_ID`: the ID of a private Google Drive folder dedicated to recoverable auto-mode checkpoints. Do not use the source-PDF folder.
4. Run `initializeCoordinator` once in the Apps Script editor. It creates a random `WORKER_TOKEN` when absent and validates the ledger. Copy that generated property value to each authorized worker; never paste it into Git.
5. Deploy as a web app that executes as the owner. Restrict access as far as the account permits.
6. Copy the `/exec` deployment URL into `coordinator_url`.
7. On every worker PC, set the token only in the project-derived PowerShell environment variable. For the default project:

   ```powershell
   $env:BRILLIANT_CONTENT_GENERATOR_COORDINATOR_TOKEN = "the generated WORKER_TOKEN value"
   ```

Every request carries `project_name`; the coordinator rejects another project, and every ledger key is scoped by project. Do not place the token, spreadsheet ID, OAuth files, or Gemini session material in Git. The Apps Script uses `LockService` only while it atomically claims or updates a row. A time-limited lease and heartbeat recover jobs abandoned by a failed worker.

For an existing default-project deployment, `initializeCoordinator` recognizes only the exact legacy `BRILLIANT_WORKER_TOKEN` property and exact pre-project ledger header. It copies the token to `WORKER_TOKEN` and adds the configured `PROJECT_NAME` column without changing job states. This compatibility is scheduled for removal after 31 December 2026; verify the generic properties and new header before then.

## Continuous auto mode

The `auto` worker uses the same ledger and `LockService` claim boundary, but adds explicit `interrupted` and `generated` states plus durable parsed-stage checkpoints. A worker that loses its lease or exits during a leased job leaves that job recoverable. Claims are deterministic within the Drive inventory and prioritize: (1) interrupted work last owned by another PC, (2) never-attempted queued work, and (3) interrupted work last owned by the same PC. This lets a failed PC move on while another PC preferentially recovers the abandoned section.

Checkpoint files contain only parsed JSON generation stages associated with the exact `job_key` and `source_version`. They do not contain source PDFs, OAuth credentials, Chrome state, machine-local paths, diagnostics, or raw Gemini responses. The coordinator deletes the checkpoint after a job reaches `generated`.

After updating `Code.gs`, create the checkpoint folder, set `CHECKPOINT_FOLDER_ID`, save a new Apps Script deployment version, and update the web-app deployment before starting either PC in `auto` mode. `python -m app_generator doctor --selection-mode auto` verifies that the coordinator is reachable and that checkpoint storage is configured; it may reconcile expired leases and seed known local completions, but it does not claim a job.
