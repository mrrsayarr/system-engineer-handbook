# Chapter 4: Scalability & Performance Patterns

> **Estimated Time:** 5–7 hours | **Prerequisites:** Chapters 1–3<br>
> **Last reviewed:** 2026-08-31 | **Level:** Foundation → applied → production judgment

---

## 🎯 Learning Objectives

By the end of this chapter, you will be able to:

1. **Distinguish horizontal vs vertical scaling** and choose correctly
2. **Apply caching patterns** strategically throughout the stack
3. **Implement database sharding** with consistent hashing
4. **Design multi-tier architectures** for scale-out workloads
5. **Optimize performance** through profiling, indexing, and async patterns
6. **Apply CDN, edge computing, and modern scaling primitives**
7. **Plan capacity** based on growth models and SLO targets

---

## 4.1 The Scalability Mindset

### What is Scalability?

> A system's ability to handle a defined increase in load while continuing to
> meet its service objectives at an acceptable marginal cost. Every design has
> a scaling envelope; discovering its next bottleneck is part of the work.

### Two Dimensions of Scale

```
LOAD INCREASE → MORE RESOURCES              LOAD INCREASE → SAME RESOURCES
                                           
SCALE OUT (Horizontal)                      SCALE UP (Vertical)
├─ Add more instances                       ├─ Bigger instance type
├─ Stateless preferred                       ├─ More CPU, RAM, disk
├─ Cost depends on efficiency and overhead   ├─ Often faces diminishing returns
├─ Requires distribution and load balancing  ├─ Failure domain grows with the node
├─ Eventual scale limit (DB)                ├─ Hard ceiling (largest SKU)
└─ Complex (consistency, ops)                └─ Simple but capped
```

### Scaling Decision Matrix

| Factor | Prefer Horizontal | Prefer Vertical |
|--------|-------------------|-----------------|
| Stateless services | ✓ | |
| Stateful (DB) | | ✓ (until sharding needed) |
| Spiky traffic | ✓ (autoscaling) | |
| Predictable load | | ✓ (simpler) |
| Team has automation | ✓ | |
| Team has DBAs | Either | |
| Cost-sensitive | | ✓ (less overhead) |

---

## 4.2 The 12-Factor App for Scalability

```
┌─────────────────────────────────────────────────────────────┐
│  12-Factor Principles (adapted for scale)                    │
├─────────────────────────────────────────────────────────────┤
│  1.  Codebase          — One repo, many deploys             │
│  2.  Dependencies      — Explicit, isolated                  │
│  3.  Config            — Environment vars, not code         │
│  4.  Backing Services  — Treat as attached resources         │
│  5.  Build, Release, Run — Strict separation                │
│  6.  Processes         — Stateless, share-nothing           │
│  7.  Port Binding      — Self-contained services            │
│  8.  Concurrency       — Scale out via process model        │
│  9.  Disposability     — Fast startup, graceful shutdown    │
│  10. Dev/Prod Parity   — Same stack, config-by-env          │
│  11. Logs              — Event streams (stdout → aggregator)│
│  12. Admin Processes   — One-off as normal processes        │
└─────────────────────────────────────────────────────────────┘

Beyond 12-factor:
• API-first design
• Telemetry as first-class
• Security automation (SAST/DAST/SCA)
• Disposable infrastructure (IaC)
• Anti-fragility (chaos engineering)
```

---

## 4.3 Stateless vs Stateful Services

### Stateless Service Pattern

```python
# Stateless API server — session in Redis, not memory
from fastapi import FastAPI, Depends
import redis

app = FastAPI()
cache = redis.Redis(host='redis-cluster', port=6379)

@app.get("/user/{user_id}")
async def get_user(user_id: str, request: Request):
    session_id = request.cookies.get("sid")
    user_data = cache.get(f"session:{session_id}")
    if not user_data:
        raise HTTPException(401)
    # Process and return
    return {"user_id": user_id}

# Now we can run 1000 instances behind a load balancer
# Any instance can handle any request
# Add/remove instances freely
```

