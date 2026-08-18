# Chapter 6: Caching Strategies

> **Estimated Time: 2-3 hours** | **Prerequisites: Chapters 1-5**

---

## 🎯 Learning Objectives

By the end of this chapter, you will be able to:

1. **Identify what to cache** and where to cache it
2. **Implement major caching patterns** (cache-aside, read-through, write-behind)
3. **Handle cache invalidation** correctly in distributed systems
4. **Prevent cache stampede** with proper concurrency control
5. **Choose cache technologies** based on requirements
6. **Measure cache effectiveness** (hit ratio, latency improvement)
7. **Design multi-tier caching** architectures

---

## 6.1 What & Why to Cache

### The Fundamental Equation

```
Without cache:
  Latency = DB_latency × operations
  Cost = DB_cost × operations
  Load = operations / DB_capacity

With cache:
  Latency = cache_hit_ratio × cache_latency + (1 - cache_hit_ratio) × DB_latency
  Cost = cache_cost + (1 - cache_hit_ratio) × DB_cost
  Load = DB sees only miss traffic

Example: 1000 QPS, 95% cache hit, DB 10ms, cache 1ms
  Without cache: 1000 × 10ms = 10 sec aggregate DB load
  With cache:    50 × 10ms = 0.5 sec aggregate DB load
                 20x DB load reduction
                 p99 latency: 10ms vs ~10ms (similar avg, much better tail)
```

### What to Cache (Cheat Sheet)

| Cacheable | Don't Cache |
|-----------|-------------|
| Reference data (countries, currencies) | Frequently changing prices |
| User profiles, sessions | Sensitive data (passwords, tokens) |
| Computed/aggregated values | Large objects (>1MB) |
| API responses (read-heavy) | User-specific private data* |
| Database query results | Strongly consistent reads |
| Rendered HTML/JSON | Anything write-heavy |
| Search results | Data without clear invalidation |
| Configuration | Real-time data (stock prices, IoT) |

*Unless encrypted and properly scoped

### Where to Cache

```
┌─────────────────────────────────────────────────────────────┐
│  CACHE HIERARCHY (left to right = closest to user)         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Browser Cache ─► CDN ─► API Gateway ─► App Cache          │
│  ◄────────────────────────────────────►                      │
│         Edge / External                    Internal         │
│                                                             │
│                  ─► Distributed Cache ─► Database           │
│                  ◄────────────────────►                      │
│                       Shared cache       Per-instance       │
│                                                             │
│  Trade-offs:                                                │
│    • Closer = faster, but harder to invalidate              │
│    • Larger = more capacity, but more network hops          │
│    • Multiple tiers = best perf + correctness               │
└─────────────────────────────────────────────────────────────┘
```

---

## 6.2 Caching Patterns

### Cache-Aside (Lazy Loading)

```
Application manages cache directly

READ:
  1. Check cache for key
  2. If HIT → return cached value
  3. If MISS → query DB, populate cache, return value

WRITE:
  1. Write to DB
  2. Invalidate cache (delete key)
     [next read will fetch fresh from DB and populate]
```

```python
class CacheAsideService:
    def __init__(self, cache, db):
        self.cache = cache
        self.db = db
    
    async def get(self, key):
        # Try cache
        value = await self.cache.get(key)
        if value is not None:
            return value
        
        # Cache miss: query DB
        value = await self.db.query(key)
        if value is not None:
            # Populate cache with TTL
            await self.cache.set(key, value, ttl=300)
        return value
    
    async def update(self, key, new_value):
        await self.db.update(key, new_value)
        await self.cache.delete(key)  # Invalidate, don't update
        # Lazy loading will repopulate on next read
```

**Pros**: Simple, only cache what's requested, resilient to cache failures  
**Cons**: Cache miss penalty (3 round trips: cache, DB, cache), stale data possible

### Read-Through

```
Cache sits between app and DB
Cache itself populates from DB

Application talks ONLY to cache
Cache handles DB fallback
```

```python
class ReadThroughCache:
    def __init__(self, cache, db, loader=None):
        self.cache = cache
        self.db = db
        self.loader = loader or self._default_loader
    
    async def get(self, key):
        # Try cache
        value = await self.cache.get(key)
        if value is not None:
            return value
        
        # Cache miss: load through to DB
        async with self.cache.lock(key):
            # Double-check after acquiring lock
            value = await self.cache.get(key)
            if value is not None:
                return value
            
            value = await self.loader(key)
            await self.cache.set(key, value, ttl=300)
            return value
    
    async def _default_loader(self, key):
        return await self.db.query(key)
```

