# Clean-room provenance

This repository is a sanitized clean-room reimplementation of generic engineering concepts:
validated experiment manifests, execution adapters, bounded orchestration, synthetic report
parsing, and neutral technical reporting.

It has a new Git history and newly written package code, tests, fixtures, and documentation. It does
not include source history, trading strategies, Expert Advisors, presets, compiled bots, real
accounts, broker details, terminal topology, credentials, customer or collaborator information,
real market data, reports, equity curves, screenshots, spreadsheets, performance claims, or
third-party skill bundles.

Every included export is deterministic synthetic test data. Third-party runtime libraries are used
through their published packages and documented in `THIRD_PARTY.md`; their code is not vendored.
Detailed source-to-concept audit notes are intentionally local-only and ignored by Git.