### Stateful Considerations

```
Stateful services can't just spin up/down:
  • Local disk (mitigation: external storage)
  • In-memory state (mitigation: stateful sidecars, external store)
  • TCP connections (mitigation: connection draining)
  • Long-running transactions (mitigation: idempotent retries)

Patterns:
  • Externalize state to DB/cache
  • Use sticky sessions only when necessary
  • Implement graceful shutdown (SIGTERM → drain → close)
  • Pre-warm caches on startup
```

---

## 4.4 Autoscaling Strategies

### Reactive Autoscaling (Threshold-Based)

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 100
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

### Predictive Autoscaling

```python
# Time-series forecasting (Prophet, ARIMA, LSTM)
# Use historical load patterns + calendar events
# Pre-scale before known peaks (Black Friday, product launches)

# AWS Predictive Scaling
# Uses ML to forecast traffic and provision ahead of time

# KEDA + event-driven scaling
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: kafka-consumer-scaler
spec:
  scaleTargetRef:
    name: kafka-consumer
  triggers:
  - type: kafka
    metadata:
      bootstrapServers: kafka:9092
      consumerGroup: my-group
      lagThreshold: "100"
```

### Scaling Limits & Anti-Patterns

```
┌─────────────────────────────────────────────────────────────────┐
│  COMMON SCALING PITFALLS                                        │
├─────────────────────────────────────────────────────────────────┤
│  1. Cache stampede      — All replicas query DB simultaneously  │
│  2. Thundering herd     — Synchronized retries / reconnects     │
│  3. Slow instance boot  — Cold caches, JIT, dependencies        │
│  4. Connection storm     — All replicas open DB connections     │
│  5. Memory leaks amplified — Leak × N replicas = quick OOM     │
│  6. Cost overrun         — No scale-down / over-provisioning    │
│  7. Hot tenants          — One noisy neighbor blocks others     │
│  8. Slow scale-up        — Image pull, readiness probe timeout  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4.5 Caching Deep Dive

> *See Chapter 6 for full coverage — quick reference here*

### Caching Layers

```
┌─────────────────────────────────────────────────────────────┐
│  CACHE HIERARCHY (closest to user → closest to data)        │
├─────────────────────────────────────────────────────────────┤
│  Browser Cache       — Cache-Control, ETag, Service Worker  │
│  CDN Cache           — Cloudflare, CloudFront, Fastly        │
│  Edge Compute Cache  — Workers@Edge, Lambda@Edge            │
│  Application Cache   — In-process (Caffeine, Guava)         │
│  Distributed Cache   — Redis, Memcached, Hazelcast           │
│  Database Cache      — Buffer pool, query cache              │
│  OS Page Cache       — Kernel-managed memory                │
│  Hardware Cache      — CPU L1/L2/L3, SSD controller         │
└─────────────────────────────────────────────────────────────┘
```

### Cache Strategies Quick Reference

| Pattern | Read | Write | Use When |
|---------|------|-------|----------|
| **Cache-Aside** | App reads cache, falls back to DB | App writes DB, invalidates cache | General purpose |
| **Read-Through** | Cache reads DB | App writes cache | Cache-managed |
| **Write-Through** | — | Cache writes DB sync | Strong consistency |
| **Write-Behind** | — | Cache writes DB async | High write throughput |
| **Refresh-Ahead** | Auto-refresh before TTL | — | Predictable access |
| **Write-Around** | — | App writes DB, not cache | Write-heavy, rarely read |

---

## 4.6 Database Sharding & Partitioning

### Sharding Strategies

```python
# 1. Hash-Based Sharding
def get_shard(user_id, num_shards=16):
    return hash(user_id) % num_shards

# Pros: Even distribution
# Cons: Resharding hard, range queries across shards

# 2. Range-Based Sharding
def get_shard(timestamp):
    if timestamp < "2024-01-01": return "shard_a"
    elif timestamp < "2024-07-01": return "shard_b"
    else: return "shard_c"

