# Chapter 3: Distributed Systems Concepts

> **Estimated Time: 4-5 hours** | **Prerequisites: Chapters 1-2, basic algorithms**

---

## 🎯 Learning Objectives

By the end of this chapter, you will be able to:

1. **Reason about** distributed systems trade-offs (CAP, consistency models)
2. **Implement consensus algorithms** (Raft, Paxos fundamentals)
3. **Design event-driven** systems with proper ordering guarantees
4. **Apply time synchronization** strategies (NTP, TrueTime, vector clocks)
5. **Handle partial failures** with circuit breakers, bulkheads, retries
6. **Build idempotent systems** safe for retry and replay
7. **Understand the 8 Fallacies of Distributed Computing** deeply

---

## 3.1 Why Distributed Systems?

### The Fundamental Drivers

```
┌─────────────────────────────────────────────────────────────────┐
│  WHY DISTRIBUTE?                                                │
├─────────────────────────────────────────────────────────────────┤
│  • SCALABILITY   — Single machine can't handle load              │
│  • AVAILABILITY  — Single point of failure is unacceptable       │
│  • LATENCY       — Place compute close to users                 │
│  • DURABILITY    — Survive disasters, geographic redundancy      │
│  • COST          — Commodity hardware vs expensive mainframe    │
│  • SPECIALIZATION — Build focused services over monoliths       │
└─────────────────────────────────────────────────────────────────┘
```

### The Cost of Distribution

```
MONOLITH                          DISTRIBUTED SYSTEM
────────                          ──────────────────
✓ Single-node transactions        ✗ Distributed transactions (2PC, Saga)
✓ Strong consistency default      ✗ Eventual consistency
✓ Synchronous calls               ✗ Network failures, timeouts
✓ Easy debugging                  ✗ Hard to reproduce bugs
✓ Simple deployment               ✗ Complex orchestration
✓ Low latency (in-process)        ✗ Network latency per call
```

> **Rule of thumb**: Stay monolith until *organizational* or *scaling* pressure forces distribution. Premature distribution is the most common system design mistake.

---

## 3.2 The 8 Fallacies of Distributed Computing

> *Peter Deutsch, Sun Microsystems, 1994-1997*

| # | Fallacy | Reality |
|---|---------|---------|
| 1 | The network is reliable | Networks fail constantly — design for it |
| 2 | Latency is zero | WAN = 50-300ms, DC = 0.5-2ms, can vary |
| 3 | Bandwidth is infinite | Bottlenecks exist, especially cross-region |
| 4 | The network is secure | Default Internet is hostile, use mTLS |
| 5 | Topology doesn't change | Servers churn, autoscaling, network rebalances |
| 6 | There is one administrator | Multi-team, multi-cloud governance |
| 7 | Transport cost is zero | API calls, cross-region traffic cost real money |
| 8 | The network is homogeneous | Mix of protocols, generations, vendors |

**Mitigation mindset**: Every distributed call is a *remote possibility* of failure. Code accordingly.

---

## 3.3 Consistency Models

### The Consistency Spectrum

```
STRONG ──────────────────────────────────────────────── WEAK
  │                                                       │
  ▼                                                       ▼
Linearizable → Sequential → Causal → Read-your-writes → Monotonic
   │                                              read → Eventual
   │                                                       │
   ▼                                                       ▼
  Most coordination                          Async replication,
  needed, slowest                            fastest, simplest
```

### Model Definitions

| Model | Guarantee | Use Cases |
|-------|-----------|-----------|
| **Linearizability** | Operations appear to take effect atomically at some point between invocation and response | Leader election, locks, financial txns |
| **Sequential** | All operations appear in some total order consistent with program order | Easier than linearizable, useful for many apps |
| **Causal** | Operations that could influence each other are seen in order | Comments, replies, social media |
| **Read-your-writes** | User sees their own writes immediately | User profile updates |
| **Monotonic reads** | Successive reads see non-decreasing values | News feeds, leaderboards |
| **Eventual** | All replicas converge given enough time without writes | DNS, feeds, analytics |

