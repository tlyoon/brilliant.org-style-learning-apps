# Documentation maintenance policy

The documentation in this repository is versioned with the code. Users should read the documentation from the same `main` revision that they are running; copied instructions in email, chat, notes, or another PC may be obsolete.

## Canonical operational documents

The current operational documentation is:

- `docs/PDF_TO_APP_QUICKSTART.md` — normal installation and PDF-to-app workflow;
- `docs/WORKSTATION_SYNC.md` — workstation synchronization and machine-local state;
- `docs/GENERIC_PROJECT_SETUP.md` — recycling the package for another project;
- `docs/CONTINUOUS_AUTO_TESTING.md` — continuous auto-mode operation and multi-PC verification;
- `app_generator/README.md` — generator technical reference;
- `config/README.md` — project configuration reference.

`README.md` links users into these documents. Historical design notes and roadmaps are not substitutes for the current operational guides.

## Same-PR rule

A pull request that changes an operator-visible interface or lifecycle must update the relevant canonical documentation in the same pull request. This includes changes to:

- generator CLI commands, arguments, or selection modes;
- project configuration or project-derived paths;
- workstation synchronization or generated local configuration files;
- Google OAuth credential/token handling;
- managed or external coordinator setup, protocol, or recovery behavior;
- continuous-auto scheduling, publication, or completion behavior.

If such a code change does not require a wording change, the PR should still record that the documentation was reviewed and explain why it remains correct.

## CI documentation-impact gate

`python scripts/check_documentation_impact.py` is run by repository CI. When an operational surface changes, the gate requires at least one canonical operational document to change in the same commit range. Unit tests additionally check that the current CLI/configuration contract is represented in the documentation.

This gate does not prove that prose is perfect, but it prevents operational code from changing silently while all user instructions remain untouched.

## User rule: refresh code before trusting instructions

On an existing PC, refresh the remote view and synchronize `main` before following operating instructions:

```powershell
git switch main
git fetch origin
git status -sb
```

If the status shows `[behind N]`, update with:

```powershell
git pull --ff-only origin main
```

Then run:

```powershell
.\sync-workstation.cmd
```

After synchronization, read the documentation from that local checkout. The synchronizer prints the exact generated local configuration filename used on that PC; direct `app_generator` commands must use `--config <that-file>` when it is not the CLI default `project.local.toml`.

## Credentials are not documentation artifacts

OAuth client JSON files, OAuth tokens, administrator tokens, browser profiles, source PDFs, and run state remain outside Git. The repository documents where they belong, but never distributes their values.