# Pros: Range queries efficient
# Cons: Hotspots, uneven growth

# 3. Consistent Hashing
class ConsistentHash:
    def __init__(self, nodes, replicas=150):
        self.ring = {}
        for node in nodes:
            for i in range(replicas):
                key = self._hash(f"{node}:{i}")
                self.ring[key] = node
        self.sorted_keys = sorted(self.ring.keys())
    
    def get_node(self, key):
        h = self._hash(key)
        for ring_key in self.sorted_keys:
            if ring_key >= h:
                return self.ring[ring_key]
        return self.ring[self.sorted_keys[0]]
    
    def _hash(self, key):
        import hashlib
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

# Pros: Only K/N keys remap on add/remove
# Cons: Virtual nodes needed for balance

# 4. Directory-Based
# Lookup service maps entity → shard
# Pros: Flexible (geo, customer, etc.)
# Cons: Lookup is single point of failure
```

### Sharding Key Selection

```
GOOD SHARDING KEYS:
  • High cardinality (many distinct values)
  • Even distribution
  • Stable (doesn't change often)
  • Query-friendly (most queries include the key)

BAD SHARDING KEYS:
  • Low cardinality (status, country)
  • Skewed (small set of "celebrities")
  • Frequently updated
  • Not used in most queries

Example: For social network users
  shard_key = hash(user_id) % 1024  ← Good
  shard_key = hash(country) % 16   ← Bad (hotspot)
  shard_key = hash(user_id + tenant_id)  ← Tenant isolation bonus
```

### Handling Cross-Shard Operations

```
SCATTER-GATHER (cross-shard query):
  App → Shard1, Shard2, Sh3 (parallel)
  ← Result1, Result2, Result3
  App → Merge, sort, return

Downsides:
  • Latency = slowest shard
  • Resource consumption
  • No native transactions

Solutions:
  • Denormalize for query patterns
  • Use separate read store (CQRS)
  • Search index (Elasticsearch) for cross-shard
```

---

## 4.7 Database Replication Patterns

### Single-Leader (Primary-Replica)

```
                    WRITE
                      │
                      ▼
                  ┌────────┐
                  │ PRIMARY│
                  └────┬───┘
                       │ async/sync replication
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌────────┐     ┌────────┐     ┌────────┐
   │REPLICA │     │REPLICA │     │REPLICA │  ← READS
   └────────┘     └────────┘     └────────┘

✓ Simple, strong consistency on primary
✗ Write bottleneck (single primary)
✗ Replication lag affects reads
```

### Multi-Leader

```
   ┌────────┐              ┌────────┐
   │LEADER A│ ←──────────→ │LEADER B│
   └───┬────┘              └────┬───┘
       │      conflict           │
       │      resolution         │
       ▼                         ▼
   replicas                   replicas

✓ Geographic write locality
✓ Higher write availability
✗ Conflict resolution (last-write-wins, CRDTs, vector clocks)
✗ Complex; use cautiously
```

### Leaderless (Dynamo-style)

```
   WRITE to all replicas, configure W=2, R=2, N=3
   
   Client → W=2 of 3 must ack
   Client → R=2 of 3 must respond
   
   W + R > N → overlapping quorums; strong consistency still depends on
               versioning, conflict handling, and the quorum implementation
   W + R ≤ N → fast, possibly stale
   
   ✓ High availability, no leader bottleneck
   ✗ Sloppy quorums, hinted handoffs
   ✗ Conflict resolution at read (vector clocks, LWW)
```

### Read Replicas vs Read-Write Splitting

```python
# Route writes to primary, reads to replicas
class Router:
    def __init__(self, primary, replicas):
        self.primary = primary
        self.replicas = replicas
        self.replica_idx = 0
    
    async def read(self, query):
        replica = self.replicas[self.replica_idx % len(self.replicas)]
        self.replica_idx += 1
        return await replica.execute(query)
    
    async def write(self, query):
        return await self.primary.execute(query)
    
    async def read_your_writes(self, query, session_id):
        # After a write, route reads to primary briefly
        if await self._recently_wrote(session_id):
            return await self.primary.execute(query)
        return await self.read(query)
```

---

## 4.8 Connection Pooling

### Why Pool Connections?

```
Without pool:
  Request → Open TCP → TLS handshake → Auth → Query → Close
  Cost: ~5-50ms per request, file descriptors, memory
  
With pool:
  Request → Acquire from pool → Query → Release
  Cost: ~0.1ms per request, bounded resources
```

### Pool Sizing

```
FORMULA (PostgreSQL, Oracle):
  connections = ((core_count * 2) + effective_spindle_count)
  
  For 4 cores, SSD: (4*2) + 1 = 9 connections
  
  Why? Databases are slow on context switch.
  Each connection = ~10MB RAM.
  Too many connections = thrashing.

For applications:
  pool_size = (target_qps × avg_query_time) + buffer
  e.g., 1000 qps × 50ms = 50 concurrent + 20 buffer = 70
```

### PgBouncer (PostgreSQL Connection Pooler)

```ini
# pgbouncer.ini
[databases]
mydb = host=10.0.1.10 port=5432 dbname=mydb
mydb_ro = host=10.0.2.10 port=5432 dbname=mydb

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

# Pool modes
pool_mode = transaction  # connection per transaction (recommended)
# pool_mode = session     # connection per session
# pool_mode = statement   # connection per statement

max_client_conn = 10000
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 3
server_idle_timeout = 600
```

---

## 4.9 CDN & Edge Computing

### CDN Architecture

```
User (Tokyo) ──► CDN Edge (Tokyo) ──► MISS ──► Origin (US)
   │                │
   │                └─► HIT (cache) ◄──┘
   │
User (Berlin) ──► CDN Edge (Frankfurt) ──► MISS ──► Origin (EU)
                     │
                     └─► HIT (cache)
```

### CDN Caching Strategy

```nginx
# Cache-Control headers
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable, max-age=31536000";
}

