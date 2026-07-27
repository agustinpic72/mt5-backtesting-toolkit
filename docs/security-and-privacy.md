# Security and privacy

## Threat model

Manifests and report exports are untrusted local inputs. A malicious input may attempt path
traversal, YAML object construction, XML entity expansion, excessive allocation, malformed numeric
values, or secret disclosure through diagnostics.

## Controls

- Manifests reject unknown fields, duplicate YAML keys, secret-like parameters, excessive grid
  products, unsafe paths, and invalid execution limits.
- Workspace paths reject POSIX absolute paths, Windows drives, UNC paths, parent traversal, NUL
  bytes, and resolved symlink escape.
- Report inputs are size-limited and decoded strictly as UTF-8/UTF-8-BOM.
- XML is parsed with `defusedxml`; external entities and unsafe declarations fail.
- Numeric parsing rejects non-finite and ambiguous localized values.
- Diagnostics redact common secret assignments and personal home paths.
- No credential model exists. Do not place credentials in a manifest, fixture, command line, issue,
  or report.

## Data boundary

Only deterministic synthetic examples belong in the repository. Do not contribute real account,
broker, terminal, strategy, market, customer, collaborator, performance, or machine-topology data.
The repository policy tests reject strategy and compiled-bot extensions and enforce disclaimer
markers on synthetic exports.

## Local adapter

The local adapter has no default paths, broker fields, credential fields, or process-launch behavior.
Its explicit opt-in validates only workspace-confined files and constructs a subprocess argument
list for future extension.
