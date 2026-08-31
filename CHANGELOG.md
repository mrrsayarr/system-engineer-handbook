# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-08-19

### Added - Initial Release

#### Chapters
- **Chapter 1: System Design Fundamentals** — Design process, requirements, scale estimation, API design, data modeling, architecture patterns (monolith, microservices, modular monolith), CAP/PACELC, failure modes, ADRs, C4 diagrams
- **Chapter 2: Network Engineering Fundamentals** — OSI/TCP-IP models, IPv4/IPv6 addressing, subnetting, routing (BGP, OSPF, IS-IS), spine-leaf fabrics, VXLAN/EVPN, TCP/UDP/QUIC, DNS, load balancing, TLS 1.3, mTLS, zero trust, SDN, network tools
- **Chapter 3: Distributed Systems Concepts** — 8 fallacies, consistency models, CAP/PACELC, consensus (Raft, Paxos), time and clocks (Lamport, vector, HLC, TrueTime), failure detection, resilience patterns (circuit breaker, retry, bulkhead, rate limiting), idempotency, distributed transactions (2PC, Saga), delivery semantics, coordination services
- **Chapter 4: Scalability & Performance Patterns** — Horizontal vs vertical scaling, 12-factor app, stateless services, autoscaling, caching hierarchy, database sharding (consistent hashing, range, directory), replication patterns, connection pooling, CDN/edge computing, async processing, CQRS/event sourcing, multi-tier architecture, RAIL performance model, capacity planning
- **Chapter 5: Database Design & Selection** — Selection framework, PostgreSQL/MySQL internals, ACID/isolation levels, schema design (normalization, zero-downtime migrations), indexing strategies (B-tree, GIN, GiST, BRIN, partial), NoSQL (MongoDB, Cassandra, Redis), NewSQL (CockroachDB, TiDB, Spanner), specialized DBs (TSDB, graph, search, object), replication patterns, backup/DR, anti-patterns
- **Chapter 6: Caching Strategies** — What/where to cache, patterns (cache-aside, read-through, write-through, write-behind, refresh-ahead), invalidation strategies, stampede prevention (locking, xfetch, stale-while-revalidate), technologies (Redis, Memcached, CDN, in-process), distributed cache patterns, coherence, negative caching, warming, security, monitoring, sizing
- **Chapter 7: Message Queues & Event-Driven Architecture** — Messaging taxonomy (queue, pub/sub, event streaming), use cases, RabbitMQ, SQS, Redis Streams, Kafka deep dive (topics, partitions, consumer groups, offsets, exactly-once), delivery semantics, idempotency, poison messages/DLQ, consumer patterns, schema registry, backpressure, operations/DR
- **Chapter 8: Load Balancing & Traffic Management** — L4 vs L7, algorithms (round robin, least connections, consistent hashing, IP hash), health checks (active/passive, readiness/liveness), session persistence, reverse proxies (NGINX, HAProxy, Envoy, Traefik), Kubernetes services/ingress/Gateway API, global LB (DNS, Anycast, geo-routing), traffic management (rate limiting, WAF, retry/timeout/circuit breaker), HA patterns, observability
- **Chapter 9: Monitoring, Observability & Alerting** — Monitoring vs observability, signals (metrics, logs, traces), OpenTelemetry instrumentation, four golden signals, RED/USE methods, structured logging, distributed tracing (W3C trace context, sampling), dashboards per audience, SLIs/SLOs/error budgets, alerting principles (actionable, tiered, response-driven), incident response, blameless postmortems, platform comparison
- **Chapter 10: Security Fundamentals** — STRIDE threat modeling, zero trust, identity/access, network security (mTLS, segmentation), host/container hardening, data classification, encryption (transit, rest), secrets management, application security (injection, XSS, CSRF, validation), API security, compliance (SOC2, ISO27001, PCI DSS, GDPR), audit logging, vulnerability management, incident response
- **Chapter 11: DevOps, CI/CD & Infrastructure as Code** — DevOps culture, team topologies, CI/CD pipeline anatomy, branching models, IaC (Terraform, Pulumi), configuration management (Ansible), container security, release strategies (rolling, blue-green, canary), Kubernetes resources/networking/observability, GitOps (ArgoCD), secrets in pipelines, testing strategy, drift prevention, cost management
- **Chapter 12: Cloud Platforms (AWS, GCP, Azure)** — Shared responsibility, well-architected pillars, compute/storage/networking services across three clouds, managed data services, identity/security, observability/management, migration strategies (rehost/replatform/refactor/retire), FinOps principles
- **Chapter 13: System Engineer Cheat Sheets** — Scale estimation, database selection, caching, load balancing, messaging, monitoring, DNS/CDN, Linux performance, Kubernetes, security, network tools, release/rollback, on-call runbook, capacity/scaling
- **Chapter 14: Real-World Case Studies** — Analysis framework, URL shortener, pastebin, news feed, Netflix streaming, Airbnb search, Uber dispatch, Uber Eats recommendation, circuit breaker patterns
- **Chapter 15: Interview Preparation Guide** — Interview formats, system design framework (6 steps), STAR behavioral framework, practice problems by topic, self-assessment criteria, exercises, final push tips

