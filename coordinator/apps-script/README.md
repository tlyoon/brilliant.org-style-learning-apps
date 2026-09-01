# Multi-PC job coordinator

The coordinator is now **repository-managed infrastructure** by default. Worker PCs do not copy `Code.gs`, create Script Properties, deploy Apps Script, or distribute `WORKER_TOKEN` manually.

The Apps Script web application still serializes only short job-claim/update operations. Gemini generation remains concurrent across worker PCs.

## Managed mode (default)

Managed mode is selected when `coordinator_url` is empty. The repository owns:

- `coordinator/apps-script/Code.gs` and `appsscript.json`;
- the required coordinator protocol version;
- an idempotent Google deployment program in `coordinator/deployment/manage.py`;
- a serialized GitHub Actions workflow in `.github/workflows/ensure-coordinator.yml`.

A single **one-time bootstrap** on one authorized workstation is required for a new project:

```powershell
python -m app_generator coordinator-bootstrap
```

The bootstrap:

1. opens Google authorization for the additional coordinator-administration scopes;
2. verifies that the authorized Google account matches the project's configured `login_name`;
3. stores the refreshable administrator credential directly in the private GitHub Actions secret `COORDINATOR_ADMIN_TOKEN_JSON` using the authenticated GitHub CLI;
4. requests the serialized `Ensure managed coordinator` workflow;
5. waits for the managed runtime to appear in the authorized Google Drive account;
6. verifies the actual deployed web app with a live `health` request before reporting success.

The Google credential, worker token, source PDFs, and Gemini session material never enter Git.

The GitHub Actions deployment creates or reuses project-scoped resources identified by Drive `appProperties`:

- a private Google Sheet job ledger;
- a private Drive checkpoint folder;
- an Apps Script project;
- one managed web-app deployment;
- a private `learning-app-coordinator-runtime.json` Drive record containing the runtime URL/token/resource IDs.

Normal worker OAuth remains Drive-readonly. Each PC discovers the private runtime record, injects the worker token only into its current process environment, and verifies live coordinator health before any queue operation.

### Simultaneous PCs

PC A and PC B may both discover that the coordinator is missing, stale, or unhealthy. Both may request the same workflow. GitHub Actions uses the project-scoped concurrency group:

```text
managed-coordinator-<project_name>
```

with `cancel-in-progress: false`, so privileged deployments are serialized. The deployer is idempotent and converges repeated requests on the same project-scoped resources. Worker generation does not begin until live health succeeds.

Useful lifecycle commands are:

```powershell
python -m app_generator coordinator-status
python -m app_generator coordinator-ensure
python -m app_generator coordinator-bootstrap   # first project setup only
```

`doctor` and `run` automatically call the same ensure/health gate when a coordinated selection mode is active.

## Continuous auto mode

The `auto` worker uses the coordinator ledger and Apps Script `LockService` claim boundary with explicit `queued`, `interrupted`, `leased`, `generated`, `review_pending`, `completed`, and terminal `failed` states. A worker that loses its lease or exits during a leased job leaves that job recoverable.

Claims are deterministic within the Drive inventory and prioritize: (1) interrupted work last owned by another PC, (2) never-attempted queued work, and (3) interrupted work last owned by the same PC. This lets a failed PC move on while another PC preferentially recovers the abandoned section.

Checkpoint files contain only parsed JSON generation stages associated with the exact `job_key` and `source_version`. They do not contain source PDFs, OAuth credentials, Chrome state, machine-local paths, diagnostics, or raw Gemini responses. The coordinator deletes the checkpoint after a job reaches `generated`.

## Existing externally managed coordinators

Backward compatibility is retained. If `coordinator_url` contains an explicit Apps Script `/exec` URL, the generator treats that deployment as external and does not try to replace it through GitHub Actions. The existing project-derived coordinator-token environment variable remains supported for that path.

For an older default-project deployment, `initializeCoordinator` still recognizes the exact legacy `BRILLIANT_WORKER_TOKEN` property and exact pre-project ledger header. It copies the token to `WORKER_TOKEN` and adds the configured `PROJECT_NAME` column without changing job states. This migration compatibility is scheduled for removal after 31 December 2026.

## Google platform prerequisite

The Google Cloud project behind the Desktop OAuth client must have the Google Drive API and Apps Script API enabled. This is a platform/API prerequisite; it is not a per-PC or per-upgrade Apps Script provisioning step. If Apps Script API access is disabled, `coordinator-bootstrap` or the GitHub deployment workflow fails safely instead of publishing a usable runtime record.
