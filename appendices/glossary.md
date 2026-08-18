# Appendix A: Glossary of Terms

This glossary provides concise definitions for the most important terms used throughout this handbook. Terms are grouped by domain for easier navigation.

---

## Systems Architecture

| Term | Definition |
|------|------------|
| **Monolith** | A single deployable unit containing all application functionality. |
| **Microservices** | Architecture style decomposing application into small, independently deployable services communicating over network. |
| **Modular Monolith** | Single deployable unit with internal module boundaries enforcing separation of concerns. |
| **Service Mesh** | Infrastructure layer managing service-to-service communication (mTLS, routing, observability). |
| **Sidecar** | Helper process deployed alongside main application container sharing network and storage namespaces. |
| **API Gateway** | Entry point handling routing, authentication, rate limiting, and protocol translation. |
| **Backplane** | Shared infrastructure enabling communication between services (message bus, service mesh). |
| **Cell-based Architecture** | Failure isolation pattern partitioning system into independent cells. |
| **CAP Theorem** | Consistency, Availability, Partition Tolerance — pick two during network partition. |
| **PACELC** | Extension of CAP: if Partition then Availability vs Consistency, Else Latency vs Consistency. |
| **Eventual Consistency** | Model where all replicas converge given sufficient time without new writes. |
| **Strong Consistency** | Model where reads reflect the most recent write (linearizability). |
| **Causal Consistency** | Model where causally related operations are seen in order. |
| **Read-Your-Writes Consistency** | Model where a client sees its own writes immediately. |
| **Monotonic Reads** | Model where successive reads never move backward in time. |
| **Saga** | Sequence of local transactions with compensating actions for rollback. |
| **Two-Phase Commit (2PC)** | Blocking protocol coordinating distributed transaction commit across participants. |
| **Idempotency** | Property where repeated identical requests produce same effect as single request. |
| **Idempotency Key** | Client-generated unique value enabling server to deduplicate retries safely. |
| **Circuit Breaker** | Pattern preventing calls to failing dependency and failing fast. |
| **Bulkhead** | Isolation pattern limiting resource consumption per dependency. |
| **Timeout** | Maximum time to wait for response before considering operation failed. |
| **Retry** | Repeating failed operation, often with exponential backoff and jitter. |
| **Dead Letter Queue (DLQ)** | Queue holding messages that failed processing after retries exhausted. |

---

## Distributed Systems

| Term | Definition |
|------|------------|
| **Consensus** | Agreement among distributed nodes on a single value despite failures. |
| **Raft** | Leader-based consensus algorithm with understandable guarantees. |
| **Paxos** | Family of consensus protocols proven correct but complex. |
| **ZooKeeper** | Coordination service providing distributed consensus, configuration, and naming. |
| **etcd** | Distributed key-value store using Raft for consensus. |
| **Consul** | Service mesh and service discovery using Raft. |
| **Leader Election** | Process selecting single coordinator among peers. |
| **Quorum** | Minimum number of nodes required to make progress (typically majority). |
| **Split Brain** | Condition where network partition creates multiple leaders believing they are sole authority. |
| **Vector Clock** | Logical timestamp tracking causality across distributed nodes. |
| **Lamport Clock** | Logical timestamp providing partial ordering of events. |
| **Hybrid Logical Clock (HLC)** | Combination of physical and logical time for causal ordering. |
| **TrueTime** | Google's globally synchronized clock with bounded uncertainty. |
| **NTP** | Network Time Protocol for clock synchronization. |
| **PTP** | Precision Time Protocol for sub-microsecond synchronization. |
| **Gossip Protocol** | Probabilistic peer-to-peer dissemination for membership and state. |
| **SWIM** | Scalable Weakly-consistent Infection-style Membership protocol. |
| **Failure Detector** | Component suspecting and confirming node failures. |
| **Phi Accrual** | Adaptive failure detector computing suspicion level over time. |
| **State Machine Replication** | Replicating deterministic state machine across nodes for fault tolerance. |

---

## Networking