**Pros**: App code simpler, transparent caching  
**Cons**: Cache becomes critical path, harder to debug

### Write-Through

```
Write goes to cache AND DB synchronously

WRITE:
  1. Write to cache (cache reflects new state)
  2. Cache writes to DB synchronously
  3. Return success after both complete
```

```python
class WriteThroughCache:
    async def update(self, key, value):
        # Write to DB first (source of truth)
        await self.db.update(key, value)
        # Then update cache (so cache always matches DB)
        await self.cache.set(key, value, ttl=300)
```

**Pros**: Cache always in sync, reads always fresh  
**Cons**: Higher write latency, cache failures affect writes

### Write-Behind (Write-Back)

```
Write to cache first, async write to DB

WRITE:
  1. Write to cache
  2. Return success immediately
  3. Queue async write to DB (batch possible)
```

```python
class WriteBehindCache:
    def __init__(self, cache, db, write_queue):
        self.cache = cache
        self.db = db
        self.write_queue = write_queue
    
    async def update(self, key, value):
        # Fast: just update cache
        await self.cache.set(key, value)
        # Queue DB write for background processing
        await self.write_queue.enqueue({
            "op": "update", 
            "key": key, 
            "value": value
        })
    
    async def flush_worker(self):
        """Background worker processes queue."""
        while True:
            batch = await self.write_queue.get_batch(max_size=100)
            if batch:
                await self.db.batch_update(batch)
```

**Pros**: Very fast writes, can batch DB writes, high throughput  
**Cons**: Data loss risk (cache crashes before DB write), complexity

### Refresh-Ahead

```
Cache proactively refreshes before TTL expires
Used for predictable access patterns

TTL = 5 minutes
Refresh trigger: TTL remaining < 1 minute
Background refresh: fetch fresh value while old still served
```

```python
class RefreshAheadCache:
    async def get(self, key):
        value, ttl_remaining, refresher = await self.cache.get_with_ttl(key)
        if value is None:
            # Cache miss
            value = await self.db.query(key)
            await self.cache.set(key, value, ttl=300)
            return value
        
        # Trigger refresh if close to expiry
        if ttl_remaining < 60 and not refresher.is_running():
            refresher.start(self._refresh, key)
        
        return value
```

**Pros**: Reduces cache miss latency for hot data  
**Cons**: Complex, may refresh unused data, hard to tune

### Pattern Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│  PATTERN         LATENCY  CONSISTENCY  COMPLEXITY  USE CASE    │
├─────────────────────────────────────────────────────────────────┤
│  Cache-Aside     Medium   Eventual     Low        General      │
│  Read-Through    Low      Eventual     Medium     Cache-managed│
│  Write-Through   High     Strong       Medium     Critical data│
│  Write-Behind    Lowest   Weak (async) High       Write-heavy  │
│  Refresh-Ahead   Lowest   Eventual     High       Predictable  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6.3 Cache Invalidation

### The "Two Hard Things"

> *"There are only two hard things in Computer Science: cache invalidation and naming things."* — Phil Karlton

### Invalidation Strategies

```python
# 1. TTL-BASED (Time-To-Live)
await cache.set(key, value, ttl=300)  # 5 minutes
# Pros: Simple, automatic cleanup
# Cons: Stale data possible until TTL expires

# 2. EVENT-DRIVEN (Pub/Sub)
await db.update(key, value)
await event_bus.publish("cache.invalidate", {"key": key})
# Listener:
async def handle_invalidation(event):
    await cache.delete(event["key"])
# Pros: Immediate invalidation
# Cons: Requires event infrastructure, can lose events

# 3. VERSION-BASED
# Store version with cached value
class VersionedCache:
    async def get(self, key):
        data, version = await cache.get_with_version(key)
        current_version = await db.get_version(key)
        if version != current_version:
            return None  # Cache stale, refetch
        return data

# 4. TAG-BASED (Cloudflare, Varnish)
await cache.set(key, value, tags=["user:123", "product:456"])
await cache.purge_tag("user:123")  # Invalidate all keys with tag
# Useful for bulk invalidation (e.g., all posts by a user)

# 5. WRITE-INVALIDATE (most common for cache-aside)
async def update(key, value):
    await db.update(key, value)
    await cache.delete(key)  # Don't update, just remove
# Next read will repopulate
```