### Implementing Consistency

```python
# Example: Eventual Consistency in DynamoDB-style KV store
class VectorClock:
    """Tracks causality across replicas."""
    def __init__(self, clock=None):
        self.clock = clock or {}
    
    def increment(self, node_id):
        self.clock[node_id] = self.clock.get(node_id, 0) + 1
    
    def merge(self, other):
        for node, count in other.clock.items():
            self.clock[node] = max(self.clock.get(node, 0), count)
    
    def happens_before(self, other):
        """True if self is causally before other."""
        return all(self.clock.get(n, 0) <= other.clock.get(n, 0)
                   for n in set(self.clock) | set(other.clock))
    
    def is_concurrent(self, other):
        """Neither happens-before the other."""
        return not self.happens_before(other) and not other.happens_before(self)
```

---

## 3.4 CAP & PACELC — Revisited

### Real-World CAP Choices

```
                    Network Partition
                         occurs
                           │
                           ▼
              ┌────────────┴────────────┐
              │                         │
        CP Systems                  AP Systems
   (Consistency >                (Availability >
    Availability)                 Consistency)
              │                         │
              ▼                         ▼
     Return error /              Return stale data,
     reject writes               accept writes
              │                         │
   • etcd, ZooKeeper             • Cassandra, DynamoDB
   • HBase, MongoDB (default)    • Riak, CouchDB
   • Spanner (also low-latency)  • S3 (eventual list)
              │                         │
              └────────────┬────────────┘
                           │
                    No partition
                           │
                           ▼
              ┌────────────┴────────────┐
              │                         │
        Latency-sensitive       Consistency-sensitive
              │                         │
              ▼                         ▼
     • DynamoDB (default)        • Spanner (TrueTime)
     • MongoDB (tunable)         • CockroachDB
     • Cassandra (ONE)           • FoundationDB
```

---

## 3.5 Consensus Algorithms

### The Consensus Problem

Multiple nodes must agree on a value despite failures:
- **Agreement**: All non-faulty nodes decide the same
- **Validity**: Decided value was proposed by some node
- **Termination**: Every non-faulty node eventually decides

### Paxos — The Classic

```
PHASE 1: Prepare
  Proposer → Acceptors: Prepare(n)
  Acceptors → Proposer: Promise(n, accepted_value) or Reject

PHASE 2: Accept
  Proposer → Acceptors: Accept(n, value)
  Acceptors → Proposer: Accepted(n, value) or Reject

LEARNING: Acceptors → Learners: AcceptedValue

Key insight: Quorum (majority) needed in both phases
             Quorum ensures intersection property
```

### Raft — The Understandable Consensus

```
┌─────────────────────────────────────────────────────────────┐
│                    RAFT STATES                              │
│                                                             │
│                  ┌──────────────┐                           │
│                  │              │                           │
│                  │   FOLLOWER   │ ◄──────┐                  │
│                  │              │        │                  │
│                  └──────┬───────┘        │                  │
│                         │ election timeout│                │
│                  ┌──────▼───────┐  vote   │                  │
│                  │              │────────►│                  │
│                  │   CANDIDATE  │         │                  │
│                  │              │         │                  │
│                  └──────┬───────┘  vote   │                  │
│                         │ majority      │                  │
│                  ┌──────▼───────┐        │                  │
│                  │              │────────┘                  │
│                  │    LEADER    │                            │
│                  │              │                            │
│                  └──────────────┘                            │
└─────────────────────────────────────────────────────────────┘

LOG REPLICATION:
  Leader → Followers: AppendEntries(entries, prevLogIndex, prevLogTerm)
  Followers: Ack if (prevLogIndex, prevLogTerm) match
  Leader commits when majority ack
  Followers apply committed entries to state machine
```