| Term | Definition |
|------|------------|
| **OSI Model** | 7-layer conceptual framework for network communication. |
| **TCP/IP Model** | 4-layer practical model used in Internet architecture. |
| **CIDR** | Classless Inter-Domain Routing notation for IP address ranges. |
| **Subnetting** | Dividing network into smaller logical segments. |
| **VLAN** | Virtual LAN segmenting broadcast domain at Layer 2. |
| **BGP** | Border Gateway Protocol — inter-domain routing protocol of the Internet. |
| **OSPF** | Open Shortest Path First — interior gateway routing protocol. |
| **IS-IS** | Intermediate System to Intermediate System — link-state interior routing protocol. |
| **VXLAN** | Virtual Extensible LAN — Layer 2 over Layer 3 overlay using UDP encapsulation. |
| **EVPN** | Ethernet VPN — control plane for VXLAN using BGP extensions. |
| **Spine-Leaf** | Two-tier data center fabric with predictable latency and non-blocking paths. |
| **Anycast** | Routing to nearest of multiple nodes advertising same IP prefix. |
| **ECMP** | Equal-Cost Multi-Path — load balancing across multiple equal-cost paths. |
| **MTU** | Maximum Transmission Unit — largest packet size for a network path. |
| **Jumbo Frames** | Ethernet frames larger than standard 1500 bytes (typically 9000). |
| **TCP Handshake** | Three-way SYN, SYN-ACK, ACK establishing TCP connection. |
| **TCP Slow Start** | Congestion control algorithm gradually increasing sending rate. |
| **TCP Fast Open** | Sending data in initial SYN packet to reduce handshake latency. |
| **QUIC** | UDP-based transport protocol with built-in encryption and multiplexing. |
| **HTTP/3** | HTTP over QUIC providing multiplexed streams without head-of-line blocking. |
| **TLS** | Transport Layer Security — cryptographic protocol for secure communication. |
| **mTLS** | Mutual TLS — both client and server authenticate via certificates. |
| **SPIFFE** | Secure Production Identity Framework for Everyone — workload identity standard. |
| **SPIRE** | SPIFFE Runtime Environment — implementation of SPIFFE. |
| **Zero Trust** | Security model verifying every request regardless of network location. |
| **WAF** | Web Application Firewall — inspecting HTTP traffic for attacks. |
| **DDoS** | Distributed Denial of Service — overwhelming target with traffic from many sources. |
| **Anycast** | Single IP announced from multiple locations for proximity routing. |
| **DNS** | Domain Name System — hierarchical naming system mapping names to addresses. |
| **DoH** | DNS over HTTPS — encrypting DNS queries in HTTPS. |
| **DoT** | DNS over TLS — encrypting DNS queries in TLS. |
| **DNSSEC** | DNS Security Extensions — cryptographic validation of DNS responses. |
| **ECS** | EDNS Client Subnet — passing client subnet to authoritative DNS for better routing. |
| **SRV Record** | DNS record specifying service location with host and port. |

---

## Load Balancing & Traffic

| Term | Definition |
|------|------------|
| **Layer 4 Load Balancer** | Operates at transport layer (TCP/UDP), forwarding without payload inspection. |
| **Layer 7 Load Balancer** | Operates at application layer (HTTP/gRPC), inspecting and routing based on content. |
| **Round Robin** | Distributing requests sequentially across backends. |
| **Least Connections** | Sending new request to backend with fewest active connections. |
| **Consistent Hashing** | Hash-based routing minimizing remapping when backend set changes. |
| **IP Hash** | Hashing source IP to achieve sticky sessions without cookies. |
| **Health Check** | Active or passive probe determining backend availability. |
| **Readiness Probe** | Determines if instance can serve traffic. |
| **Liveness Probe** | Determines if instance should be restarted. |
| **Connection Draining** | Gracefully closing existing connections before instance termination. |
| **Rate Limiting** | Controlling request rate per client, IP, or identity. |
| **Token Bucket** | Rate limiting algorithm allowing burst up to bucket capacity. |
| **Leaky Bucket** | Rate limiting algorithm smoothing output at constant rate. |
| **Circuit Breaker** | Failing fast when upstream dependency shows degradation. |
| **Retry Storm** | Cascading retries amplifying load on already failing dependency. |
| **Canary Release** | Gradually shifting traffic to new version while monitoring metrics. |
| **Blue-Green Deployment** | Maintaining two identical environments and switching traffic atomically. |
| **Shadow Traffic** | Duplicating production traffic to new version without affecting responses. |
| **Feature Flag** | Runtime toggle controlling feature visibility without deployment. |

