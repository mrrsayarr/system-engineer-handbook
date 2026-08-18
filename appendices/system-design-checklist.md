# Appendix D: System Design Checklist

This checklist ensures you cover all critical dimensions when designing or reviewing a system. Use it during design reviews, architecture discussions, and interview preparation.

---

## Pre-Design: Requirements & Constraints

### Functional Requirements
- [ ] Core use cases identified and prioritized
- [ ] User roles and permissions defined
- [ ] API contracts specified (endpoints, payloads, error codes)
- [ ] Data flow diagrams for primary workflows
- [ ] Integration points with external systems documented

### Non-Functional Requirements (NFRs)
- [ ] **Availability**: Target (e.g., 99.9%, 99.99%), downtime budget
- [ ] **Latency**: p50, p95, p99 targets for each critical path
- [ ] **Throughput**: Peak QPS, sustained QPS, growth projections
- [ ] **Consistency**: Strong, eventual, causal — per data domain
- [ ] **Durability**: RPO target, backup/recovery requirements
- [ ] **Scalability**: Horizontal vs vertical, scaling triggers, limits
- [ ] **Security**: Data classification, encryption, compliance (PCI, GDPR, SOC2)
- [ ] **Observability**: SLIs, SLOs, alerting requirements
- [ ] **Cost**: Budget constraints, cost per request targets
- [ ] **Operational**: Deployment model, rollback time, on-call expectations

### Scale Estimation (Back-of-the-Envelope)
- [ ] Daily/Monthly active users
- [ ] Requests per second (average, peak)
- [ ] Read/Write ratio
- [ ] Data volume (current, 1yr, 3yr projection)
- [ ] Storage growth rate
- [ ] Network bandwidth requirements
- [ ] Cache hit ratio targets

---

## High-Level Architecture

### Component Design
- [ ] Service boundaries defined (bounded contexts)
- [ ] Component diagram with data flows
- [ ] Technology choices justified per component
- [ ] Communication patterns (sync vs async) decided
- [ ] Failure domains isolated

### Data Architecture
- [ ] Database selection per service (SQL, NoSQL, NewSQL, specialized)
- [ ] Data models with access patterns
- [ ] Sharding/partitioning strategy
- [ ] Replication topology (single-leader, multi-leader, leaderless)
- [ ] Cross-region data strategy
- [ ] Backup and DR procedures defined

### Network & Edge
- [ ] Load balancing strategy (L4 vs L7, algorithms)
- [ ] TLS termination point
- [ ] CDN strategy for static assets
- [ ] DNS architecture (geo-routing, failover)
- [ ] Service mesh or sidecar decision
- [ ] Network segmentation (VPC, subnets, security groups)

---

## Detailed Design: Critical Paths

### Caching Strategy
- [ ] What to cache (and what NOT to cache)
- [ ] Cache layers (browser, CDN, edge, app, distributed, DB)
- [ ] Cache patterns (cache-aside, read-through, write-through, write-behind)
- [ ] TTL strategy per data type
- [ ] Invalidation mechanism (TTL, event-driven, version-based, tag-based)
- [ ] Stampede prevention (locking, xfetch, stale-while-revalidate)
- [ ] Negative caching for missing keys
- [ ] Cache warming strategy
- [ ] Monitoring: hit ratio, latency, evictions, memory

### Database Design
- [ ] Schema normalized to 3NF (or justified denormalization)
- [ ] Primary keys: UUIDv7/ULID for distributed, BIGINT for single-node
- [ ] Indexes for all query patterns (composite order matters)
- [ ] Partial indexes for sparse filters
- [ ] Connection pooling configured (PgBouncer, HikariCP)
- [ ] Read replicas for read scaling
- [ ] Query optimization (EXPLAIN ANALYZE, no N+1)
- [ ] Migration strategy (expand-contract, zero-downtime)

### Messaging & Event-Driven
- [ ] Pattern selected (queue, pub/sub, event streaming)
- [ ] Broker choice (Kafka, RabbitMQ, SQS, NATS, Pulsar)
- [ ] Topic/queue design (partitioning, retention, compaction)
- [ ] Delivery guarantees (at-least-once + idempotency = exactly-once)
- [ ] Schema registry with compatibility enforcement
- [ ] Consumer design (batching, offset management, rebalance handling)
- [ ] Dead letter queue strategy
- [ ] Backpressure handling
- [ ] Monitoring: lag, throughput, error rate, latency