### Raft Implementation Outline

```python
class RaftNode:
    def __init__(self, node_id, peers):
        self.node_id = node_id
        self.peers = peers
        self.state = 'follower'
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.commit_index = 0
        self.last_applied = 0
    
    def become_candidate(self):
        self.current_term += 1
        self.voted_for = self.node_id
        self.state = 'candidate'
        # Send RequestVote RPC to all peers
        return self.collect_votes()
    
    def become_leader(self):
        self.state = 'leader'
        # Send heartbeats and replicate log
        self.send_append_entries()
    
    def handle_request_vote(self, term, candidate_id, last_log_index, last_log_term):
        if term > self.current_term:
            self.step_down(term)
        if term == self.current_term and (self.voted_for in [None, candidate_id]):
            if self.log_is_up_to_date(last_log_index, last_log_term):
                self.voted_for = candidate_id
                return True
        return False
    
    def handle_append_entries(self, term, leader_id, prev_index, prev_term, entries, leader_commit):
        if term < self.current_term:
            return False
        if not self.log_matches(prev_index, prev_term):
            return False  # Conflict, decrement nextIndex
        self.log[prev_index + 1:] = entries
        if leader_commit > self.commit_index:
            self.commit_index = min(leader_commit, len(self.log) - 1)
        return True
```

### Consensus in Practice

| System | Algorithm | Notes |
|--------|-----------|-------|
| etcd | Raft | Kubernetes, distributed locks |
| Consul | Raft | Service discovery, config |
| CockroachDB | Raft | Distributed SQL |
| TiKV | Raft | Distributed KV (TiDB) |
| ZooKeeper | Zab (Paxos-like) | Hadoop ecosystem |
| Spanner | Paxos + TrueTime | Google's global SQL |
| Kafka KRaft | Raft | Controller quorum (replaced ZooKeeper) |
| MongoDB | Raft (for config) | Replica set leader election |

---

## 3.6 Time, Clocks, and Ordering

### Clock Types

```
┌──────────────────────────────────────────────────────────────┐
│  PHYSICAL CLOCKS                                             │
│    • Hardware clocks (RTC, TSC)                             │
│    • NTP-synced (LAN: ~1ms, WAN: ~10-100ms accuracy)        │
│    • PTP (Precision Time Protocol): ~1µs LAN accuracy       │
│    • GPS receivers: ~10-100ns accuracy                      │
│    • Atomic clocks: ~1ns                                     │
│    • Google TrueTime: GPS + atomic, with bounded uncertainty │
│                                                              │
│  LOGICAL CLOCKS                                              │
│    • Lamport timestamps: Total ordering of events            │
│    • Vector clocks: Causal ordering + concurrency detection │
│    • Hybrid Logical Clocks (HLC): Physical + logical mix    │
└──────────────────────────────────────────────────────────────┘
```

### Lamport Timestamps

```python
class LamportClock:
    def __init__(self):
        self.counter = 0
    
    def tick(self):
        """Local event."""
        self.counter += 1
        return self.counter
    
    def send_event(self):
        """Before sending a message."""
        self.counter += 1
        return self.counter
    
    def receive_event(self, received_ts):
        """After receiving a message."""
        self.counter = max(self.counter, received_ts) + 1
        return self.counter

# Properties:
# 1. If a → b, then L(a) < L(b) (causal implies ordering)
# 2. NOT converse: L(a) < L(b) doesn't imply a → b
# 3. Total order can be imposed: (L, node_id)
```

### Vector Clocks (Detect Concurrency)

```python
class VectorClock:
    def __init__(self, nodes):
        self.clock = {n: 0 for n in nodes}
    
    def increment(self, node):
        self.clock[node] += 1
    
    def update(self, other_clock):
        for node in other_clock:
            self.clock[node] = max(self.clock[node], other_clock[node])
        self.increment(...)  # ...your node
    
    def happens_before(self, other):
        # All entries ≤ other AND at least one <
        return (all(self.clock[n] <= other.clock[n] for n in self.clock) 
                and any(self.clock[n] < other.clock[n] for n in self.clock))
    
    def is_concurrent(self, other):
        # Neither dominates the other
        return not self.happens_before(other) and not other.happens_before(self)
```

