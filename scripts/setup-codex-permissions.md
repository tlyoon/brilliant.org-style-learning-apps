# Set Up Codex Permissions on This PC

Use this prompt after cloning this repository onto another Windows PC. Open
Codex in the repository, then ask it to read this file and carry out the
instructions.

## Instructions for Codex

Configure this PC's user-level Codex permissions as follows.

1. Locate the active Codex home directory. On Windows, it is normally
   `%USERPROFILE%\.codex`.

2. Inspect these existing files before changing anything:

   - `<Codex home>\config.toml`
   - `<Codex home>\rules\default.rules`

3. Back up every existing file that will be changed to a timestamped temporary
   directory. Report the backup location.

4. Merge the following settings into `config.toml`. Preserve unrelated
   settings and existing TOML tables, and do not create duplicate keys:

   ```toml
   approval_policy = "on-request"
   approvals_reviewer = "auto_review"
   sandbox_mode = "workspace-write"

   [sandbox_workspace_write]
   network_access = true
   ```

5. If this repository's learning-app content generator is present, determine the
   current Windows user's local run-artifact directory and add that absolute
   directory to `sandbox_workspace_write.writable_roots`. The expected location
   is under the project-derived `paths.state_dir` rendered from `config/project.toml`. Do not copy a
   username or absolute path from another PC.

6. Remove any existing rule that broadly allows `pattern=["git", "push"]`,
   because that prefix can also match force-push variants. Then merge these
   narrow rules into `rules\default.rules`. Create the directory or file if
   necessary, preserve unrelated rules, and do not add duplicates:

   ```python
   prefix_rule(pattern=[".\\.venv\\Scripts\\python.exe", "-m", "app_generator", "run"], decision="allow", justification="Allow this project's generator command")
   prefix_rule(pattern=["git", ["status", "diff", "log", "show", "rev-parse"]], decision="allow", justification="Allow read-only Git inspection")
   prefix_rule(pattern=["gh", "pr", ["view", "checks", "status", "list"]], decision="allow", justification="Allow read-only GitHub pull-request inspection")
   prefix_rule(pattern=["git", "add"], decision="allow", justification="Allow staging repository changes")
   prefix_rule(pattern=["git", "commit"], decision="allow", justification="Allow creating local commits")
   prefix_rule(pattern=["git", "fetch"], decision="allow", justification="Allow fetching remote Git references")
   prefix_rule(pattern=["git", "pull", "--ff-only"], decision="allow", justification="Allow fast-forward-only pulls")
   prefix_rule(pattern=["git", "ls-remote"], decision="allow", justification="Allow inspecting remote Git references")
   prefix_rule(pattern=["git", "push"], decision="prompt", justification="Review every remote push; force pushes must never run automatically")
   prefix_rule(pattern=["git", ["rebase", "reset", "clean"]], decision="prompt", justification="Review history-rewriting or destructive Git operations")
   prefix_rule(pattern=["git", "branch", "-D"], decision="prompt", justification="Review forced branch deletion")
   ```

7. Keep the safety boundary narrow:

   - Do not set `approval_policy = "never"`.
   - Do not set `sandbox_mode = "danger-full-access"`.
   - Do not add broad PowerShell, Python, shell, deletion, package-installation,
     deployment, or unrestricted filesystem rules.
   - Keep all pushes, rebases, resets, cleans, forced branch deletions, and
     other destructive history operations approval-gated.
   - Do not read, copy, print, or modify credentials or authentication tokens.

8. Validate the resulting TOML and all listed execution rules. Show the exact
   diff and validation results, then tell the user to restart Codex so the
   configuration and rules are reloaded.

Writing to the user-level Codex directory may require one initial approval on a
new PC. This prompt does not bypass that approval.

## Reference

- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
- [Codex auto-review](https://learn.chatgpt.com/docs/sandboxing/auto-review)
- [Codex execution rules](https://learn.chatgpt.com/docs/agent-configuration/rules)