---

## Databases & Storage

| Term | Definition |
|------|------------|
| **ACID** | Atomicity, Consistency, Isolation, Durability — transaction guarantees. |
| **BASE** | Basically Available, Soft state, Eventual consistency — alternative to ACID. |
| **OLTP** | Online Transaction Processing — short, frequent transactions. |
| **OLAP** | Online Analytical Processing — complex queries over large datasets. |
| **HTAP** | Hybrid Transactional/Analytical Processing — single system serving both. |
| **Sharding** | Horizontal partitioning distributing data across multiple databases. |
| **Partitioning** | Dividing table into smaller physical pieces (range, hash, list). |
| **Replication** | Copying data to multiple nodes for availability and read scaling. |
| **Single-Leader** | One primary accepting writes, replicating to secondaries. |
| **Multi-Leader** | Multiple primaries accepting writes, resolving conflicts. |
| **Leaderless** | Any replica can accept writes, quorum for reads and writes. |
| **Synchronous Replication** | Waiting for replica acknowledgment before committing write. |
| **Asynchronous Replication** | Acknowledging write locally, replicating in background. |
| **Semi-Synchronous** | Waiting for at least one replica before committing. |
| **RPO** | Recovery Point Objective — maximum acceptable data loss. |
| **RTO** | Recovery Time Objective — maximum acceptable downtime. |
| **PITR** | Point-In-Time Recovery — restoring database to specific moment. |
| **WAL** | Write-Ahead Log — sequential log of changes for durability and replication. |
| **LSM Tree** | Log-Structured Merge Tree — write-optimized storage engine. |
| **B-Tree** | Balanced tree structure for ordered key-value storage. |
| **Covering Index** | Index containing all columns needed by query avoiding table lookup. |
| **Partial Index** | Index built on subset of rows matching predicate. |
| **Expression Index** | Index on function result of columns. |
| **VACUUM** | PostgreSQL process reclaiming space from dead tuples. |
| **ANALYZE** | PostgreSQL command updating planner statistics. |
| **Connection Pooling** | Reusing database connections to reduce overhead. |
| **PgBouncer** | Lightweight connection pooler for PostgreSQL. |
| **Vitess** | MySQL sharding middleware with connection pooling and query routing. |
| **Citus** | PostgreSQL extension turning it into distributed database. |

---

## Caching

| Term | Definition |
|------|------------|
| **Cache-Aside** | Application manages cache population and invalidation explicitly. |
| **Read-Through** | Cache handles reads and populates from source on miss. |
| **Write-Through** | Cache writes to source synchronously before acknowledging. |
| **Write-Behind** | Cache acknowledges write, persists to source asynchronously. |
| **Refresh-Ahead** | Proactively refreshing entries before TTL expiration. |
| **Cache Stampede** | Thundering herd of requests hitting origin on cache miss. |
| **XFetch** | Probabilistic early expiration preventing stampede. |
| **Stale-While-Revalidate** | Serving stale content while asynchronously refreshing. |
| **Negative Caching** | Caching "not found" responses to protect origin. |
| **Cache Invalidation** | Removing or updating cached entries when source changes. |
| **TTL** | Time To Live — duration after which cache entry expires. |
| **Cache Hit Ratio** | Fraction of requests served from cache vs total requests. |
| **CDN** | Content Delivery Network — geographically distributed cache. |
| **Edge Cache** | Cache located at network edge close to users. |
| **Varnish** | HTTP accelerator and reverse proxy cache. |
| **Redis** | In-memory data structure store used as cache, queue, or database. |
| **Memcached** | Simple, fast, distributed memory object caching system. |
| **LRU** | Least Recently Used — eviction policy removing oldest accessed item. |
| **LFU** | Least Frequently Used — eviction policy removing least accessed item. |
| **ARC** | Adaptive Replacement Cache — combining LRU and LFU. |