### Google's TrueTime

```cpp
// Spanner API
class TrueTime {
  // Returns interval [earliest, latest] guaranteed to contain real time
  static TTInterval Now();
  
  // Wait until time is definitely in the past
  static void WaitUntil(TTTimestamp time);
};

// Used in Spanner transactions:
void SpannerTransaction::Commit() {
    TTtimestamp commit_ts = TrueTime::Now().latest;
    // Coordinators wait until commit_ts is definitely past
    TrueTime::WaitUntil(commit_ts);
    // Now safe to return success to client — no other tx can claim earlier ts
}
```

### Time Synchronization in Practice

```bash
# NTP configuration (/etc/chrony/chrony.conf)
server 0.pool.ntp.org iburst
server 1.pool.ntp.org iburst
server time.cloudflare.com iburst prefer
makestep 1.0 3
rtcsync
logdir /var/log/chrony

# Verify
chronyc tracking
chronyc sources -v

# PTP (datacenter high-precision)
# ptp4l -i eth0 -m -S
# phc2sys -s eth0 -w

# Modern: Amazon Time Sync Service, Google Cloud's NTP
# Use chrony/ntpd with multiple servers, monitor drift
```

---

## 3.7 Failure Modes & Detection

### Failure Taxonomy

```
┌─────────────────────────────────────────────────────────────────┐
│  FAILURE TYPES                                                 │
├─────────────────────────────────────────────────────────────────┤
│  • Crash-stop: Node halts, doesn't return                       │
│  • Crash-recovery: Node restarts with persistent state          │
│  • Omission: Drop messages (send or receive)                    │
│  • Network partition: Some nodes can't reach others             │
│  • Byzantine: Arbitrary, malicious behavior                     │
│  • Timing: Operations are too slow                              │
│  • Response: Wrong result returned                             │
└─────────────────────────────────────────────────────────────────┘
```

### Failure Detection

```yaml
# Heartbeat-based detection
Interval: 1s
Timeout: 3s
Suspect threshold: 2 missed heartbeats
Confirm failure: 3 missed heartbeats
Action: Mark suspect → remove from membership

# Phi Accrual Failure Detector (Cassandra uses variant)
φ = -log10(1 - P(latency > t_now))
# φ > 8 → likely failure (configurable)

# Gossip-based detection (Akka, Cassandra)
Each node gossips heartbeat list with timestamps
Node X is marked down if M nodes report X down
```

### SWIM Protocol (Membership)

```
SWIM (Scalable Weakly-consistent Infection-style Membership):
  1. Periodically ping random peer directly
  2. If no ACK, ask K random peers to ping the same target
  3. If still no ACK, mark as suspect
  4. Gossip suspicion state to spread info
  5. Refute via alive messages if false suspicion
  
Used by: Hashicorp Serf, Consul, memberlist
```

---

## 3.8 Resilience Patterns

### Circuit Breaker

```
┌─────────────────────────────────────────────────────────────┐
│  STATES                                                     │
│                                                             │
│   ┌─────────┐  failure threshold  ┌─────────┐               │
│   │ CLOSED  │ ─────────────────► │  OPEN   │               │
│   │ (normal)│                    │ (fail   │               │
│   └────▲────┘                    │  fast)  │               │
│        │                         └────┬────┘               │
│        │                              │                     │
│        │                       timeout elapsed              │
│        │                              ▼                     │
│        │ trial call            ┌───────────┐               │
│        └────────────────────── │ HALF_OPEN │               │
│                                 │  (probe)  │               │
│                                 └───────────┘               │
└─────────────────────────────────────────────────────────────┘

Implementation (resilience4j, Hystrix legacy):
- failureRateThreshold: 50%
- waitDurationInOpenState: 30s
- slidingWindowSize: 100
- permittedNumberOfCallsInHalfOpenState: 10
```