### Invalidation Race Condition

```
PROBLEM: "Thundering herd on stale data"

Timeline:
  T1: Reader A reads key X (cache MISS)
  T2: Writer updates X in DB
  T3: Writer invalidates cache (delete key X)
  T4: Reader A populates cache with OLD value (from T1 fetch)
  
  Now cache has old value until next invalidation!

SOLUTIONS:
  1. Use locks during repopulation
  2. Use version numbers to detect stale reads
  3. Use CAS (compare-and-swap) operations
  4. Set short TTL for hot-write data
  5. Use message queue for ordered invalidation
```

---

## 6.4 Cache Stampede Prevention

### The Problem

```
Cache expires (TTL reached)
  ↓
1000 concurrent requests hit
  ↓
All 1000 check cache: MISS
  ↓
All 1000 query DB simultaneously
  ↓
DB overwhelmed, response time spikes
  ↓
Only 1 request should query DB; others wait or use stale
```

### Solution 1: Locking (Mutex)

```python
class StampedeProtectedCache:
    async def get(self, key):
        value = await cache.get(key)
        if value is not None:
            return value
        
        # Try to acquire lock for repopulation
        lock_key = f"lock:{key}"
        if await cache.set_if_not_exists(lock_key, "1", ttl=10):
            try:
                # Only one requester queries DB
                value = await db.query(key)
                await cache.set(key, value, ttl=300)
            finally:
                await cache.delete(lock_key)
        else:
            # Other requesters wait or use stale
            for _ in range(20):
                await asyncio.sleep(0.1)
                value = await cache.get(key)
                if value is not None:
                    return value
            # Lock holder may be stuck, query DB anyway
            value = await db.query(key)
            await cache.set(key, value, ttl=300)
        
        return value
```

### Solution 2: Probabilistic Early Expiration (XFetch)

```python
import random

def xfetch(ttl, beta=1.0):
    """Compute delta for early expiration."""
    # beta controls aggressiveness (0=no early, 1=very aggressive)
    return random.uniform(0, beta) * ttl * math.log(random.uniform(1, math.e))

async def get(self, key):
    # Use stored 'expiry' with random delta subtracted
    value, expiry = await cache.get_with_metadata(key)
    if value is None:
        return await self._fetch_and_set(key)
    
    delta = xfetch(self.beta * 1000)
    if time.time() * 1000 + delta >= expiry:
        # Probabilistically refresh before TTL
        return await self._fetch_and_set(key)
    
    return value

# Higher hit ratio with controlled stampede probability
```

### Solution 3: Stale-While-Revalidate

```python
async def get(self, key):
    value, is_stale = await cache.get_with_stale_flag(key)
    
    if value is not None and not is_stale:
        return value  # Fresh hit
    
    if value is not None and is_stale:
        # Stale: trigger async refresh, return stale value
        asyncio.create_task(self._refresh(key))
        return value  # Serve stale immediately
    
    # Complete miss
    return await self._fetch_and_set(key)
# Pattern: Background refresh; users always get fast response
```

### Solution 4: Pre-warming

```python
# For known traffic patterns (e.g., daily peak)
async def warm_cache():
    hot_keys = await analytics.get_hot_keys(top_n=1000)
    for key in hot_keys:
        value = await db.query(key)
        await cache.set(key, value, ttl=3600)

# Schedule before predicted peak
scheduler.cron("0 8 * * *", warm_cache)  # 8 AM daily
```

---

## 6.5 Cache Technologies

### In-Memory Caches

```python
# Python: cachetools (in-process LRU)
from cachetools import LRUCache, TTLCache

cache = LRUCache(maxsize=10000)
cache['key'] = 'value'

# With TTL
ttl_cache = TTLCache(maxsize=10000, ttl=300)
ttl_cache['key'] = 'value'

# Caffeine (Java)
LoadingCache<String, User> cache = Caffeine.newBuilder()
    .maximumSize(10_000)
    .expireAfterWrite(Duration.ofMinutes(5))
    .recordStats()
    .build(key -> db.findById(key));

# go-cache (Go)
cache := cache.New(5*time.Minute, 10*time.Minute)
cache.Set("key", value, cache.DefaultExpiration)
```

### Redis (Distributed Cache)