location /api/ {
    add_header Cache-Control "private, no-cache";
    # Authenticated, never cache at CDN
}

location /public/ {
    add_header Cache-Control "public, max-age=300, stale-while-revalidate=60";
    # Cache 5min, serve stale up to 1min while revalidating
}

# Cache invalidation
# 1. URL purge: POST /cache/purge?url=...
# 2. Tag-based: purge by surrogate-key
# 3. Soft purge: mark stale, revalidate on next request
```

### Edge Computing (Cloudflare Workers, Lambda@Edge)

```javascript
// Cloudflare Worker — runs at edge in <1ms
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // A/B test routing at edge
    const cohort = request.headers.get('cf-ipcountry') === 'TR' ? 'A' : 'B';
    
    if (url.pathname.startsWith('/api/')) {
      // Cache API responses for 30s
      const cache = caches.default;
      const cached = await cache.match(request);
      if (cached) return cached;
      
      const response = await fetch(request);
      const newResponse = new Response(response.body, response);
      newResponse.headers.set('Cache-Control', 'max-age=30');
      ctx.waitUntil(cache.put(request, newResponse.clone()));
      return newResponse;
    }
    
    return fetch(request);
  }
};
```

---

## 4.10 Async Processing & Backpressure

### Synchronous vs Asynchronous

```
SYNCHRONOUS:
  Client → API → DB → Response (blocking)
  Latency: sum of all calls
  Throughput: limited by request lifecycle
  
ASYNCHRONOUS:
  Client → API → Queue → Response (ack)
                  │
                  └→ Worker → Process → DB (background)
  Latency: queue + worker processing
  Throughput: decoupled, scales independently
```

### Queue-Based Load Leveling

```python
# Producer: Accept work fast, queue it
@app.post("/orders")
async def create_order(order: Order):
    # Quick: validate, persist, enqueue
    order_id = str(uuid.uuid4())
    db.orders.insert({"id": order_id, **order.dict(), "status": "pending"})
    queue.publish("orders.process", {"id": order_id})
    return {"id": order_id, "status": "pending"}