---

## Messaging & Event Streaming

| Term | Definition |
|------|------------|
| **Message Queue** | Point-to-point channel delivering each message to one consumer. |
| **Pub/Sub** | Publish-subscribe pattern delivering message to all interested subscribers. |
| **Event Streaming** | Append-only log retaining messages for replay by multiple consumer groups. |
| **Kafka** | Distributed event streaming platform with partitioned, replicated logs. |
| **Pulsar** | Cloud-native messaging and streaming platform with tiered storage. |
| **NATS** | Lightweight messaging system with JetStream for persistence. |
| **Redpanda** | Kafka-compatible streaming platform written in C++ without JVM. |
| **RabbitMQ** | Message broker implementing AMQP with flexible routing. |
| **SQS** | Amazon Simple Queue Service — fully managed queue. |
| **SNS** | Amazon Simple Notification Service — fully managed pub/sub. |
| **EventBridge** | Amazon serverless event bus with schema registry. |
| **Topic** | Named category or feed to which messages are published. |
| **Partition** | Ordered segment of a topic enabling parallel consumption. |
| **Consumer Group** | Set of consumers sharing subscription, each partition consumed by one. |
| **Offset** | Position within partition indicating next message to read. |
| **Consumer Lag** | Difference between latest produced offset and committed consumer offset. |
| **Rebalance** | Redistribution of partition ownership among consumer group members. |
| **Schema Registry** | Service managing and enforcing message schema compatibility. |
| **Avro** | Binary serialization format with schema evolution support. |
| **Protobuf** | Protocol Buffers — language-neutral serialization with schema. |
| **Idempotent Consumer** | Consumer producing same result when processing same message multiple times. |
| **Exactly-Once** | End-to-end guarantee combining at-least-once delivery with idempotent processing. |
| **Dead Letter Queue** | Queue capturing messages that failed processing permanently. |
| **Backpressure** | Mechanism allowing consumers to signal producers to slow down. |

---

## Monitoring & Observability

| Term | Definition |
|------|------------|
| **Monitoring** | Collecting and alerting on predefined metrics for known failure modes. |
| **Observability** | Ability to understand system internal state from external outputs. |
| **SLI** | Service Level Indicator — quantifiable measure of service behavior. |
| **SLO** | Service Level Objective — target value for an SLI over time window. |
| **SLA** | Service Level Agreement — contractual commitment with consequences. |
| **Error Budget** | Inverse of SLO — allowable failure quota for risk-taking. |
| **Burn Rate** | Speed at which error budget is consumed. |
| **Golden Signals** | Latency, Traffic, Errors, Saturation — four key service metrics. |
| **RED Method** | Rate, Errors, Duration — service-centric metric methodology. |
| **USE Method** | Utilization, Saturation, Errors — resource-centric metric methodology. |
| **Metric** | Numerical measurement over time (counter, gauge, histogram). |
| **Counter** | Monotonically increasing cumulative value. |
| **Gauge** | Instantaneous value that can go up or down. |
| **Histogram** | Distribution of observed values in buckets. |
| **Summary** | Client-side calculated quantiles (deprecated in favor of histograms). |
| **Log** | Discrete event record with timestamp and structured fields. |
| **Structured Log** | Log record as key-value pairs (typically JSON). |
| **Trace** | End-to-end request execution across services. |
| **Span** | Single operation within a trace with start time, end time, and metadata. |
| **Trace Context** | Standardized headers propagating trace identity (W3C traceparent). |
| **Sampling** | Selecting subset of traces to record due to volume constraints. |
| **Head-Based Sampling** | Decision at trace start whether to record full trace. |
| **Tail-Based Sampling** | Decision at trace end based on outcome (errors, latency). |
| **OpenTelemetry** | Vendor-neutral observability framework for instrumentation. |
| **Prometheus** | Pull-based metrics collection and alerting system. |
| **Grafana** | Visualization platform for metrics, logs, and traces. |
| **Loki** | Log aggregation system optimized for label-based indexing. |
| **Tempo** | Distributed tracing backend integrated with Grafana. |
| **Jaeger** | End-to-end distributed tracing system. |
| **Alert** | Notification triggered when metric exceeds threshold or condition. |
| **Alert Fatigue** | Desensitization due to excessive or non-actionable alerts. |
| **Runbook** | Documented procedure for responding to specific alerts or incidents. |
| **Postmortem** | Blameless analysis of incident timeline, root cause, and remediation. |