### Retry with Exponential Backoff + Jitter

```python
import random
import time

def retry_with_backoff(fn, max_attempts=5, base=0.1, cap=10.0):
    """Exponential backoff with full jitter."""
    for attempt in range(max_attempts):
        try:
            return fn()
        except (TimeoutError, ConnectionError) as e:
            if attempt == max_attempts - 1:
                raise
            sleep = min(cap, base * (2 ** attempt))
            jittered = random.uniform(0, sleep)  # Full jitter
            time.sleep(jittered)

# Why jitter?
# Without jitter: 1000 clients all retry at second 1, 2, 4, 8...
# Server hits with synchronized storm = overload
# With jitter: retries spread across time window
```

### Bulkhead Pattern

```
┌─────────────────────────────────────────────────────────────┐
│  RESOURCE ISOLATION                                          │
│                                                             │
│  Without bulkhead:                                          │
│    Pool 1 ──┐                                               │
│             ├──► Shared Thread Pool ──► All services       │
│    Pool 2 ──┘                                               │
│                                                             │
│  If Service A hangs, it consumes all threads.               │
│  Service B gets no threads → cascade failure.               │
│                                                             │
│  With bulkhead:                                             │
│    Pool A (10 threads) ──► Service A                        │
│    Pool B (20 threads) ──► Service B                        │
│    Pool C (5 threads)  ──► Service C                        │
│                                                             │
│  Failure of A doesn't affect B or C.                        │
└─────────────────────────────────────────────────────────────┘
```

### Rate Limiting

```python
# Token Bucket
class TokenBucket:
    def __init__(self, rate, capacity):
        self.rate = rate              # tokens/sec
        self.capacity = capacity      # burst size
        self.tokens = capacity
        self.last_refill = time.monotonic()
    
    def allow(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

# Distributed rate limit (Redis)
def rate_limit(user_id, max_per_minute=60):
    key = f"rl:{user_id}:{int(time.time() // 60)}"
    count = redis.incr(key)
    if count == 1:
        redis.expire(key, 60)
    return count <= max_per_minute

# Algorithms: Token bucket, Leaky bucket, Fixed window, 
# Sliding window, Sliding log
```

### Timeout Strategy

```yaml
Timeouts Hierarchy (avoid timeout = no timeout):
  Application: 5s       # Final hard stop
    HTTP client: 4s      
      Connect: 1s        
      TLS handshake: 1s  
      Request: 2s        
        Read: 500ms      # Per chunk
        Idle: 100ms      
      
Rule: total timeouts along path < parent timeout
Rule: timeouts should differ across services (avoid thundering herd)
```

---

## 3.9 Idempotency

### Why Idempotency Matters

```
Network is unreliable. Retries happen.
Without idempotency:
  POST /payments  →  (network timeout, server processed)
  Retry → Two charges!

With idempotency:
  POST /payments 
    Idempotency-Key: abc123
  → Server sees existing abc123, returns cached response
```

### Implementation Patterns

```python
# Pattern 1: Idempotency Key
@app.post("/payments")
def create_payment(request: Request, body: Payment):
    key = request.headers.get("Idempotency-Key")
    if not key:
        return {"error": "Idempotency-Key required"}, 400
    
    cached = redis.get(f"idem:{key}")
    if cached:
        return json.loads(cached)
    
    # Use SETNX to prevent races
    lock_key = f"idem:lock:{key}"
    if not redis.set(lock_key, "1", nx=True, ex=30):
        return {"error": "Concurrent request in progress"}, 409
    
    try:
        result = process_payment(body)
        redis.set(f"idem:{key}", json.dumps(result), ex=86400)
        return result
    finally:
        redis.delete(lock_key)

# Pattern 2: Natural Idempotency
# PUT /users/123 (specific resource) — natural idempotency
# DELETE /users/123 — natural idempotency

# Pattern 3: Deduplication IDs in message queues
# Producer assigns message ID → consumer tracks processed IDs
```