# Consumer: Process at sustainable rate
def process_orders():
    while True:
        msg = queue.consume("orders.process")
        try:
            order = db.orders.get(msg["id"])
            # Heavy work: inventory, payment, shipping, email
            charge_payment(order)
            reserve_inventory(order)
            ship_order(order)
            send_confirmation(order)
            db.orders.update(order["id"], {"status": "complete"})
        except Exception as e:
            db.orders.update(order["id"], {"status": "failed", "error": str(e)})
            # Dead letter queue for permanent failures
```

### Backpressure Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│  BACKPRESSURE TECHNIQUES                                        │
├─────────────────────────────────────────────────────────────────┤
│  1. Bounded queues    — Reject when full, return 503/429         │
│  2. Rate limiting     — Per-client limits                        │
│  3. Circuit breakers  — Fail fast when downstream overwhelmed    │
│  4. Adaptive batching — Reduce batch size under pressure        │
│  5. Sampling          — Process subset, drop rest                │
│  6. Shedding          — Drop low-priority work first             │
└─────────────────────────────────────────────────────────────────┘
```

### Admission Control and Load Shedding

Autoscaling reacts after a threshold is crossed. Admission control protects the system during the delay between overload and added capacity by limiting work before threads, database connections, memory or queue slots are exhausted.

| Condition | Decision | Response | Reason |
|-----------|----------|----------|--------|
| Per-tenant budget exceeded | Reject | `429` + `Retry-After` | Fairness and abuse protection |
| Global concurrency full | Reject or queue briefly | `503` | Preserve healthy in-flight work |
| Queue age exceeds SLO | Drop low-priority jobs | DLQ/job failure | Stale work has lost value |
| Dependency circuit open | Fail fast or degrade | Cached/partial response | Prevent cascading failure |
| Critical memory pressure | Disable optional work | Reduced response | Keep critical path alive |

```python
import asyncio
from contextlib import asynccontextmanager

class ConcurrencyLimiter:
    def __init__(self, limit: int):
        self._slots = asyncio.Semaphore(limit)

    @asynccontextmanager
    async def admit(self, wait_seconds: float = 0.02):
        try:
            await asyncio.wait_for(self._slots.acquire(), timeout=wait_seconds)
        except TimeoutError as exc:
            raise RuntimeError("capacity exhausted") from exc
        try:
            yield
        finally:
            self._slots.release()

limiter = ConcurrencyLimiter(limit=200)
```

**Design rules:**

- Bound every queue; unbounded queues turn overload into memory exhaustion and tail latency.
- Reserve capacity for health checks, control-plane calls and high-priority traffic.
- Retry only idempotent work with exponential backoff and jitter.
- Shed based on queue age or deadline miss, not only queue length.
- Measure admitted, rejected, dropped and timed-out requests separately.

---

## 4.11 CQRS & Event Sourcing

### CQRS (Command Query Responsibility Segregation)

```
TRADITIONAL CRUD:
  Same model used for writes (commands) and reads (queries)
  
CQRS:
  ┌─────────┐                  ┌─────────┐
  │ COMMAND │                  │  QUERY  │
  │  SIDE   │                  │   SIDE  │
  ├─────────┤                  ├─────────┤
  │ Validate│                  │ Read    │
  │ Business│                  │ Models  │
  │ Logic   │                  │(denorm) │
  └────┬────┘                  └────▲────┘
       │                            │
       ▼                            │
   ┌───────┐    events     ┌─────────┴───┐
   │ Write │ ────────────► │   Read DB   │
   │  DB   │               │(projections)│
   └───────┘               └─────────────┘

BENEFITS:
  • Optimized read & write models independently
  • Scale read side aggressively
  • Different stores for different needs

TRADE-OFFS:
  • Eventual consistency
  • Increased complexity
  • Projection rebuilds
```

### Event Sourcing

