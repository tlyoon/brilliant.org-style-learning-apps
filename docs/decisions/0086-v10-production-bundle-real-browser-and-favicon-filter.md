# Decision 0086 — Real Chrome acceptance of private V9 release bundles (BSA230)

**20 November 2026, owner Yoga6, autonomous v7.1 continuation.**

## Historical evidence and actual failure

BSA229 genuinely staged three eight-file production release bundles
for public Pages routes 9.1, 9.2 and 9.6 in owner-private LOCALAPPDATA,
with exact V7/V8 source-bound HMAC release evidence, immutable SHA
manifest and pinned public main. GitHub CI passed at source
`3ac86d08e75a00e8f411413833bb98b50ac78c2f`;
ordinary source-free normal worker EXIT0 and V9 integrity receipt
`7d1852ecc8a6aa5f595e589b0125424dd7d09dae0f5aeb1a78e8b2eea01ba743`.
No public PR, push, merge or deployment occurred.

The first **actual local Selenium 4.47 Chrome smoke** served each
V9 route from loopback HTTP. All three routes returned 200 on the
index, app.js, styles, domain renderers, visual renderers, and genuine
package bytes, and each showed a real learner UI with seven buttons.
Section 9.1 logged two browser SEVERE messages for the missing sitewide
`http://127.0.0.1:<ephemeral-port>/favicon.ico` only, HTTP 404;
sections 9.2 and 9.6 logged zero severe errors. The first probe
incorrectly rejected all real page acceptance because it treated
those harmless favicon requests as application failures.

A historical source search found existing broader runtime browser
audit/error sanitation, but no reusable exact favicon filter. BSA230
adds the narrowly bounded repair to the **normal executable worker**,
not just its scratch smoke script.

## Automated V10 boundary

After genuine V9 on the same source-free invocation, invoke
`run_private_release_browser_acceptance`. It must recheck exact clean
GitHub head CI, immutable signed source-bound V9 receipt, all 24 local
bundle file SHA values and three exact package hashes, then run a real
headless Selenium Chrome session against loopback-only served
production bundles 9.1/9.2/9.6. Verify actual DOM learner content,
interactive buttons and that every route loaded, not an initial or
error placeholder. Only match the **exact localhost favicon.ico 404**
console text as benign. Wrong status, wrong host/path, app.js 404,
JavaScript exceptions and any other SEVERE event block acceptance.

Write an immutable V10 integrity receipt only after all three
real browser sessions pass and the HTTP server and Chrome resources
are properly released. No model or PDF calls, private review
replay, public push, PR, merge, or deployment. Production artifacts
remain in private storage. Any interrupted restart must validate
the existing V10 receipt for exact consistency.

## Verification and next work

Synthetic and fault-injection tests must demonstrate the exact
favicon-only exception, true JS/resource failure detection, source
and manifest corruption rejection and automatic V9→V10 dispatch.
Genuine owner Yoga6 normal worker V1–V10 on clean new Git head and
exact green hosted CI are required to close BSA230. The next
independent release boundary is a tightly scoped non-merging PR
proposal on the pinned existing Pages main, subject to route/asset
verification and external authority; no automatic public release
may be inferred from local V10 acceptance.

The historical finite C3 three-topic heldout generalization
`FAILED_LIMITED_CAMPAIGN` is unchanged, and no manual academic
signoff or learner-pilot requirement is reintroduced.