### Load Balancing & Traffic
- [ ] L4 vs L7 decision
- [ ] Algorithm selection
- [ ] Health checks (active + passive, readiness vs liveness)
- [ ] Session persistence (if needed) with cookie/IP hash
- [ ] Rate limiting (per client, per route, global)
- [ ] Circuit breakers and retries with budgets
- [ ] Canary/blue-green deployment support
- [ ] WAF rules for OWASP Top 10
- [ ] Graceful shutdown and connection draining

---

## Resilience & Fault Tolerance

### Failure Handling
- [ ] Timeout values set at every layer (client, LB, service, DB)
- [ ] Retry policies with exponential backoff + jitter
- [ ] Circuit breakers on all downstream dependencies
- [ ] Bulkheads isolating critical resources
- [ ] Idempotency keys on all mutating operations
- [ ] Graceful degradation (feature flags, cached fallbacks)
- [ ] Chaos engineering experiments defined

### Multi-Region / DR
- [ ] Active-active vs active-passive decision
- [ ] Data replication strategy (sync vs async)
- [ ] Failover automation and runbooks
- [ ] RPO/RTO targets documented and tested
- [ ] Cross-region latency impact assessed
- [ ] Data residency/compliance constraints mapped

---

## Security

### Network Security
- [ ] Zero-trust network segmentation
- [ ] mTLS for all service-to-service communication
- [ ] WAF at edge for HTTP traffic
- [ ] DDoS protection at cloud provider level
- [ ] Egress controls (allowlist external destinations)

### Identity & Access
- [ ] Authentication strategy (OIDC, JWT, mTLS, API keys)
- [ ] Authorization model (RBAC, ABAC, ReBAC)
- [ ] Service identity (SPIFFE/SPIRE, cloud workload identity)
- [ ] Least privilege enforced
- [ ] Secrets management (Vault, cloud KMS, rotation)

### Data Protection
- [ ] Encryption in transit (TLS 1.3 minimum)
- [ ] Encryption at rest (cloud KMS, envelope encryption)
- [ ] Field-level encryption for PII/secrets
- [ ] Key rotation schedule
- [ ] Data classification and handling procedures

### Application Security
- [ ] Input validation at all boundaries
- [ ] Parameterized queries (no SQL injection)
- [ ] Output encoding (XSS prevention)
- [ ] CSRF tokens for state-changing operations
- [ ] Security headers (CSP, HSTS, X-Frame-Options)
- [ ] Dependency scanning (SAST, DAST, SCA in CI)

---

## Observability & Operations

### Instrumentation
- [ ] OpenTelemetry on all services (traces, metrics, logs)
- [ ] Structured JSON logging with correlation IDs
- [ ] Golden signals (latency, traffic, errors, saturation)
- [ ] RED metrics per service
- [ ] USE metrics per resource
- [ ] Business metrics (conversion, revenue, adoption)

### Dashboards & Alerts
- [ ] Executive dashboard (SLO health, incidents)
- [ ] Operations dashboard (service health, dependencies)
- [ ] Engineering dashboard (detailed latency, errors, resources)
- [ ] Alert tiers: Page (immediate), Business-hours ticket, Ticket, Suppress
- [ ] Runbooks linked to every alert
- [ ] Alert fatigue review quarterly

### SLOs & Error Budgets
- [ ] SLIs defined for each critical user journey
- [ ] SLOs set with stakeholder agreement
- [ ] Error budget calculated and tracked
- [ ] Burn rate alerts configured
- [ ] Release gates based on error budget

### Incident Response
- [ ] On-call rotation with escalation policy
- [ ] Incident commander role defined
- [ ] Communication channels (Slack, bridge, status page)
- [ ] Blameless postmortem template
- [ ] Action item tracking with owners and due dates

---

## Deployment & Release

### CI/CD Pipeline
- [ ] Build: compile, lint, unit test, static analysis
- [ ] Security: SAST, DAST, SCA, container scan
- [ ] Test: integration, contract, e2e (selective)
- [ ] Package: container image built, signed, SBOM generated
- [ ] Deploy: progressive (canary/blue-green), health checks
- [ ] Verify: smoke tests, synthetic monitoring
- [ ] Rollback: automated, < 5 minutes