```
INSTEAD OF: Current state, mutated by CRUD
USE: Append-only event log, current state = fold of events

Example: Bank Account
  Events:
    • AccountOpened(id=123, owner=Alice, initial=0)
    • MoneyDeposited(id=123, amount=100)
    • MoneyWithdrawn(id=123, amount=30)
    • MoneyDeposited(id=123, amount=50)
    
  Current State (projection):
    Balance = 0 + 100 - 30 + 50 = 120

BENEFITS:
  • Complete audit trail
  • Time travel (replay to any point)
  • New projections from old events
  • Domain events as integration contract

TRADE-OFFS:
  • Schema evolution (event versioning)
  • Storage growth (snapshot + compaction)
  • Complex queries (need projections)
  • Learning curve

TOOLS: EventStoreDB, Axon, Kafka + projections, MartenDB
```

---

## 4.12 Multi-Tier Architecture

### Classic N-Tier

```
┌─────────────────────────────────────────────────────────────┐
│  PRESENTATION TIER (CDN, Static, SPA, Mobile)               │
│     │                                                       │
│     ▼                                                       │
│  EDGE TIER (WAF, API Gateway, Rate Limiter)                 │
│     │                                                       │
│     ▼                                                       │
│  APPLICATION TIER (Stateless API, Workers)                  │
│     │                                                       │
│     ▼                                                       │
│  BUSINESS LOGIC TIER (Domain Services, Orchestrators)       │
│     │                                                       │
│     ▼                                                       │
│  DATA TIER (Databases, Caches, Object Storage)              │
│     │                                                       │
│     ▼                                                       │
│  INFRASTRUCTURE TIER (Networking, Storage, Compute)         │
└─────────────────────────────────────────────────────────────┘
```

### Layered Service Architecture

```
EDGE LAYER:
  CDN + WAF + API Gateway + Auth

STATEFUL SERVICES:
  Databases, Object Storage, Message Brokers
  Hard to scale — design for it from day 1

STATELESS SERVICES:
  Application servers, API handlers, workers
  Easy to scale horizontally

ASYNC WORKERS:
  Background jobs, batch processing, notifications
  Decouple from request path

ANALYTICS:
  Data warehouse, search index, ML pipeline
  Often separate tech stack
```

---

## 4.13 Performance Optimization

### Latency Optimization Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│  PERFORMANCE OPTIMIZATION (impact × effort)                     │
├─────────────────────────────────────────────────────────────────┤
│  HIGH IMPACT, LOW EFFORT:                                        │
│    • Enable compression (gzip, brotli)                          │
│    • Add cache headers                                          │
│    • Connection: keep-alive, HTTP/2, HTTP/3                     │
│    • Async/parallel calls where possible                        │
│    • DB indexes for hot queries                                 │
│                                                                 │
│  HIGH IMPACT, MEDIUM EFFORT:                                     │
│    • Multi-level caching                                        │
│    • Database query optimization                                 │
│    • Denormalization for read patterns                          │
│    • CDN for static assets                                      │
│    • Connection pooling                                         │
│                                                                 │
│  HIGH IMPACT, HIGH EFFORT:                                       │
│    • Sharding/replication                                       │
│    • Service decomposition                                      │
│    • Rewrite hot path in lower-level language                   │
│    • Custom data structures / algorithms                       │
│                                                                 │
│  LOW IMPACT, ANY EFFORT (avoid over-engineering):               │
│    • Micro-optimizations in cold paths                          │
│    • Premature refactoring                                      │
│    • Exotic tech without measurement                            │
└─────────────────────────────────────────────────────────────────┘
```

### The RAIL Performance Model

RAIL is a user-experience model for interactive front ends, not a universal
backend latency standard. Apply its thresholds only to the browser or client
interaction being evaluated; derive service budgets from the end-to-end SLO.

| Metric | Target | Focus |
|--------|--------|-------|
| **Response** (input delay) | < 100ms | UI responsiveness |
| **Animation** (frame render) | 16ms (60fps) | Smooth interactions |
| **Idle** (background work) | 50ms chunks | Avoid blocking main thread |
| **Load** (page ready) | < 1s on 3G | Time to interactive |

### Profiling & Observability for Performance

```bash
# Application profiling
go tool pprof http://service:6060/debug/pprof/profile?seconds=30
py-spy dump --pid 1234
perf top -p $(pgrep -f myapp)
async-profiler (Java)