#### Appendices
- **Appendix A: Glossary of Terms** — 200+ terms across systems, distributed systems, networking, load balancing, databases, caching, messaging, monitoring, CI/CD, security, cloud, interview terminology
- **Appendix B: Recommended Resources & References** — Essential books, must-read papers, official documentation, engineering blogs, video courses, tools by category, practice platforms, communities, newsletters, conferences, certifications
- **Appendix C: ADR Templates** — Standard format + 6 complete examples (database selection, messaging platform, caching strategy, service decomposition, mTLS, migration strategy) + blank template + index
- **Appendix D: System Design Checklist** — Pre-design requirements, high-level architecture, detailed design (caching, DB, messaging, LB), resilience, security, observability, deployment, cost, documentation, pre-launch go/no-go, interview quick checklist, one-page summary template

#### Project Files
- README.md with full table of contents and learning paths
- LICENSE (MIT)
- CONTRIBUTING.md with style guide and process
- CHANGELOG.md

---

## [Unreleased]

### Changed

- **Chapters 1–5:** Added progressive learning metadata (`Foundation → applied → production judgment`), 2026 review dates, level-labeled exercises, and more explicit production assumptions.
- **Chapter 1 — System Design Fundamentals:** Reworked cost estimation around billable workload drivers instead of stale provider prices; clarified CAP/PACELC, idempotency, caching, delivery guarantees, and failure-aware capacity planning.
- **Chapter 2 — Network Engineering Fundamentals:** Replaced classful IPv4 teaching with CIDR and special-purpose ranges; corrected `/26` subnet math; clarified IPv6 fragmentation, IPsec, RPKI/ROV, BGPsec, QUIC, and TLS terminology; changed TCP tuning from copy-paste kernel values to a measured experiment workflow.
- **Chapter 3 — Distributed Systems Concepts:** Reframed CAP as an operation- and failure-specific trade-off; distinguished delivery attempts from effectively-once business outcomes; replaced an unsafe distributed-lock example with atomic acquisition, ownership-aware release, lease-loss handling, and fencing requirements.
- **Chapter 4 — Scalability & Performance Patterns:** Defined scaling in terms of an explicit scaling envelope, SLOs, and marginal cost; modernized primary/replica terminology; qualified quorum claims, RAIL scope, caching guidance, growth assumptions, and failure headroom.
- **Chapter 5 — Database Design & Selection:** Made database selection access-pattern and correctness driven; clarified PostgreSQL isolation and durability; converted zero-downtime claims into online migration risk controls; replaced absolute index and tuning recipes with evidence-based analysis; strengthened replication, backup verification, RTO/RPO, and reconciliation guidance.
- **Chapter 6 — Caching Strategies:** Reframed cache effectiveness around hit/miss latency distributions and origin protection; documented write-through race boundaries; modernized Redis primary/replica terminology; strengthened authorization-aware cache keys, bounded-cardinality metrics, lifecycle policy, and failure fallback guidance.
- **Chapter 7 — Message Queues & Event-Driven Architecture:** Removed fixed or unlimited throughput claims; separated broker delivery attempts, Kafka transaction scope, and effectively-once business outcomes; made deduplication atomic and tied retry, DLQ, replication, and upgrade policy to explicit failure requirements.
- **Chapter 8 — Load Balancing & Traffic Management:** Replaced zero-downtime and fixed-RTO claims with detection, draining, dependency, capacity, and validation requirements; improved health-check/deadline guidance and framed internal identity, authorization, segmentation, and encryption as threat-model decisions.
- **Chapter 9 — Monitoring, Observability & Alerting:** Distinguished time-based and request-based error budgets; made availability/freshness SLIs user-intent based; clarified percentile use; replaced fixed telemetry retention schedules with purpose-, compliance-, query-, and cost-driven policy.
- **Chapter 10 — Security Fundamentals:** Updated zero-trust, TLS, secret delivery, CSRF, JWT, vulnerability prioritization, credential containment, and compliance guidance; added current NIST, IETF OAuth BCP, OWASP ASVS, and PCI SSC primary references.
- **Chapter 11 — DevOps, CI/CD & Infrastructure as Code:** Clarified reproducible artifact promotion, IaC state/drift boundaries, Kubernetes request/limit semantics, release rollback constraints, and policy layers; added a Mermaid delivery-gate and progressive-rollout flow.
- **Chapter 12 — Cloud Platforms:** Reframed provider selection around requirements, quotas, failure domains, operations, and exit constraints; clarified shared responsibility, object-storage limits, presigned URL risk, managed-service trade-offs, and migration value; added a cloud service-model decision flow.
- **Chapter 13 — System Engineer Cheat Sheets:** Converted fixed latency/peak/retention guarantees into measured operational references; corrected messaging and replication formulas; added command safety context and a visual incident-response loop.
- **Chapter 14 — Real-World Case Studies:** Added an explicit evidence boundary separating teaching assumptions from documented company architecture, plus a reusable visual case-study analysis chain from requirements through evolution triggers.
- **Chapter 15 — Interview Preparation Guide:** Corrected learning objectives and technology-prescription language; added a visual system-design interview flow, an adaptable 45-minute time budget, and progressive practice levels.