```bash
# Data structures
SET key value EX 300          # String with TTL
HSET user:1 name Alice age 30 # Hash
LPUSH queue:jobs job1         # List (queue)
SADD tags:user:1 tech music   # Set
ZADD leaderboard 100 alice    # Sorted set

# Advanced features
SET key value NX EX 300       # Set if not exists
SET key value XX EX 300       # Set if exists (CAS)
INCR counter                  # Atomic increment
SETBIT key 7 1                # Bitmaps
GETBIT key 7

# Lua scripting (atomic operations)
EVAL "
  local current = redis.call('GET', KEYS[1])
  if current then
    redis.call('SET', KEYS[1], ARGV[1])
    return 1
  else
    return 0
  end
" 1 key value

# Modules
RedisJSON, RedisSearch, RedisGraph, RedisBloom, RedisTimeSeries

# Cluster mode (sharding)
# Sentinel (HA + auto-failover)
```

### Memcached

```python
# When to use Memcached vs Redis:
# Memcached: simpler, multi-threaded, pure cache, larger values
# Redis: feature-rich, single-threaded (cluster shards), persistence, pub/sub

from pymemcache.client.base import Client

client = Client(('memcached', 11211))
client.set('key', 'value', expire=300)
value = client.get('key')

# Slabs, LRU eviction, no persistence
```

### CDN Caching (HTTP)

```nginx
# Nginx caching example
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=app_cache:10m 
                max_size=10g inactive=60m use_temp_path=off;

location /api/products {
    proxy_cache app_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_valid 404 1m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
    proxy_cache_bypass $http_cache_control;
    add_header X-Cache-Status $upstream_cache_status;
    proxy_pass http://backend;
}

# Cloudflare CDN caching
# Page Rules: Cache Level, Edge TTL, Browser TTL
# Cache API: purge by URL, tag, prefix, host
```

### Cache Technology Selection

| Need | Choose |
|------|--------|
| In-process, fast, simple | Caffeine, Guava, cachetools, freecache |
| Distributed, feature-rich | Redis |
| Distributed, simple, large values | Memcached |
| HTTP-level, CDN | Varnish, Nginx, Cloudflare |
| Persistent cache | RocksDB, Aerospike |
| Edge / global | Cloudflare Workers KV, Lambda@Edge |

---

## 6.6 Distributed Cache Patterns

### Redis Cluster

```
┌─────────────────────────────────────────────────────────────┐
│  REDIS CLUSTER (16384 hash slots)                            │
│                                                             │
│  Slot 0-5460     Slot 5461-10922    Slot 10923-16383        │
│  ┌─────────────┐ ┌─────────────┐   ┌─────────────┐          │
│  │ Master 1    │ │ Master 2    │   │ Master 3    │          │
│  │ + Replica   │ │ + Replica   │   │ + Replica   │          │
│  └─────────────┘ └─────────────┘   └─────────────┘          │
│                                                             │
│  Key routing: CRC16(key) mod 16384 = slot                   │
│  Client knows topology, routes directly                     │
│  Replica promotion on master failure                        │
└─────────────────────────────────────────────────────────────┘
```

### Cache Topology Patterns

```
PATTERN 1: Client-Side Cache + Distributed Cache
  App → Local (L1) → Miss → Redis (L2) → Miss → DB
  
  Pros: Very fast (sub-ms) on L1 hits
  Cons: Stale data across instances

PATTERN 2: Distributed Cache Only
  App → Redis → Miss → DB
  
  Pros: Single source of truth, simpler invalidation
  Cons: Network hop on every request

PATTERN 3: Read-Through Cache
  App → Cache (transparent to app) → DB
  
  Pros: App doesn't know about DB
  Cons: Cache is critical path

PATTERN 4: CDN + Edge Cache
  Client → CDN PoP → Origin
  
  Pros: Global latency, offloads origin
  Cons: Stale data, complex invalidation
```

---

## 6.7 Cache Coherence & Consistency

### Cache Coherence Problem

```
Instance 1 has key X = "A" (in L1)
Instance 2 has key X = "A" (in L1)
Instance 3 updates DB, invalidates Redis (L2)

Now:
  Redis: empty
  Instance 1 L1: "A" (stale!)
  Instance 2 L1: "A" (stale!)

Instance 1's read: serves "A" from L1 (stale)
Instance 2's read: serves "A" from L1 (stale)
Instance 3's read: cache miss, fetches fresh from DB, populates L1 with "B"
```