# Database query analysis
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 123;
# Look for: Seq Scan, high cost, slow row estimates

# Network analysis
tcpdump + Wireshark → identify retransmits, slow start, etc.

# Continuous profiling
Pyroscope / Polar Signals — flame graphs in production
Parca / eBPF — kernel-level visibility

# APM tools
Datadog APM, New Relic, Honeycomb, Lightstep, Elastic APM
```

### Common Performance Wins

```yaml
1. CACHE DELIBERATELY:
   - Cache measured hot paths when staleness and invalidation are understood
   - Use stale-while-revalidate
   - Layer caches (L1 in-process, L2 Redis)

2. PARALLELIZE INDEPENDENT CALLS:
   - Promise.all() in JS
   - asyncio.gather() in Python
   - errgroup in Go

3. AVOID N+1 QUERIES:
   - Eager load with JOIN or includes
   - DataLoader pattern for GraphQL

4. USE STREAMING:
   - Server-Sent Events, gRPC streaming
   - WebSockets for bi-directional
   - Chunked transfer for large responses

5. COMPRESS AND MINIFY:
   - Benchmark Brotli and gzip by payload, client support, CPU cost, and cacheability
   - Image optimization (WebP, AVIF, lazy load)
   - Minify CSS/JS, tree-shake

6. RIGHT-SIZE RESOURCES:
   - Profile first, then scale
   - Eliminate GC pauses (tune heap, use ZGC/Shenandoah)
   - Use native code for hot paths
```

---

## 4.14 Capacity Planning

### Growth Models

```python
# Linear Growth
users(t) = users_0 + rate * t

# Exponential Growth
users(t) = users_0 * (1 + growth_rate) ** t

# S-Curve (more realistic for adoption)
adoption(t) = total_market / (1 + exp(-k * (t - midpoint)))

# Resource Planning
# Given:
#   - Current load: 100K DAU
#   - Growth assumption: 100% YoY
#   - Target SLO: p99 < 200ms, 99.9% availability
# Plan for: 200K DAU at year 1, 400K at year 2

# Capacity calculation
# Current: 100K DAU × 100 requests/user = 10M requests/day
# Peak: 10M / 86400 × 5 = 580 QPS
# Year 2: 1160 QPS peak
# Required capacity after failure headroom is determined by load tests and the
# chosen zone/instance failure model; a universal 2x multiplier is not implied.
```

### Little's Law for Concurrency and Queue Capacity

Little's Law relates average concurrency (`L`), arrival rate (`λ`) and average time in the system (`W`): `L = λ × W`.

Example: An API receives 2,000 requests/second and spends 100 ms per request on average.

```text
λ = 2,000 requests/s
W = 0.100 s
L = 2,000 × 0.100 = 200 concurrent requests

Per-instance safe concurrency = 50
Base instances = ceil(200 / 50) = 4
N+1 capacity = 5
30% headroom = ceil(5 × 1.30) = 7 instances
```

Little's Law is an average model, not a tail-latency guarantee. Use peak arrival rate and measured service-time distributions for production planning.

### Latency Budget Example

| Segment | p99 budget |
|---------|------------|
| Edge, TLS and load balancer | 20 ms |
| Authentication and policy | 15 ms |
| Application logic | 35 ms |
| Cache/database access | 60 ms |
| Downstream service | 40 ms |
| Serialization and response | 10 ms |
| Safety margin | 20 ms |
| **Total** | **200 ms** |

Child timeouts must fit inside the parent deadline; otherwise the end-to-end SLO cannot be met.

### Capacity Test Acceptance Criteria

- Test normal, expected peak and overload traffic separately.
- Record p50, p95 and p99—not only averages.
- Find the saturation point where throughput stops rising but latency and errors increase.
- Verify one-instance or one-zone failure at peak traffic.
- Observe CPU, memory, queue age, connection pools, cache hit rate and dependencies together.
- Confirm overload returns bounded `429`/`503` responses instead of cascading failure.

### SLO-Based Capacity Planning

```
SLO: 99.9% availability, p99 < 200ms
Error budget: 0.1% × 30 days × 86400 = 43.2 minutes/month

