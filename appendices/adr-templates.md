# Appendix C: Architecture Decision Record (ADR) Templates

This appendix provides ready-to-use ADR templates for documenting architectural decisions. ADRs capture context, alternatives considered, and consequences for future maintainers.

---

## Why ADRs Matter

```text
ARCHITECTURAL DECISIONS ARE EXPENSIVE TO REVERSE.

An ADR provides:
  - Historical context for why a choice was made
  - Explicit trade-offs considered
  - Decision ownership and date
  - Basis for future reconsideration
  - Onboarding artifact for new team members
```

---

## ADR Format (Standard)

```markdown
# ADR {NUMBER}: {TITLE}

## Status
{Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-{NUMBER}}

## Context
{What is the problem we're facing? What forces are at play? What constraints exist?}

## Decision
{What are we doing? Be specific and actionable.}

## Consequences
### Positive
- {Benefit 1}
- {Benefit 2}

### Negative
- {Drawback 1}
- {Drawback 2}

### Risks
- {Risk 1 and mitigation}
- {Risk 2 and mitigation}

## Alternatives Considered
| Alternative | Pros | Cons | Why Not Chosen |
|-------------|------|------|----------------|
| {Alt 1} | {Pros} | {Cons} | {Reason} |
| {Alt 2} | {Pros} | {Cons} | {Reason} |

## References
- {Link to relevant doc, issue, RFC, or external resource}
- {Related ADRs}

## Metadata
- **Date**: {YYYY-MM-DD}
- **Author(s)**: {Name(s)}
- **Reviewers**: {Name(s)}
- **Tags**: {database, security, scaling, migration, ...}
```

---

## Template 1: Database Selection

```markdown
# ADR 001: Primary Database Selection for Order Service

## Status
Accepted

## Context
The Order Service requires:
- Strong consistency for financial transactions
- Complex relational queries (joins, aggregations)
- Horizontal scaling to 10K QPS within 18 months
- Multi-region deployment for DR (RPO < 1s, RTO < 5m)
- Team has strong PostgreSQL expertise, no CockroachDB experience

## Decision
Use **PostgreSQL 16** with **Citus** extension for horizontal scaling.

- Single-primary per shard with synchronous replication within region
- Cross-region async replication with logical replication slots
- Citus coordinator for distributed queries and shard management
- pgBouncer for connection pooling

## Consequences
### Positive
- Leverages existing PostgreSQL expertise
- Strong ACID guarantees for transactions
- Citus provides transparent sharding
- Mature ecosystem and tooling

### Negative
- Citus adds operational complexity vs managed service
- Cross-region async replication introduces RPO > 0
- Distributed transactions require application-level saga pattern
- Coordinator is single point of failure (mitigate with Patroni)

### Risks
- Shard rebalancing during scale events may cause latency spikes
  - Mitigation: pre-split shards, monitor shard distribution
- Citus version upgrades require coordinated rollout
  - Mitigation: test upgrades in staging, blue-green coordinator

## Alternatives Considered
| Alternative | Pros | Cons | Why Not Chosen |
|-------------|------|------|----------------|
| CockroachDB | Native distributed SQL, strong consistency, multi-region | Team lacks expertise, different SQL dialect quirks | Learning curve too steep for timeline |
| Aurora PostgreSQL | Managed, auto-scaling storage, global database | Limited sharding, cross-region writes complex | Write scaling ceiling at ~20K QPS |
| DynamoDB | Serverless, infinite scale, multi-region | No SQL, eventual consistency default, cost at scale | Transactions require ACID |
| Vitess (MySQL) | Proven at YouTube scale, connection pooling | Team expertise is PostgreSQL, not MySQL | Migration cost high |

## References
- Citus Documentation: https://docs.citusdata.com/
- PostgreSQL Logical Replication: https://www.postgresql.org/docs/current/logical-replication.html
- Related: ADR-003 (Connection Pooling Strategy)

## Metadata
- **Date**: 2024-01-15
- **Author(s)**: Sarah Chen, Marcus Rodriguez
- **Reviewers**: Priya Patel, James Wong
- **Tags**: database, postgresql, citus, scaling, multi-region
```