---

## CI/CD & Infrastructure

| Term | Definition |
|------|------------|
| **CI** | Continuous Integration — merging code frequently with automated verification. |
| **CD** | Continuous Delivery/Deployment — automating release to environments. |
| **Pipeline** | Automated sequence of steps from commit to production. |
| **Quality Gate** | Automated check blocking promotion if criteria not met. |
| **Trunk-Based Development** | Short-lived branches or direct commits to main with feature flags. |
| **GitFlow** | Branching model with develop, release, and hotfix branches. |
| **IaC** | Infrastructure as Code — managing infrastructure through machine-readable definitions. |
| **Terraform** | Declarative IaC tool using HCL with provider ecosystem. |
| **Pulumi** | IaC tool using general-purpose programming languages. |
| **CloudFormation** | AWS native IaC service using JSON/YAML templates. |
| **State File** | Terraform's mapping of configuration to real-world resources. |
| **Remote Backend** | Shared state storage with locking for team collaboration. |
| **Module** | Reusable IaC component accepting inputs and producing outputs. |
| **Drift** | Difference between desired state (code) and actual state (cloud). |
| **GitOps** | Operating model where Git is single source of truth for desired state. |
| **ArgoCD** | GitOps continuous delivery tool for Kubernetes. |
| **Flux** | GitOps toolkit for Kubernetes with progressive delivery. |
| **Helm** | Package manager for Kubernetes applications. |
| **Kustomize** | Template-free customization of Kubernetes manifests. |
| **Blue-Green** | Deployment maintaining two identical production environments. |
| **Canary** | Gradual rollout to subset of users with automated rollback. |
| **Rolling Update** | Incremental replacement of instances maintaining availability. |
| **Immutable Infrastructure** | Replacing rather than modifying deployed components. |
| **Artifact** | Built and versioned deployable unit (container image, binary). |
| **SBOM** | Software Bill of Materials — inventory of components and dependencies. |
| **SAST** | Static Application Security Testing — analyzing source code. |
| **DAST** | Dynamic Application Security Testing — analyzing running application. |
| **SCA** | Software Composition Analysis — identifying vulnerable dependencies. |
| **DORA Metrics** | Deployment Frequency, Lead Time, MTTR, Change Failure Rate. |

---

## Security