---

## 3.10 Distributed Transactions

### Two-Phase Commit (2PC)

```
              COORDINATOR
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
    PARTICIPANT  PARTICIPANT  PARTICIPANT
    
Phase 1 (Prepare):
  Coord → All: Prepare
  All → Coord: Yes/No (vote)
  Coord waits for ALL votes
  
Phase 2 (Commit/Abort):
  If all yes: Coord → All: Commit
  If any no:  Coord → All: Abort
  
PROBLEMS:
  • Blocking — if coordinator crashes after prepare, participants stuck
  • Locking — resources held during uncertainty
  • Slow — 2 round-trips minimum
  • Not partition-tolerant
```

### Saga Pattern

```
Long-lived transaction as sequence of local transactions + compensations

Example: Order Saga
  1. CreateOrder
  2. ReserveInventory        (compensate: ReleaseInventory)
  3. ChargePayment            (compensate: RefundPayment)
  4. ShipOrder                (compensate: CancelShipment)
  5. SendConfirmation         (no compensation)

Choreography (events):
  Service A emits OrderCreated
  Service B listens, reserves, emits InventoryReserved
  Service C listens, charges, emits PaymentCharged
  ...

Orchestration (central coordinator):
  Saga Orchestrator (e.g., Temporal, Camunda)
    → Directs each step, handles compensation
    → Easier to understand, single place for logic
    → Coupling to orchestrator
```

### Saga Failure Recovery

```python
# Forward recovery: saga continues despite partial failure
# Backward recovery: compensating transactions

# Example using Temporal.io
@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, order):
        compensations = []
        try:
            compensations.append(
                await workflow.execute_activity(
                    create_order, order, start_to_close_timeout=timedelta(seconds=30)
                )
            )
            compensations.append(
                await workflow.execute_activity(
                    reserve_inventory, order.items, ...
                )
            )
            compensations.append(
                await workflow.execute_activity(
                    charge_payment, order, ...
                )
            )
            await workflow.execute_activity(ship_order, order, ...)
        except Exception:
            # Run compensations in reverse
            for c in reversed(compensations):
                await workflow.execute_activity(c.compensate, ...)
            raise
```

---

## 3.11 Idempotency, Exactly-Once Delivery & Ordering

### Delivery Semantics

| Semantics | Definition | How |
|-----------|------------|-----|
| **At-most-once** | Message may be lost, no duplicates | Fire and forget |
| **At-least-once** | Message always delivered, may duplicate | Retries |
| **Exactly-once** | Message processed once and only once | Idempotency + dedup |
| **Effectively-once** | Combined: at-least-once delivery + idempotent processing | Standard approach |

### Message Ordering

```
Per-partition ordering (Kafka):
  Partition P1: M1, M2, M3, M4  ← Ordered within partition
  Partition P2: M5, M6, M7, M8
  M2 < M3 < M4 in P1, M6 < M7 < M8 in P2
  No order guarantee ACROSS partitions

Global ordering:
  Single partition, single consumer (throughput bottleneck)
  Or use Total Order Broadcast (atomic broadcast)

Causal ordering:
  Use vector clocks or version vectors
  Process messages in causal order
```

---

## 3.12 Distributed System Building Blocks

### Coordination Services (ZooKeeper, etcd, Consul)

```
Use Cases:
  • Configuration distribution
  • Leader election
  • Service discovery
  • Distributed locks
  • Cluster membership

etcd example:
  $ etcdctl put /services/api/leader "node-3"
  $ etcdctl watch /services/api/leader
  PUT
  /services/api/leader
  node-3

Zab vs Raft:
  Both similar; Zab focuses on primary-backup model,
  Raft on leader-based replicated log
```