### Coherence Strategies

```python
# 1. Short L1 TTL
# L1 TTL = 1s, L2 TTL = 5min
# L1 hits fast, eventually consistent
cache_l1 = TTLCache(ttl=1)

# 2. Cache invalidation broadcast (pub/sub)
class CoherentCache:
    async def update(self, key, value):
        await db.update(key, value)
        await self.cache.delete(key)
        # Notify all instances to invalidate L1
        await self.pubsub.publish("cache.invalidate", {"key": key})
    
    async def _listener(self):
        async for msg in self.pubsub.listen("cache.invalidate"):
            self.local_cache.pop(msg["key"], None)

# 3. Version-based
# Tag cached values with version
async def get(self, key):
    cached = self.local_cache.get(key)
    if cached:
        data, version = cached
        if await self.is_fresh(key, version):
            return data
    return await self._fetch_and_cache(key)

# 4. Read-through with single shared cache
# No L1, just shared Redis. Less optimal latency.
```

### Multi-Region Cache Coherence

```
REGION A          REGION B
   │                  │
 Redis A            Redis B
   │                  │
   └────── Replicate ─┘
       (Redis CRDT, write-through, or async)

For multi-region cache coherence:
  • Active-Active with conflict resolution
  • Active-Passive with primary writes
  • Per-region cache with eventual consistency
  • CRDT-based caches (e.g., PnR + vector clocks)
```

---

## 6.8 Negative Caching

### Cache Misses Too

```python
# Cache "NOT FOUND" results too
async def get_user(self, user_id):
    cache_key = f"user:{user_id}"
    value = await cache.get(cache_key)
    
    if value is not None:
        if value == b"__NOT_FOUND__":
            return None  # Known missing
        return json.loads(value)
    
    # Cache miss
    user = await db.find_user(user_id)
    if user:
        await cache.set(cache_key, json.dumps(user), ttl=300)
    else:
        # Cache negative result for short TTL
        await cache.set(cache_key, b"__NOT_FOUND__", ttl=60)
    return user

# Protects DB from repeated queries for non-existent data
# Common: bots searching for /wp-admin, .env, etc.
```

---

## 6.9 Cache Warming & Pre-loading

### Strategies

```python
# 1. Application startup warm-up
async def warm_cache_on_startup():
    # Top 1000 hot products
    hot_products = await db.get_top_products(1000)
    for product in hot_products:
        await cache.set(f"product:{product.id}", product, ttl=3600)

# 2. Scheduled refresh
@scheduler.cron("*/15 * * * *")  # Every 15 minutes
async def refresh_hot_keys():
    hot_keys = await analytics.get_top_keys(100)
    for key in hot_keys:
        value = await db.query(key)
        await cache.set(key, value, ttl=3600)

# 3. Just-in-time warming after invalidation
async def update_with_warm(key, value):
    await db.update(key, value)
    await cache.delete(key)
    # Read-through will populate on first access
    # OR: actively repopulate
    await cache.set(key, value, ttl=300)

# 4. Bulk warming for new features
async def warm_for_new_feature():
    affected_users = await db.get_active_users()
    for user in affected_users:
        await cache.set(f"feature_flag:{user.id}", {"new_ui": True}, ttl=3600)
```

---

## 6.10 Cache Security

### Common Vulnerabilities

```
┌─────────────────────────────────────────────────────────────────┐
│  CACHE SECURITY CONCERNS                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. CACHE POISONING                                             │
│     Attacker injects malicious cached content                  │
│     Mitigation: validate inputs, integrity checks, isolation   │
│                                                                 │
│  2. CACHE SIDE-CHANNEL ATTACKS                                 │
│     Timing attacks reveal if key exists                       │
│     Mitigation: constant-time responses, uniform caching      │
│                                                                 │
│  3. SENSITIVE DATA EXPOSURE                                     │
│     Cache contains PII, secrets, tokens                       │
│     Mitigation: encrypt, scope keys, strict ACLs              │
│                                                                 │
│  4. UNAUTHORIZED ACCESS                                         │
│     Direct cache access bypasses app auth                      │
│     Mitigation: don't expose cache directly, firewall          │
│                                                                 │
│  5. DOS VIA CACHE STARVATION                                   │
│     Attacker fills cache, evicts legit data                   │
│     Mitigation: rate limiting, isolation by tenant            │
│                                                                 │
│  6. DNS REBINDING (for client-side cache)                      │
│     Attacker accesses internal cache via DNS trick            │
│     Mitigation: same-origin policy, firewall                  │
└─────────────────────────────────────────────────────────────────┘
```