Plan:
  1. Determine SLO per service
  2. Calculate error budget
  3. Track SLI (Service Level Indicator)
     • Availability: (successful_requests / total_requests) over window
     • Latency: histogram (p50, p95, p99)
  4. Burn rate: how fast are you using budget?
  5. Provision capacity for target SLI with margin

  Example: Need p99 < 200ms
  Capacity test: at 70% CPU, p99 = 180ms (good)
  At 90% CPU, p99 = 350ms (fail)
  → Keep load below 75% for SLO compliance
```

---

## 4.15 Exercises

### Exercise 1 — Foundation: Scale-Out Design
A monolithic Rails app handles 500 RPS. Database is bottleneck (60% CPU on primary).
Design migration to:
- Phase 1: Quick wins (caching, indexing, read replicas)
- Phase 2: Extract bottlenecks into services
- Phase 3: Database sharding

Include timeline, risks, rollback plan.

### Exercise 2 — Applied: Sharding Key Selection
For a SaaS multi-tenant application (1000 tenants, 10M users, 1B events):
- Choose sharding strategy
- Justify with metrics (query patterns, growth)
- Handle tenant isolation needs

### Exercise 3 — Applied: Caching Strategy
Design caching for a product catalog (10M SKUs, 100K updates/day, 1M reads/sec):
- Cache layers
- Invalidation strategy
- Cache stampede prevention
- Memory sizing

### Exercise 4 — Advanced: Performance Investigation
Users report that p99 latency for `/search` increased from 200ms to 800ms over the past week.
Create a structured investigation:
- What metrics to check
- What hypotheses to test
- How to identify root cause

### Exercise 5 — Advanced: CQRS for Audit
A financial system needs complete audit trail. Design CQRS + Event Sourcing:
- Event schema
- Projection strategy
- Snapshotting
- Event versioning approach

---

## 4.16 Further Reading

### Books
- *Designing Data-Intensive Applications* — Kleppmann (Ch. 5, 6, 11)
- *Web Scalability for Startup Engineers* — Artur Ejsmont
- *Scalability Rules* — Michael Fisher
- *Building Evolutionary Architectures* — Ford, Parsons, Kua

### Papers
- [The Tail at Scale](https://research.google/pubs/the-tail-at-scale/) — Dean & Barroso, Google
- [Sharding the Empire](https://medium.com/stripe-engineering/sharding-the-empire-stripes-path-to-database-scalability-4425d66da98c) — Stripe Engineering
- [TAO: Facebook's Distributed Data Store](https://www.usenix.org/system/files/conference/atc13/atc13-bronson.pdf)

### Tools & Frameworks
- **Caching**: Redis, Memcached, Hazelcast, Caffeine
- **Sharding**: Vitess (MySQL), Citus (PostgreSQL), MongoDB Sharding
- **Load Testing**: k6, Locust, Gatling, JMeter
- **Continuous Profiling**: Pyroscope, Parca, Datadog Continuous Profiler

---

## 4.17 Summary Checklist

- [ ] Can articulate horizontal vs vertical trade-offs
- [ ] Can design a stateless service for scale-out
- [ ] Can implement consistent hashing
- [ ] Understand replication patterns (single-leader, multi-leader, leaderless)
- [ ] Can choose appropriate sharding key
- [ ] Know when to use CQRS and event sourcing
- [ ] Can apply RAIL performance model
- [ ] Understand CDN caching and edge computing
- [ ] Can plan capacity using SLO-based approach
- [ ] Can diagnose performance issues with proper methodology

---

> **Next Chapter**: [Chapter 5: Database Design & Selection](../chapters/05-database-design-selection.md) — From SQL to NoSQL to NewSQL.
