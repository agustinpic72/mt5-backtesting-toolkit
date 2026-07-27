# Third-party dependencies

No dependency source code is vendored. Runtime packages are installed from their publishers:

| Package | Purpose | Upstream license |
|---|---|---|
| Pydantic | Typed validation and serialization | MIT |
| PyYAML | Safe YAML parsing | MIT |
| defusedxml | Entity-safe XML parsing | Python Software Foundation License |

Development-only tooling and complete resolved versions appear in `requirements-dev.lock`. Each
dependency remains governed by its own license; Apache-2.0 applies only to this repository's newly
implemented code and documentation.