---

## Template 2: Messaging Platform Selection

```markdown
# ADR 002: Event Streaming Platform Selection

## Status
Accepted

## Context
We need a messaging backbone for:
- Order events (created, paid, shipped, cancelled) — 50K events/sec peak
- Inventory reservation commands — 20K/sec
- Notification fanout (email, push, SMS) — 100K/sec
- Audit log retention 7 years
- Cross-region replication for DR
- Exactly-once semantics for payment events

## Decision
Use **Apache Kafka** (self-managed on Kubernetes via Strimzi operator).

- 3 clusters: primary (us-east-1), DR (eu-west-1), analytics (us-east-1)
- Topic design: domain-driven (orders, inventory, notifications, audit)
- Retention: 7 days hot (SSD), 7 years cold (S3 via tiered storage)
- Compression: ZSTD for all topics
- Schema Registry: Confluent Schema Registry with BACKWARD compatibility

## Consequences
### Positive
- High throughput, durable, replayable
- Exactly-once via idempotent producer + transactional consumer
- Mature ecosystem (Kafka Connect, ksqlDB, Flink)
- Tiered storage reduces cost for long retention

### Negative
- Operational burden: broker management, ISR monitoring, rebalancing
- JVM tuning and heap management complexity
- Zookeeper/KRaft controller adds failure domain
- Cross-cluster replication (MirrorMaker) adds latency

### Risks
- Under-replicated partitions during broker loss
  - Mitigation: min.insync.replicas=2, rack awareness, alerting on under-replicated
- Consumer lag during traffic spikes
  - Mitigation: partition by order_id, scale consumers, lag alerts
- Schema evolution breaking consumers
  - Mitigation: CI gate on schema compatibility, contract tests

## Alternatives Considered
| Alternative | Pros | Cons | Why Not Chosen |
|-------------|------|------|----------------|
| Amazon MSK | Managed, integrates with AWS | Vendor lock-in, cost at scale, less control | Multi-cloud strategy |
| Pulsar | Tiered storage native, geo-replication, multi-tenancy | Smaller ecosystem, team unfamiliar | Kafka expertise already exists |
| NATS JetStream | Lightweight, simple, good for lower throughput | Not proven at 100K+/sec sustained | Scale requirements |
| RabbitMQ | Flexible routing, mature | Not log-based, no replay, lower throughput | Event streaming requirements |

## References
- Kafka Documentation: https://kafka.apache.org/documentation/
- Strimzi Operator: https://strimzi.io/
- Confluent Schema Registry: https://docs.confluent.io/platform/current/schema-registry/
- Related: ADR-005 (Schema Evolution Policy)

## Metadata
- **Date**: 2024-01-20
- **Author(s)**: Alex Kumar, Nina Petrov
- **Reviewers**: David Liu, Maria Santos
- **Tags**: messaging, kafka, streaming, events, multi-region
```

---

## Template 3: Cache Strategy