### Release Strategies
- [ ] Trunk-based development with feature flags
- [ ] Canary analysis (automated metric comparison)
- [ ] Blue-green for stateful components
- [ ] Database migrations: expand-contract, backward compatible
- [ ] Feature flag lifecycle (creation, cleanup)

### GitOps
- [ ] Git as single source of truth
- [ ] ArgoCD/Flux for continuous reconciliation
- [ ] Environment promotion via PR
- [ ] Drift detection and alerting

---

## Cost Optimization

- [ ] Resource right-sizing (CPU, memory, storage)
- [ ] Reserved/Committed use for baseline
- [ ] Spot/Preemptible for fault-tolerant batch
- [ ] Auto-scaling policies (scale-to-zero where possible)
- [ ] Data tiering (hot/warm/cold storage)
- [ ] Tagging strategy enforced (owner, env, service, cost-center)
- [ ] Anomaly detection on daily/weekly spend
- [ ] Regular cost review with stakeholders

---

## Documentation & Knowledge Transfer

- [ ] Architecture decision records (ADRs) for all major choices
- [ ] Runbooks for common operations and incidents
- [ ] API documentation (OpenAPI/Swagger, kept current)
- [ ] Data dictionary and schema documentation
- [ ] Onboarding guide for new team members
- [ ] Quarterly architecture review cadence

---

## Pre-Launch Checklist (Go/No-Go)

| Check | Owner | Status |
|-------|-------|--------|
| All P0/P1 bugs resolved | Engineering | [ ] |
| Load test passed at 2x peak | SRE | [ ] |
| Chaos experiments passed | SRE | [ ] |
| Security review complete | Security | [ ] |
| Compliance validation (PCI/GDPR/SOC2) | Compliance | [ ] |
| Runbooks written and reviewed | SRE | [ ] |
| Dashboards and alerts deployed | SRE | [ ] |
| On-call rotation confirmed | Management | [ ] |
| Rollback tested and < 5 min | Engineering | [ ] |
| Stakeholder sign-off | Product | [ ] |

---

## Interview-Specific Quick Checklist

When solving a system design problem in an interview:

### First 5 Minutes
- [ ] Clarify functional requirements
- [ ] Define non-functional requirements (scale, latency, availability, consistency)
- [ ] Back-of-the-envelope estimation (QPS, storage, bandwidth)
- [ ] Identify 2-3 key constraints that drive architecture

### Minutes 5-20: High-Level Design
- [ ] Draw component diagram
- [ ] Define API contracts
- [ ] Choose databases with justification
- [ ] Show data flows for primary use cases
- [ ] Identify caching layers

### Minutes 20-40: Deep Dive
- [ ] Pick 1-2 bottlenecks and go deep
- [ ] Sharding/partitioning strategy
- [ ] Replication and consistency model
- [ ] Failure scenarios and mitigations
- [ ] Scaling triggers and limits

### Minutes 40-55: Production Concerns
- [ ] Observability (metrics, logs, traces, alerts)
- [ ] Deployment strategy (CI/CD, rollback)
- [ ] Security (auth, encryption, compliance)
- [ ] Cost optimization
- [ ] DR and multi-region (if applicable)

### Final 5 Minutes
- [ ] Summarize key trade-offs
- [ ] Acknowledge what you'd do differently with more time
- [ ] Ask if interviewer wants to dive deeper anywhere

---

## Template: One-Page Architecture Summary

```
SYSTEM: __________________________________________
OWNER: ___________________  LAST REVIEWED: _______

SCALE: _____ QPS peak  |  _____ TB data  |  _____ regions

NFR TARGETS:
  Availability: _____%  |  Latency p99: _____ms  |  Consistency: __________

ARCHITECTURE:
  Edge: _________________________________________
  Compute: ______________________________________
  Data: _________________________________________
  Messaging: ____________________________________
  Observability: ________________________________

KEY DECISIONS (ADR refs):
  - ____________________________________________
  - ____________________________________________

TOP RISKS:
  1. ___________________________________________
  2. ___________________________________________
  3. ___________________________________________

RUNBOOKS: ______________________________________
ON-CALL: _______________________________________
```

---

> **Return to**: [Main README](../README.md) | [Glossary](./glossary.md) | [Resources](./resources.md) | [ADR Templates](./adr-templates.md)