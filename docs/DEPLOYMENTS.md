# Deployment registry

Public deployments are tracked in:

```text
config/deployments.json
```

The registry is the repository-owned record of public app routes. Publication eligibility is determined by automated repository validation and configured deployment checks; package status remains metadata.

## List deployments

From the repository root:

```powershell
python -m app_generator deployments
```

The command does not require `project.local.toml`, Google Drive credentials, coordinator access, or a browser. It compares the tracked registry with generated packages under:

```text
content/chapter-*/section-*/package.json
```

and prints:

- app label;
- whether the referenced package exists in the checkout;
- whether the registry marks the app deployed;
- public URL.

Generated packages that are not represented in the registry are appended automatically with `DEPLOYED = no` and URL `-`. This prevents a newly generated section from being hidden merely because deployment metadata has not been added yet.

## Registry entry

Each deployment has the form:

```json
{
  "appId": "section-8-2",
  "label": "Section 8.2",
  "packagePath": "content/chapter-8/section-8-2/package.json",
  "deploymentRepository": "tlyoon/section-8-1-learning-app",
  "publicUrl": "https://tlyoon.github.io/section-8-1-learning-app/section-8-2/",
  "deployed": true
}
```

Optional `variant` text may distinguish multiple routes backed by the same section package, such as historical and regenerated review variants.

New automatic review deployments also record optional `packageSha256`, the SHA-256 of the exact `package.json` bundled for Pages. Older records without it remain readable, but an auto worker treats them as insufficient proof that its current package reached Pages. The Drive success event also records the public PR/URL/digest for cross-PC reconciliation.

## Automatic public deployment

This project's enabled policy uses `tlyoon/section-8-1-learning-app` and routes a section as `section-{section_slug}/` (for example, `9.1` is `section-9-1/`). Workers build only the minimal static bundle, open/reuse a deterministic package-digest branch and PR in that public repository, and merge it automatically. Source PDFs, Drive marker data, run state, raw model responses, credentials, and source manifests never enter that repository. Automated validation and configured deployment checks are the publication gate; manual review is optional.

### Direct links to activities

Every rendered activity has a stable deep link using its package activity ID:

```text
https://<pages-route>/?activity=<activity-id>
```

For example, `.../section-9-5/?activity=act-int-mod-1` opens that exact interactive activity rather than starting at Activity 1. The player updates the `activity` query parameter as the learner advances, preserves unrelated query parameters and URL fragments, and falls back safely to the first activity if an unknown ID is supplied.

## Maintenance rule

When a public route is created, changed, or removed, update `config/deployments.json` in the same source-repository PR that records/authorizes that deployment. Keep only public, non-secret deployment metadata in the registry.

A deployment entry records operational publication state. Content quality remains governed by the automated validation and provenance checks in the generation pipeline; optional manual review remains separate.