### Secure Caching Practices

```python
# Don't cache sensitive data without protection
async def get_pii(user_id, requester_id):
    if not await can_access_pii(requester_id, user_id):
        raise PermissionError()
    
    cache_key = f"pii:{user_id}:{hash(requester_id)}"  # Scoped
    value = await cache.get(cache_key)
    if value is None:
        value = await db.get_pii(user_id)
        await cache.set(cache_key, value, ttl=300)
    return value

# Encrypt cached values for defense in depth
async def get_secure(key):
    encrypted = await cache.get(key)
    if encrypted:
        return decrypt(encrypted)
    value = await db.query(key)
    await cache.set(key, encrypt(value), ttl=300)
    return value

# Use separate cache namespaces per tenant
# Cache key: "tenant_A:user:123" vs "tenant_B:user:123"
```

---

## 6.11 Cache Monitoring & Metrics

### Key Metrics

```python
# Cache metrics to track:
cache_hits_total              # Total hits
cache_misses_total             # Total misses
cache_hit_ratio = hits / (hits + misses)  # Goal: >90%
cache_evictions_total          # Items evicted (cache pressure)
cache_memory_used_bytes       # Memory usage
cache_key_count               # Number of keys
cache_get_latency_seconds     # Latency histogram
cache_set_latency_seconds
cache_errors_total            # Connection errors, etc.

# Per-key metrics for hot keys
cache_key_hits{key="user:123"}  # Label-based metrics
```

### Monitoring Example (Prometheus)

```python
# Using prometheus_client
from prometheus_client import Counter, Histogram, Gauge

cache_hits = Counter('cache_hits_total', 'Cache hits', ['cache', 'key_pattern'])
cache_misses = Counter('cache_misses_total', 'Cache misses', ['cache', 'key_pattern'])
cache_latency = Histogram('cache_operation_seconds', 'Cache latency', 
                         ['cache', 'operation'])
cache_size = Gauge('cache_size_bytes', 'Cache size', ['cache'])

class InstrumentedCache:
    async def get(self, key):
        with cache_latency.labels(cache='redis', operation='get').time():
            value = await redis.get(key)
        if value is None:
            cache_misses.labels(cache='redis', key_pattern=self._pattern(key)).inc()
        else:
            cache_hits.labels(cache='redis', key_pattern=self._pattern(key)).inc()
        return value
```

### Cache Health Alerts

```yaml
Alerts:
  - alert: CacheHitRatioTooLow
    expr: cache_hit_ratio < 0.7
    for: 10m
    annotations:
      summary: "Cache hit ratio {{ $value }} for {{ $labels.cache }}"
  
  - alert: CacheMemoryHigh
    expr: cache_size_bytes / cache_max_bytes > 0.85
    for: 5m
    annotations:
      summary: "Cache at {{ $value }}% capacity"
  
  - alert: CacheLatencyHigh
    expr: histogram_quantile(0.99, cache_operation_seconds) > 0.05
    for: 5m
    annotations:
      summary: "p99 cache latency {{ $value }}s"
```

---

## 6.12 Cache Sizing & Capacity

### Memory Sizing

```
Formula:
  Cache size = num_keys × avg_value_size × overhead_factor

Example:
  1M users × 5KB profile = 5 GB
  × overhead 1.5 (Redis overhead) = 7.5 GB
  × 1.5 headroom = 11 GB

  Plus: hot data, sessions, etc.

Common cache sizes:
  • Small app: 2-8 GB
  • Medium app: 16-64 GB
  • Large app: 128-512 GB
  • Hyperscaler: TB-scale with sharding
```

### Cache Pressure Detection

```bash
# Redis
redis-cli INFO memory
# Used memory, peak memory, fragmentation ratio

# Check eviction policy
redis-cli CONFIG GET maxmemory-policy
# Options: noeviction, allkeys-lru, volatile-lru, allkeys-lfu, etc.

# Hit ratio
redis-cli INFO stats | grep keyspace
# keyspace_hits / (keyspace_hits + keyspace_misses)

# Hot keys (Redis 4.0+)
redis-cli --hotkeys

# Memory analysis
redis-cli MEMORY USAGE <key>
```

---