| Term | Definition |
|------|------------|
| **Authentication** | Verifying identity of user or system (who are you?). |
| **Authorization** | Determining permitted actions for authenticated identity (what can you do?). |
| **Zero Trust** | Security model requiring verification for every request. |
| **mTLS** | Mutual TLS — both parties present and verify certificates. |
| **SPIFFE** | Standard for identifying workloads with cryptographically verifiable identity. |
| **JWT** | JSON Web Token — compact, URL-safe token format for claims. |
| **OAuth 2.0** | Authorization framework for delegated access. |
| **OIDC** | OpenID Connect — identity layer on top of OAuth 2.0. |
| **RBAC** | Role-Based Access Control — permissions assigned to roles. |
| **ABAC** | Attribute-Based Access Control — policies evaluated against attributes. |
| **ReBAC** | Relationship-Based Access Control — permissions derived from graph relationships. |
| **Secret** | Sensitive value (password, key, token) requiring protection. |
| **Vault** | HashiCorp Vault — secrets management with dynamic secrets and leasing. |
| **Rotation** | Periodically replacing secrets to limit exposure window. |
| **Least Privilege** | Granting minimum permissions necessary for function. |
| **WAF** | Web Application Firewall — filtering malicious HTTP requests. |
| **SQL Injection** | Attack injecting malicious SQL through unsanitized input. |
| **XSS** | Cross-Site Scripting — injecting malicious scripts into web pages. |
| **CSRF** | Cross-Site Request Forgery — forcing authenticated user to execute unwanted action. |
| **CSP** | Content Security Policy — HTTP header restricting resource loading. |
| **HSTS** | HTTP Strict Transport Security — enforcing HTTPS. |
| **SAST/DAST/SCA** | Security testing methodologies (static, dynamic, composition). |
| **SOC 2** | Service Organization Control 2 — audit for security, availability, confidentiality. |
| **ISO 27001** | International standard for information security management systems. |
| **PCI DSS** | Payment Card Industry Data Security Standard. |
| **GDPR** | General Data Protection Regulation — EU data privacy law. |

---

## Cloud & Platform

| Term | Definition |
|------|------------|
| **IaaS** | Infrastructure as a Service — virtualized compute, storage, network. |
| **PaaS** | Platform as a Service — managed runtime and services for applications. |
| **SaaS** | Software as a Service — fully managed applications. |
| **FaaS** | Function as a Service — event-driven serverless compute. |
| **CaaS** | Containers as a Service — managed container orchestration. |
| **VPC/VNet** | Virtual Private Cloud/Network — isolated network segment in cloud. |
| **Subnet** | IP range within VPC associated with availability zone. |
| **Security Group** | Stateful firewall at instance level. |
| **NACL** | Network ACL — stateless firewall at subnet level. |
| **NAT Gateway** | Managed NAT enabling private subnet egress to internet. |
| **Internet Gateway** | VPC component enabling bidirectional internet communication. |
| **VPC Endpoint** | Private connection to AWS services without internet gateway. |
| **Transit Gateway** | Hub connecting multiple VPCs and on-premise networks. |
| **Direct Connect / ExpressRoute / Interconnect** | Dedicated network connection to cloud provider. |
| **CDN** | Content Delivery Network — edge caching for global low latency. |
| **Load Balancer** | Distributing traffic across targets (ALB, NLB, CLB, GLB). |
| **Auto Scaling** | Automatically adjusting capacity based on metrics or schedule. |
| **Spot / Preemptible** | Discounted interruptible compute capacity. |
| **Reserved / Savings Plans** | Committed use discounts for predictable workloads. |
| **FinOps** | Financial Operations — collaborative cloud cost management. |
| **Multi-Cloud** | Using multiple cloud providers simultaneously. |
| **Hybrid Cloud** | Combining on-premise and cloud infrastructure. |

---

## Interview Terminology

| Term | Definition |
|------|------------|
| **System Design Interview** | Open-ended architecture problem evaluating process and depth. |
| **Clarifying Questions** | Asking about scale, consistency, latency, constraints before designing. |
| **Back-of-the-Envelope** | Quick capacity estimation using round numbers and known constants. |
| **API Contract** | Request/response definitions, error codes, versioning strategy. |
| **Data Model** | Entity-relationship diagram with access patterns and keys. |
| **High-Level Design** | Component diagram showing services, storage, messaging, edge. |
| **Deep Dive** | Detailed analysis of bottleneck, sharding, replication, consistency. |
| **Trade-off Analysis** | Comparing alternatives with explicit pros, cons, and rationale. |
| **Production Readiness** | Addressing observability, security, deployment, DR, cost. |
| **STAR Method** | Situation, Task, Action, Result — structure for behavioral answers. |
| **DORA Metrics** | Four key delivery performance indicators. |
| **Whiteboard Coding** | Writing code on physical or virtual whiteboard during interview. |

---

> **Quick Reference**: Use `Ctrl+F` / `Cmd+F` to search for specific terms. For terms not listed, consult the chapter where the concept is introduced.