### Service Discovery

```
DNS-based:
  Service A → dig api.service.consul → 10.0.1.5
  Simple, cached, well-understood
  
Service Registry (Consul, Eureka):
  Services register on startup
  Health checks periodically
  Clients query registry
  
Sidecar / Mesh:
  Istio: Envoy sidecar handles discovery + load balancing
  mTLS between services
  No app code changes needed
```

### Distributed Locks

```python
# Redis Redlock (controversial — see antirez reply)
# Better: use Zookeeper/etcd lease-based locks

import etcd3

class EtcdLock:
    def __init__(self, etcd_client, key, ttl=10):
        self.client = etcd_client
        self.key = key
        self.ttl = ttl
        self.lease = None
    
    def acquire(self):
        self.lease = self.client.lease(self.ttl)
        try:
            self.client.put(self.key, self.lease.id, lease=self.lease)
            return True
        except etcd3.Etcd3Error:
            return False
    
    def release(self):
        if self.lease:
            self.lease.revoke()

# Redlock considerations:
# • Network partitions can break safety
# • Use fencing tokens (Martin Kleppmann critique)
# • Avoid for correctness-critical use, prefer async coordination
```

---

## 3.13 Distributed Storage Fundamentals

### Replication Strategies

```
SYNCHRONOUS REPLICATION:
  W1 → Ack W1
  W1 → Replicate to R2, R3 (wait for ack)
  W1 → Ack W2, W3 (after all replicas acked)
  W1 → Return success
  ✓ Strong consistency
  ✗ Higher latency, lower availability (if any replica down)

ASYNCHRONOUS REPLICATION:
  W1 → Ack W1, log to WAL
  W1 → Return success
  W1 → Replicate to R2, R3 (background)
  ✓ Low latency, high availability
  ✗ Risk of data loss on failover

QUORUM-BASED:
  W (write) + R (read) > N (replicas)
  N=3, W=2, R=2: any 2 replicas must overlap → strong reads
  Tunable: W+R > N for strong, W+R ≤ N for fast
```

### Partitioning (Sharding)

```
Strategies:
  • Hash partitioning: hash(key) mod N
    + Uniform distribution
    - Resharding is hard (consistent hashing helps)
  • Range partitioning: key ranges per shard
    + Range queries easy
    - Hotspots (timestamps, etc.)
  • Directory-based: lookup service
    + Flexible
    - Lookup overhead, single point
  • Geo-partitioning: shard by region
    + Low latency, compliance
    - Cross-region queries expensive

CONSISTENT HASHING:
  Hash ring: nodes + keys mapped to ring
  Each key → next clockwise node
  Add/remove node: only K/N keys remapped
  Virtual nodes for better distribution
```

### Storage Models Comparison

| Type | Examples | Strengths | Weaknesses |
|------|----------|-----------|------------|
| **KV Store** | Redis, DynamoDB, etcd | Simple, fast | Limited query |
| **Document** | MongoDB, CouchDB, Firestore | Flexible schema | Weak joins |
| **Wide-Column** | Cassandra, HBase, ScyllaDB | Petabyte scale, write-heavy | Limited query patterns |
| **Relational** | PostgreSQL, MySQL | ACID, joins, mature | Vertical scaling limits |
| **Graph** | Neo4j, JanusGraph | Relationship traversal | Not general-purpose |
| **Time-Series** | InfluxDB, TimescaleDB, Prometheus | Efficient storage, queries | Limited for general use |
| **Search** | Elasticsearch, OpenSearch | Full-text, aggregations | Eventually consistent |
| **Object** | S3, GCS, MinIO | Massive scale, cheap | High latency |

---

## 3.14 Distributed Tracing & Causality

### Causal Context Propagation