```markdown
# ADR 003: Caching Strategy for Product Catalog

## Status
Accepted

## Context
Product Catalog API serves 500K QPS peak with:
- 10M SKUs, 100K updates/day
- Read-heavy: 99% reads, 1% writes
- Latency SLO: p99 < 50ms
- Stale data acceptable for 30 seconds (eventual consistency)
- Multi-region active-active deployment

## Decision
Implement **three-tier caching**:

1. **CDN (Cloudflare)**: Cache public product pages, TTL 5 min, purge by tag on update
2. **Edge Cache (Cloudflare Workers KV)**: Per-region cache for API responses, TTL 30s
3. **Distributed Cache (Redis Cluster)**: Per-region Redis with async cross-region invalidation via Kafka

Cache-Aside pattern with **stale-while-revalidate**:
- On cache miss: fetch from DB, populate cache, return
- On cache hit with age > 25s: return stale, async refresh in background
- On write: invalidate cache key, publish invalidation event to Kafka
- Consumers in other regions receive event, delete local key

## Consequences
### Positive
- CDN absorbs 80%+ of traffic
- Edge cache reduces cross-region latency
- Stale-while-revalidate eliminates cache stampede
- Event-driven invalidation ensures eventual consistency

### Negative
- Three layers increase complexity
- Redis cross-region invalidation adds eventual consistency window
- Cache warming needed after deployments
- Cache keys must be carefully designed to avoid cardinality explosion

### Risks
- Cache key explosion from user-specific variations
  - Mitigation: normalize keys, separate user-specific data
- Stale data served beyond acceptable window
  - Mitigation: monitor staleness metric, alert on p99 age > 30s
- Redis failover causes cache miss storm
  - Mitigation: Redis Cluster with replica promotion < 5s, circuit breaker

## Alternatives Considered
| Alternative | Pros | Cons | Why Not Chosen |
|-------------|------|------|----------------|
| Read-Through (Redis only) | Simpler, single cache layer | No CDN offload, all traffic hits Redis | CDN cost savings significant |
| Write-Through | Strong consistency | Write latency doubled, complex for 100K updates/day | Eventual consistency acceptable |
| No caching, read replicas only | Simplest | Cannot meet p99 < 50ms at 500K QPS | Latency SLO |

## References
- Cloudflare Caching: https://developers.cloudflare.com/cache/
- Redis Cluster: https://redis.io/docs/management/scaling/
- Related: ADR-007 (Cache Key Design Standards)

## Metadata
- **Date**: 2024-02-01
- **Author(s)**: Lisa Zhang, Omar Hassan
- **Reviewers**: Kevin Park, Ana Silva
- **Tags**: caching, redis, cloudflare, cdn, multi-region
```

---

## Template 4: Service Decomposition

```markdown
# ADR 004: Extract Payment Service from Monolith

## Status
Accepted

## Context
Monolithic payment module causes:
- Deployment coupling: any change requires full monolith deploy
- Scaling: payment traffic (10K QPS) differs from catalog (500K QPS)
- Team autonomy: payments team blocked by monolith release train
- Failure domain: payment bug crashes entire application
- Compliance: PCI DSS scope includes entire monolith

## Decision
Extract **Payment Service** as independent microservice.

- API: gRPC for internal, REST for webhooks
- Database: dedicated PostgreSQL with encrypted columns for PAN
- Communication: async via Kafka for order events, sync gRPC for authorization
- Deployment: independent CI/CD pipeline, canary to 5% then 100%
- Data migration: dual-write with CDC, cutover after verification

## Consequences
### Positive
- Independent deployments and scaling
- Reduced PCI DSS scope (only payment service)
- Team autonomy for payments team
- Failure isolation: payment outage doesn't crash catalog

### Negative
- Distributed transaction complexity (saga for order+payment)
- Network latency added to payment flow
- Operational overhead: separate monitoring, logging, on-call
- Data consistency: eventual between order and payment

### Risks
- Saga compensation failures leave orders in inconsistent state
  - Mitigation: idempotent compensation, dead letter queue, manual reconciliation runbook
- Network partition between order and payment services
  - Mitigation: circuit breaker, timeout, fallback to async with polling
- PCI compliance validation for new service boundary
  - Mitigation: engage QSA early, document data flows, tokenize PAN

## Alternatives Considered
| Alternative | Pros | Cons | Why Not Chosen |
|-------------|------|------|----------------|
| Keep in monolith, modularize | Simple, no distributed complexity | Doesn't solve scaling, deployment, compliance | Core problems persist |
| Extract to serverless functions | Auto-scaling, no infrastructure | Cold starts, vendor lock-in, debugging harder | Latency and compliance needs |
| Separate database per service (current) | Clear ownership | Distributed transactions needed | Accepted trade-off |

## References
- Saga Pattern: https://microservices.io/patterns/data/saga.html
- PCI DSS Scoping: https://www.pcisecuritystandards.org/
- Related: ADR-002 (Kafka for async), ADR-006 (gRPC Standards)

## Metadata
- **Date**: 2024-02-15
- **Author(s)**: Rachel Kim, Thomas Berg
- **Reviewers**: Sunita Rao, Carlos Mendez
- **Tags**: microservices, payments, pci-dss, saga, extraction
```

---

## Template 5: Security Control

