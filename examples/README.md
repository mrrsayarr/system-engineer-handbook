# Practical Engineering Examples

This directory contains small, reviewable examples for the six practical labs in
the learning roadmap. They are intentionally compact: each example exposes one
engineering invariant, a failure mode, and a verification command. They are
learning artifacts, not production-ready components.

| Example | Main skill | Run locally |
|---------|------------|-------------|
| [Network troubleshooting](./network-troubleshooting/) | Layered diagnosis with reproducible evidence | PowerShell or Bash + `curl`/`dig`/`ss`/`mtr` where available |
| [Database/index analysis](./database-index-analysis/) | Compare query plans before/after an index | PostgreSQL 15+ with `psql` |
| [Cache stampede protection](./cache-stampede-protection/) | Single-flight refresh, stale-while-revalidate | Python 3.11+; standard library only |
| [Idempotent message consumer](./idempotent-message-consumer/) | Atomic deduplication and retry-safe side effects | Python 3.11+; standard library only |
| [OpenTelemetry instrumentation](./opentelemetry-instrumentation/) | HTTP spans, context propagation, redaction | Python 3.11+; optional OpenTelemetry packages |
| [Kubernetes deployment/rollback](./kubernetes-deployment-rollback/) | Immutable image rollout and guarded rollback | Kubernetes 1.28+ with `kubectl` |

## Learning contract

For each lab, first read the assumptions and failure modes, then run the happy
path, inject the listed failure, and explain the observed evidence. Keep test
data synthetic. Do not point the commands at production systems without an
approved change and rollback plan.

## Suggested order

```mermaid
flowchart LR
    N[Network evidence] --> D[Database plan]
    D --> C[Cache concurrency]
    C --> M[Message idempotency]
    M --> O[Trace context and redaction]
    O --> K[Kubernetes rollout and rollback]
```

All examples were reviewed on 2026-08-31. Provider-specific flags and package
versions can change; pin versions in a real project and verify against current
official documentation before deployment.
