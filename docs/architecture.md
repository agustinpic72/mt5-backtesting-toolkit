# Architecture

The toolkit is a clean-room implementation with one-way dependencies:

```text
CLI -> orchestration -> adapter protocol
 |          |
 |          +-> domain manifests and results
 |
 +-> parsers -> domain results
 |
 +-> reporting -> domain results
```

The domain layer contains immutable Pydantic models, strict validation, stable case expansion, and
typed errors. It does not import adapters, parsers, the CLI, or subprocess facilities.

The orchestration layer expands only previously validated manifests. Retry amplification is capped
by the manifest schema. Transient failures may retry; permanent and timeout failures are converted
immediately to structured terminal results.

The fake adapter is the complete execution path in version 0.1.0. It uses SHA-256-derived seeds,
never Python's process-randomized hash, wall-clock time, a network, or MT5. The local adapter is a
separate fail-closed Windows command boundary and does not execute a process.

CSV, XML, and HTML parsers accept intentionally narrow, documented synthetic schemas. They apply
size, encoding, field, numeric, entity, duplicate, and disclaimer checks before producing canonical
result models.

Reporting serializes stable JSON, renders a compact Markdown table, and calculates explicit
`right - left` metric deltas. It has no selection or recommendation policy.