```markdown
# ADR 005: mTLS Implementation for Service Mesh

## Status
Accepted

## Context
Current state:
- Plain HTTP between services in Kubernetes
- No service identity verification
- Network policies only at namespace level
- Compliance requires encryption in transit for all internal traffic

## Decision
Implement **mutual TLS (mTLS)** using **Istio** service mesh.

- Istio control plane (istiod) with external CA (Vault PKI)
- Workload identity via SPIFFE IDs: spiffe://cluster.local/ns/{ns}/sa/{sa}
- STRICT mTLS mode enforced cluster-wide via PeerAuthentication
- DestinationRules for per-service traffic policies
- Certificate rotation: 24h TTL, automated by Istio
- Egress: mTLS to external services where supported, otherwise TLS origination

## Consequences
### Positive
- Zero-trust encryption and identity for all service communication
- Automatic certificate lifecycle management
- Fine-grained authorization via AuthorizationPolicy
- Observability: metrics, traces, access logs with identity context

### Negative
- Added complexity: sidecar injection, control plane, certificate management
- CPU/memory overhead per pod (Envoy sidecar ~10-20m CPU, ~50-100Mi memory)
- MTU issues with IPsec/CNI plugins
- Debugging complexity: encrypted payloads require sidecar logs

### Risks
- Control plane outage breaks certificate rotation
  - Mitigation: HA istiod (3 replicas), external CA fallback, monitoring
- Certificate expiry causes connection failures
  - Mitigation: short TTL (24h), automated rotation, alert on expiry < 6h
- Legacy services without sidecar support
  - Mitigation: PERMISSIVE mode during migration, gateway for external

## Alternatives Considered
| Alternative | Pros | Cons | Why Not Chosen |
|-------------|------|------|----------------|
| Linkerd | Lighter weight, simpler | Less ecosystem, fewer features | Istio features needed (WASM, advanced routing) |
| Consul Connect | Integrated with Consul | Requires Consul cluster | Already standardizing on Istio |
| Application-level mTLS | No sidecar | Manual cert management, inconsistent | Operational burden too high |
| NetworkPolicy only | Native K8s, no sidecar | No encryption, no identity | Compliance requires encryption |

## References
- Istio mTLS: https://istio.io/latest/docs/tasks/security/mtls-migration/
- SPIFFE: https://spiffe.io/
- Vault PKI: https://www.vaultproject.io/docs/secrets/pki
- Related: ADR-008 (Authorization Policy Standards)

## Metadata
- **Date**: 2024-03-01
- **Author(s)**: Priya Nair, Stefan Weber
- **Reviewers**: Elena Volkov, Marcus Johnson
- **Tags**: security, mtls, istio, spiffe, zero-trust, compliance
```

---

## Template 6: Migration Strategy