## 6.13 Anti-Patterns

### Caching Anti-Patterns to Avoid

```
1. CACHE EVERYTHING
   → Memory cost, invalidation complexity, low hit ratio
   → Cache only what's hot

2. NO TTL ON KEYS
   → Memory growth, stale data forever
   → Always set TTL

3. CACHE OBJECTS THAT CHANGE WITH EVERY REQUEST
   → 0% hit ratio, wasted memory
   → Profile before caching

4. UPDATING CACHE INSTEAD OF INVALIDATING
   → Race conditions, stale values
   → DELETE the key, let next read repopulate

5. NOT HANDLING CACHE FAILURES
   → Cascading failure if cache dies
   → Cache misses should fall back to DB

6. CACHING BIG OBJECTS (>1MB)
   → Network overhead, low hit ratio
   → Cache smaller, normalized pieces

7. NOT USING CACHE ASIDE PATTERN
   → Read-through as default when cache-aside is better
   → Match pattern to use case

8. IGNORING CACHE STAMPEDE
   → Cache miss = DB overload
   → Use locking, xfetch, or stale-while-revalidate

9. CACHING WITHOUT MONITORING
   → Don't know if cache is effective
   → Measure hit ratio, latency, errors

10. UNIFORM TTL FOR ALL DATA
    → Same TTL for rarely vs frequently changing data
    → Use different TTLs per data type
```

---

## 6.14 Exercises

### Exercise 1: Pattern Selection
For each scenario, choose the caching pattern and justify:
- Product catalog (5M items, updated daily)
- User session (high write rate, low latency)
- Shopping cart (frequent updates, multi-tab)
- API responses (read-heavy, medium-sized JSON)
- Search results (compute-heavy aggregation)

### Exercise 2: Cache Stampede Solution
A news site has 10K QPS. Their cache TTL is 60s. When cache expires:
- All requests hit DB simultaneously
- DB overwhelmed

Design a multi-layered solution. Include code/config.

### Exercise 3: Invalidation Strategy
E-commerce platform with 100K products, prices change frequently (sometimes flash sales):
- Cache key design
- TTL strategy
- Invalidation mechanism
- Coherence across instances

### Exercise 4: Multi-Tier Cache
Design a 3-tier caching strategy for a global SaaS:
- Tier 1 (browser/CDN)
- Tier 2 (edge compute)
- Tier 3 (in-region cache)
- What goes in each tier
- Invalidation across tiers

### Exercise 5: Cache Coherence
Two app instances with L1 cache. User A updates via Instance 1, Instance 2 reads via L1.
- Design invalidation propagation
- Handle network partitions
- Handle Redis failures

---

## 6.15 Further Reading

### Books
- *Designing Data-Intensive Applications* — Kleppmann (Ch. 5)
- *Caching at Reddit*](https://reddit.com) — Engineering blog
- *Redis in Action* — Josiah Carlson
- *Web Caching* — Duane Wessels (O'Reilly, free online)

### Documentation
- [Redis Documentation](https://redis.io/documentation)
- [Memcached Wiki](https://github.com/memcached/memcached/wiki)
- [Caffeine User Guide](https://github.com/ben-manes/caffeine/wiki)
- [Cloudflare Caching Docs](https://developers.cloudflare.com/cache/)

### Blog Posts & Papers
- [Caching Best Practices](https://aws.amazon.com/caching/best-practices/)
- [Facebook's Memcache Scaling](https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final14_update.pdf)
- [TAO: How Facebook Serves the Social Graph](https://www.usenix.org/system/files/conference/atc13/atc13-bronson.pdf)
- [Scaling Memcache at Facebook](https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final14_update.pdf)

---

## 6.16 Summary Checklist

- [ ] Can identify what to cache (and what not to)
- [ ] Can implement cache-aside pattern
- [ ] Understand read-through, write-through, write-behind trade-offs
- [ ] Can design cache invalidation strategy
- [ ] Can prevent cache stampede with locking/xfetch/SWR
- [ ] Know Redis, Memcached, CDN trade-offs
- [ ] Can implement multi-tier caching
- [ ] Can handle cache coherence across instances
- [ ] Can monitor cache effectiveness
- [ ] Can size cache properly for workload

---

> **Next Chapter**: [Chapter 7: Message Queues & Event-Driven Architecture](../chapters/07-message-queues-event-driven.md) — Decouple services and scale asynchronously.