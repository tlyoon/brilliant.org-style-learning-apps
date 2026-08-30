# Project-specific extensions

This directory contains checked-in tooling that belongs to an existing project's historical or review workflow. Nothing here is imported by the generic generator, workstation synchronizer, learner runtime, or generic public-release builder.

`brilliant_content_generator/build_public_review.py` preserves the approved Chapter 8 comparison site. Recycled projects do not edit or invoke it; they use `scripts/build_public_release.py` with an explicitly selected package.