```python
# W3C Trace Context (OpenTelemetry standard)
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
# version-traceid-spanid-flags (01 = sampled)

# Baggage: arbitrary key-value pairs propagated
baggage: userId=alice,region=eu-west-1

# Trace example:
Span A (API Gateway)
  ├── Span B (Auth Service)
  ├── Span C (User Service)
  │     ├── Span D (DB Query)
  │     └── Span E (Cache Lookup)
  └── Span F (Notification Service)
```

---

## 3.15 Exercises

### Exercise 1: Consistency Model Selection
For each scenario, choose the appropriate consistency model:
- Bank transfer between accounts
- Facebook posts visibility
- Inventory reservation during flash sale
- User preference updates
- DNS resolution

### Exercise 2: CAP Trade-off Analysis
Design a system for IoT sensor data ingestion (100M devices, 1 msg/sec each). Justify CP vs AP with:
- Failure modes
- Recovery strategy
- Cost

### Exercise 3: Raft Implementation
Implement a minimal Raft leader election in your language of choice. Test with:
- 3 nodes, kill leader, ensure new election
- Network partition, ensure no split brain

### Exercise 4: Saga Design
Design a saga for "Travel Booking" (flight + hotel + car):
- List the steps and compensations
- Identify failure modes
- Choose choreography vs orchestration with justification

### Exercise 5: Idempotency Design
Design an idempotency system for a payment API:
- Key strategy (UUID v4, v7, ULID?)
- Storage (Redis? PostgreSQL? Both?)
- TTL considerations
- Race conditions

---

## 3.16 Further Reading

### Essential Papers
- [Time, Clocks, and the Ordering of Events](https://lamport.azurewebsites.net/pubs/time-clocks.pdf) — Lamport, 1978
- [The Byzantine Generals Problem](http://lamport.azurewebsites.net/pubs/byz.pdf) — Lamport et al., 1982
- [Paxos Made Simple](https://lamport.azurewebsites.net/pubs/paxos-simple.pdf) — Lamport, 2001
- [In Search of an Understandable Consensus Algorithm](https://raft.github.io/raft.pdf) — Ongaro & Ousterhout, 2014
- [Dynamo: Amazon's Highly Available Key-value Store](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)
- [Spanner: Google's Globally-Distributed Database](https://static.googleusercontent.com/media/research.google.com/en//archive/spanner-osdi2012.pdf)
- [The 8 Fallacies of Distributed Computing (revisited)](https://blogs.oracle.com/javamagazine/post/the-8-fallacies-of-distributed-computing-revisited)

### Books
- *Designing Data-Intensive Applications* — Martin Kleppmann **(must-read)**
- *Distributed Systems* — Maarten van Steen & Andrew Tanenbaum (free online)
- *Data-intensive Applications and Systems* — Various
- *Consensus: Bridging Theory and Practice* — Diego Ongaro (PhD thesis)

### Online Resources
- [Jepsen](https://jepsen.io/) — Kyle Kingsbury's distributed systems tests
- [The Morning Paper](https://blog.acolyer.org/) — Adrian Colyer's paper summaries
- [Marc Shapiro's work](https://www.microsoft.com/en-us/research/people/mas/) — CRDTs, eventual consistency

---

## 3.17 Summary Checklist

- [ ] Can list the 8 fallacies and give real examples
- [ ] Can choose consistency model based on requirements
- [ ] Understand Raft vs Paxos trade-offs
- [ ] Can implement vector clocks and Lamport timestamps
- [ ] Know when to use sync vs async replication
- [ ] Can design saga with compensations
- [ ] Can implement circuit breakers, retries with jitter
- [ ] Understand 2PC limitations vs saga advantages
- [ ] Can reason about CAP/PACELC for any system
- [ ] Know the difference between logical and physical clocks

---

> **Next Chapter**: [Chapter 4: Scalability & Performance Patterns](../chapters/04-scalability-performance-patterns.md) — From single-server to planetary scale.