```markdown
# ADR 006: Database Migration from MySQL to PostgreSQL

## Status
Accepted

## Context
Legacy MySQL 5.7 instance:
- 2TB data, 5K QPS peak
- End of life (EOL) October 2023
- Team wants PostgreSQL for JSONB, better indexing, CTEs
- Zero-downtime requirement (RTO < 30s, RPO = 0)

## Decision
**Phased migration using dual-write with CDC**.

Phase 1 (Week 1-2): Schema translation and validation
- Convert schema using pgloader, manual review
- Create PostgreSQL instance in same VPC
- Validate data types, constraints, indexes

Phase 2 (Week 3-4): Dual-write with CDC
- Application writes to both MySQL (primary) and PostgreSQL (shadow)
- Debezium CDC from MySQL binlog to Kafka
- Kafka Connect sinks to PostgreSQL for backfill
- Data comparison job: checksum tables daily

Phase 3 (Week 5): Read traffic shadow
- Route 1% of read traffic to PostgreSQL
- Compare results, measure latency
- Gradually increase to 100% reads

Phase 4 (Week 6): Cutover
- Stop MySQL writes, promote PostgreSQL to primary
- Update DNS/connection strings
- Monitor for 48h, then decommission MySQL

Rollback plan at each phase: revert traffic, continue dual-write.

## Consequences
### Positive
- Zero downtime, zero data loss
- Incremental risk reduction
- Ability to validate at each phase
- Rollback available until final cutover

### Negative
- 6-week migration timeline
- Dual-write complexity in application
- CDC pipeline adds operational surface
- Schema drift risk during migration

### Risks
- CDC lag causes stale reads during shadow phase
  - Mitigation: monitor lag, pause shadow if lag > 5s
- Data mismatch between MySQL and PostgreSQL
  - Mitigation: automated comparison, alert on any discrepancy
- Application bugs in dual-write path
  - Mitigation: feature flag per write path, extensive integration tests

## Alternatives Considered
| Alternative | Pros | Cons | Why Not Chosen |
|-------------|------|------|----------------|
| pgloader one-shot | Simple, fast | Requires downtime, no RPO=0 | Zero-downtime requirement |
| AWS DMS | Managed CDC | Limited transformation, vendor lock-in | Need custom type handling |
| Logical replication (pglogical) | Native | MySQL to PG not supported | Cross-engine not supported |
| Application-level sync | Full control | High development effort | CDC tools mature |

## References
- pgloader: https://pgloader.io/
- Debezium: https://debezium.io/
- AWS DMS: https://aws.amazon.com/dms/
- Related: ADR-009 (CDC Pipeline Standards)

## Metadata
- **Date**: 2024-03-10
- **Author(s)**: Diego Morales, Hannah Brooks
- **Reviewers**: Victor Hugo, Leila Ahmadi
- **Tags**: migration, mysql, postgresql, cdc, debezium, zero-downtime
```

---

## ADR Index (Example)

```markdown
# Architecture Decision Records Index

| ID | Title | Status | Date | Tags |
|----|-------|--------|------|------|
| 001 | Primary Database Selection for Order Service | Accepted | 2024-01-15 | database, postgresql, citus |
| 002 | Event Streaming Platform Selection | Accepted | 2024-01-20 | messaging, kafka, streaming |
| 003 | Caching Strategy for Product Catalog | Accepted | 2024-02-01 | caching, redis, cdn |
| 004 | Extract Payment Service from Monolith | Accepted | 2024-02-15 | microservices, payments, pci-dss |
| 005 | mTLS Implementation for Service Mesh | Accepted | 2024-03-01 | security, mtls, istio |
| 006 | Database Migration from MySQL to PostgreSQL | Accepted | 2024-03-10 | migration, mysql, postgresql |

---

## ADR Lifecycle

1. **Proposed** — Author creates ADR, shares for review
2. **Review** — Stakeholders comment, suggest alternatives
3. **Accepted** — Consensus reached, merged to main
4. **Implemented** — Decision enacted in code/infrastructure
5. **Deprecated** — Superseded by new ADR (link to superseding ADR)
6. **Superseded** — Explicitly replaced by newer ADR

---

## ADR Best Practices

- One ADR per architectural decision
- Keep ADRs in version control (docs/adr/)
- Number sequentially (001, 002, ...)
- Link related ADRs in References section
- Update status when decision changes
- Never delete ADRs — mark Deprecated/Superseded
- Review ADRs quarterly during architecture review
```

---

## Blank ADR Template (Copy-Paste Ready)

```markdown
# ADR {NUMBER}: {SHORT TITLE}

## Status
Proposed

## Context
{Describe the problem, constraints, and forces driving this decision.}

## Decision
{State the decision clearly and specifically.}

## Consequences
### Positive
- {Benefit 1}
- {Benefit 2}

### Negative
- {Drawback 1}
- {Drawback 2}

### Risks
- {Risk 1 and mitigation}
- {Risk 2 and mitigation}

## Alternatives Considered
| Alternative | Pros | Cons | Why Not Chosen |
|-------------|------|------|----------------|
| {Alt 1} | | | |
| {Alt 2} | | | |

## References
- {Link 1}
- {Link 2}

## Metadata
- **Date**: {YYYY-MM-DD}
- **Author(s)**: {Names}
- **Reviewers**: {Names}
- **Tags**: {comma-separated}
```

---

> **Return to**: [Main README](../README.md) | [Glossary](./glossary.md) | [Resources](./resources.md) | [System Design Checklist](./system-design-checklist.md)