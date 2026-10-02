# Drive-native auto coordination

## Purpose

Continuous `auto` mode coordinates multiple generator PCs without Google Apps Script, a Google Sheet, or a Google Cloud coordinator deployment. The shared Google Drive source tree itself carries a small append-only coordination log.

The default project setting is:

```toml
[automation]
coordination_backend = "drive"
```

`distributed` mode and legacy coordinator administration commands remain available for compatibility; they are not on the normal auto-mode path.

## Shared state location

Coordination marker/event files are written directly into the existing Google Drive subchapter folder beside that topic's PDFs. No shared coordinator folder has to be created, so simultaneous first runs on multiple PCs have no container-bootstrap race. Drive `appProperties` identify the project, event kind, corpus job key, and attempt where applicable.

Source PDFs remain untouched. Marker names are unique and are not used as locks. No generated package, credential, OAuth token, browser profile, or raw Gemini response is written into coordination state.

## Job identity

Auto coordination uses the complete PDF corpus for a subchapter, not only `source.pdf`. The corpus is the anchor `source.pdf` plus all eligible sibling PDFs in that topic folder. Its job key is derived from every Drive file ID and source version.

Consequences:

- changing `source.pdf` creates a new job identity;
- changing, adding, or replacing a supplementary PDF creates a new job identity;
- checkpoints from an older corpus cannot be restored into the new corpus;
- historical marker files can remain in Drive without affecting the current job.

## Claim creation and deterministic election

Every worker that wants a job creates its own uniquely named `claim` JSON marker with a UUID attempt ID. File-name uniqueness is not used as a lock because Google Drive permits duplicate names.

After creating a claim, the worker lists active claims twice with a short settling delay. The elected owner is the claim with the earliest Drive server `createdTime`; Drive file ID is the deterministic tie-breaker. A losing worker deletes only its own claim and tries another eligible job.

## Lease fencing and heartbeat

The winning claim file ID is the fencing token. Before heartbeat-sensitive operations, the worker re-lists active claims and must still be the elected winner.

Lease age is determined from Google Drive server timestamps: the HTTP `Date` header supplies server time and the claim file's Drive `modifiedTime` supplies its last heartbeat. Local PC clocks do not decide ownership.

A heartbeat first proves the claim is still active and elected, then updates the winning claim. An already expired claim is therefore rejected before update and cannot be resurrected. If the claim is missing, expired, or loses election, `LeaseLostError` stops the worker from publishing stale work.

The existing background `LeaseGuard` remains the fail-closed watchdog. The Drive client implements the same `heartbeat()` behavior expected by that guard.

## Append-only checkpoints

Parsed generation stages are stored as `checkpoint` event files. Operations are `save`, `delete`, and `clear`; no shared checkpoint file is overwritten. Recovery replays events in Drive `createdTime`/file-ID order to reconstruct the latest valid stage map.

Checkpoint history belongs to the job identity, not to one PC. A new worker attempt can therefore recover valid parsed stages left by an earlier failed attempt. Raw Gemini responses remain only in local run state and are never uploaded as Drive checkpoints.
## Failure, interruption, and retry

When a leased run fails, the worker writes a durable `failure` event containing the attempt ID, attempt count, worker ID, error code, and bounded error message, then releases its live claim when possible. A crashed machine may leave an expired claim; expiry alone is sufficient for another worker to proceed.

A job with previous attempts but remaining attempt budget is `interrupted` and is preferred over untouched queued work. Once `max_job_attempts` is exhausted, it becomes terminal `failed` and ordinary auto mode stops treating it as runnable.

The existing operator command remains available:

```powershell
python -m app_generator coordinator-retry-failed --config .\project.local.toml --pdf-subchapter-path 8.2 --confirm
```

For the Drive backend this writes a `retry` reset event. Earlier attempt/failure history is retained for diagnosis, while the effective attempt budget after the reset starts again from zero.

## Durable success and Git handoff

Drive success is written only after the validated package has completed its configured Git publication path. A `success` marker therefore means the generated result has a durable shared handoff, not merely local files on one PC.

Before opening Gemini, auto still checks deterministic recoverable Git handoffs. If a previous PC pushed a valid branch/PR but crashed before recording success, the next worker claims the exact job, completes Git reconciliation, records success, and skips Gemini regeneration.

When `public_deploy` is enabled, success is delayed until the deterministic public GitHub Pages review PR has also merged. A source package already present in `main` is therefore not treated as globally complete by itself: the next worker claims it, skips Gemini, and finishes/reuses the public branch/PR. The success marker includes public branch, PR URL, route URL, and package digest for diagnostics.

## Stall supervision and resume

Each normal continuous-auto generation attempt runs in a supervised child process. By default the parent checks meaningful run-state activity every 600 seconds; after 600 seconds without activity, three consecutive stale checks terminate that child. Lease heartbeats intentionally do not reset this counter. The parent remains alive to reconcile the queue.

The supervisor first requests termination and gives the child a bounded grace period before a hard kill where the platform supports it. On Windows a hard kill can be unavoidable. It never clears Drive checkpoints: another worker reclaims after lease expiry and restores the last durable parsed-stage checkpoint. Resume is from the last parsed stage, not from a mid-token model response.
## Google Drive authorization

Drive-native coordination creates and updates files, so the generator now requests writable Google Drive OAuth access instead of the earlier read-only scope. An existing token that does not contain the writable scope is discarded in memory and the normal installed-app authorization flow asks the operator to authorize again; the refreshed token remains machine-local.

This is a one-time scope migration per workstation. It does not change the independently configured Gemini browser account.

## Multi-PC behavior

If several PCs start together, each independently discovers the same source inventory and may briefly create a claim for the same first job. Deterministic election selects one winner. Losing workers discard their own claims and continue to other eligible sections, so useful work naturally spreads across PCs.

If a winner crashes, its `modifiedTime` stops advancing. After `lease_seconds`, that claim is no longer active and another worker can create a new attempt. If the old PC later reconnects, its expired claim fails the ownership check and cannot publish.

Targeted auto uses exactly the same mechanism but filters inventory to the requested section. It waits rather than falling through to another section when the target is owned elsewhere.

Chapter-scoped auto (`--chapter 10`) filters the shared inventory to exact `10.*` section IDs while retaining normal multi-PC lease election. Workers may take several sections from that chapter but cannot claim another chapter, and they exit when that chapter's scoped queue is globally successful.

Each workstation is also bound locally to one PC hostname and one absolute repository checkout through `workstation-sync.toml`; the rendered local generator config repeats that binding. This prevents a Yoga6 process, for example, from accidentally using a Dell-115 checkout simply because both folders are visible through a synchronized drive.

## Operational commands

Normal auto operation no longer needs `coordinator-bootstrap`, `coordinator-ensure`, a worker coordinator token, or an Apps Script URL. Existing coordinator administration commands are retained only for legacy cloud/distributed operation.