### Fixed

- Corrected Chapter 1 capacity calculations, including replicated tweet storage and the URL-shortener traffic/storage model.
- Corrected Chapter 1 weighted decision scores and removed contradictions between deletable redirects and immutable year-long caching.
- Corrected Chapter 2 private-range classification and subnet-count calculations.
- Corrected Chapter 3's claim that at-least-once delivery guarantees eventual delivery.
- Corrected Chapter 4's 20% growth example, which previously used 100% growth results.
- Corrected Chapter 5 backup checksum verification and replaced obsolete TCP/PostgreSQL terminology and examples where encountered.
- Corrected Chapter 6 weighted-latency and cache-consistency claims and removed unsafe raw-key metric guidance.
- Corrected Chapter 7 SQS throughput/order descriptions and exactly-once boundary claims.
- Corrected Chapter 8 health-check text, fixed an accidental non-English line, and removed topology-based RTO guarantees.
- Corrected Chapter 9 error-budget, freshness-SLI, and trace-retention examples.
- Corrected Chapter 10 claims that mTLS alone constitutes zero trust and that fixed vulnerability severity order is sufficient for remediation priority.
- Corrected Chapter 11 CPU-request, immutable-infrastructure, Terraform-state, and instant-rollback overstatements.
- Corrected Chapter 12 unlimited object-storage and uniform managed-service benefit claims.
- Corrected Chapter 13 exactly-once/unlimited replay wording, unsafe incident restart advice, and obsolete command recommendations.
- Corrected Chapter 14 attribution risk by labeling unverified architecture details as illustrative.
- Corrected Chapter 15's incomplete learning objective and overly prescriptive database comparison.

### Visual Improvements

