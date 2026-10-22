# Multi-PC production gate

This gate is the last infrastructure validation before continuous auto generation is treated as feature-complete.

## Required workstation conditions

The three supported production workers are Dell-115, HP, and Yoga6. Zenbook is intentionally excluded.

Each worker must satisfy all of the following before a live multi-PC run:

- repository revision matches current main;
- clean Git working tree;
- llm_backend is gemini_api;
- machine-local Gemini API token exists;
- machine-local Drive OAuth client exists;
- the configured source root is identical across workers;
- doctor in auto mode completes without claiming a job;
- no worker uses the shared browser Gem in continuous auto mode.

## Deterministic concurrency gate

tests/test_multi_pc_production_gate.py exercises three independent coordinator clients against one shared in-memory Drive event store. It verifies:

1. three workers distribute onto three distinct jobs;
2. no duplicate live fencing token is accepted;
3. a failed worker writes durable failure state and releases its claim;
4. a different worker reclaims the interrupted job as attempt 2;
5. parsed-stage checkpoints survive the worker change;
6. the released lease token cannot remain active.

This complements the lower-level election tests in tests/test_drive_coordination.py and the watchdog/publication tests in tests/test_auto_public_watchdog.py.

## Exit criterion

When the deterministic gate, repository regression suite, and three real workstation doctors pass on the same main revision, the coordination layer is considered complete. Further changes to leasing, browser isolation, or coordinator architecture require a concrete defect or contract change.

A later live content stress run should use fresh work only after the visual-generation pilot is ready, so validation does not create content that must immediately be regenerated under a newer visual contract.
