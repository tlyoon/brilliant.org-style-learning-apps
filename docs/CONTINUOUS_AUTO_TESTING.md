# Continuous auto mode manual test

This branch is intentionally an unmerged test candidate for multi-PC continuous generation.

## Preconditions

- PC A and PC B must check out the same `feature/continuous-auto-mode` commit.
- Both machines need working Google Drive OAuth, Gemini access, and the same coordinator URL/token.
- Update the Apps Script deployment with this branch's `coordinator/apps-script/Code.gs`.
- Create a private Drive folder for recoverable checkpoints and set its ID as the Apps Script `CHECKPOINT_FOLDER_ID` property.
- Do not use the source-PDF folder as checkpoint storage.

## Verify each PC

```powershell
git fetch origin
git switch feature/continuous-auto-mode
git pull --ff-only origin feature/continuous-auto-mode
git rev-parse HEAD
python -m app_generator run --help
python -m app_generator doctor --selection-mode auto
```

Both PCs must report the same commit SHA. The CLI help must expose `--selection-mode {specific,auto,distributed}`.

## Recovery test

1. On PC A, run:

   ```powershell
   python -m app_generator run --selection-mode auto
   ```

2. Let a fresh section progress through several generation stages, then stop the worker with `Ctrl+C`.
3. Allow the lease to be released/expire as applicable.
4. On PC B, run the auto doctor. The interrupted section should be preferred over untouched work.
5. Start auto mode on PC B. It should claim the interrupted section, restore durable parsed-stage checkpoints, skip already-completed generation stages, finish the section, and continue to the next globally available job.

## Concurrency test

Run auto mode simultaneously on both PCs. Active leases must never assign the same section to both machines. When all remaining work is leased by the other PC, a worker should poll rather than declare global completion. A normal zero exit is valid only when all discovered source jobs are globally successful; terminal failures block successful completion.

## Safety boundary

Shared checkpoints contain parsed generation-stage JSON only. They must not contain source PDFs, OAuth credentials, Chrome state, machine-local paths, diagnostics, or raw Gemini responses. Final content is installed only after validation succeeds.