- Added focused Mermaid diagrams for delivery pipelines, cloud service selection, incident response, case-study analysis, and system-design interview flow.
- Kept diagrams intentionally small and paired them with the chapter text so they remain useful in rendered Markdown and source review.

### Added

- Began **Appendix E — Exercise Solutions and Evaluation Guides** with a reusable evaluation rubric and complete worked solutions for Chapters 1–3.
- Added calculation tables, decision matrices, Mermaid flows, failure analysis, acceptance criteria, and alternative-aware guidance to the first Appendix E batch.
- Linked Appendix E from the README appendices index with its current completion status.
- Expanded Appendix E with complete worked solutions for Chapters 4–8, covering scaling gates, sharding, caching, CQRS/event sourcing, database migration and DR, messaging reliability, backpressure, global routing, health checks, and proxy validation.
- Expanded Appendix E with verified worked solutions for Chapters 9–12, covering SLO mathematics, structured telemetry, OpenTelemetry tracing, incident and alert quality, STRIDE and zero trust, secrets operations, CI/CD, Terraform and GitOps governance, cloud architecture, multi-region recovery, and managed-service migration.
- Added Mermaid architecture and sequence diagrams plus official 2026-current verification links for observability, security, delivery performance, Terraform state, cloud reliability, and managed Kafka guidance.
- Completed Appendix E for Chapters 13–15 with performance triage, feature-flag and on-call runbooks, evidence-aware industry case studies, a production outage analysis, web-crawler design, behavioral evaluation, written-design rubrics, and a measurable three-month study plan.
- Marked Appendix E complete for all 15 chapters and added primary-source verification links for X/Twitter, Meta, Cloudflare, Google SRE, crawler guidance, and RFC 9309.
- Added the Roadmap Step 3 practical examples collection under `examples/`: evidence-first network troubleshooting, PostgreSQL index analysis, cache stampede protection, atomic idempotent message consumption, OpenTelemetry instrumentation, and Kubernetes rollout/rollback.
- Added Appendix F — Troubleshooting Playbooks for HTTP 5xx, DNS, TCP timeouts, CPU/memory saturation, disk/inode exhaustion, database pools, Kafka lag, Kubernetes CrashLoopBackOff, certificate failures, BGP route loss, and cache stampedes.
- Hardened GitHub Actions CI to work without deleted local package/config files, validate Markdown and Mermaid blocks correctly, and skip optional Vale/cspell checks when their configuration is absent.
- Added a repository-level `.markdownlint.json` policy that preserves the handbook's diagram/code style while enforcing the remaining Markdown defaults.
- Added additional decision tables, capacity calculations, acceptance criteria, rollback guidance, and focused Mermaid diagrams to the second solution batch.

### Planned
- Interactive web version with search
- PDF/EPUB export
- Translations (TR, ES, FR, DE, JP, CN)
- Video walkthroughs for each chapter
- Expanded case studies (Stripe, Shopify, Discord, WhatsApp)
- Kubernetes deep-dive chapter
- eBPF and observability chapter
- Platform engineering chapter
- Cost optimization deep-dive

---

## Versioning Policy

- **Major**: Structural reorganization, chapter additions/removals
- **Minor**: New sections, significant content additions, new case studies
- **Patch**: Typos, bug fixes, link updates, small clarifications

---

## Attribution

This handbook draws inspiration and structure from excellent community resources:
- [system-design-primer](https://github.com/donnemartin/system-design-primer) by Donne Martin
- [system-design](https://github.com/karanpratapsingh/system-design) by Karan Pratap Singh
- [awesome-system-design-resources](https://github.com/ashishps1/awesome-system-design-resources) by Ashish Patel
- [System-Engineer-Cheat-Sheets](https://github.com/nduytg/System-Engineer-Cheat-Sheets) by Nguyen Duy
- [Agile Model-Based Systems Engineering Cookbook](https://github.com/PacktPublishing/Agile-Model-Based-Systems-Engineering-Cookbook) by Packt Publishing

---

> See [CONTRIBUTING.md](./CONTRIBUTING.md) for how to contribute to future releases.
