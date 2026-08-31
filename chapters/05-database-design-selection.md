# Chapter 5: Database Design & Selection

> **Estimated Time:** 6–8 hours | **Prerequisites:** Chapters 1–4 and SQL basics<br>
> **Last reviewed:** 2026-08-31 | **Level:** Foundation → applied → production judgment

---

## 🎯 Learning Objectives

By the end of this chapter, you will be able to:

1. **Build an evidence-based database shortlist** from workload and correctness requirements
2. **Design normalized and denormalized schemas** purposefully
3. **Apply indexing strategies** that match query patterns
4. **Understand ACID vs BASE** trade-offs in real systems
5. **Implement replication** patterns for high availability
6. **Plan backward-compatible schema changes** with measured lock and rollback risk
7. **Tune database performance** for production workloads

---

## 5.1 Database Selection — The Right Tool for the Job

### Decision Framework

```
┌─────────────────────────────────────────────────────────────────┐
│  DATABASE SELECTION TREE                                        │
├─────────────────────────────────────────────────────────────────┤
│  Start: What are your data characteristics?                     │
│                                                                 │
│  ├── Structured + Relational queries + ACID → Relational (SQL)  │
│  │     ├── Single-node → PostgreSQL, MySQL                      │
│  │     ├── Distributed SQL → CockroachDB, TiDB, Spanner         │
│  │     └── OLAP → Snowflake, BigQuery, Redshift, ClickHouse     │
│  │                                                              │
│  ├── Flexible schema + Document-oriented → Document Store       │
│  │     └── MongoDB, CouchDB, Firestore, DocumentDB              │
│  │                                                              │
│  ├── Massive scale + Simple access → Wide-Column                │
│  │     └── Cassandra, ScyllaDB, HBase                           │
│  │                                                              │
│  ├── Graph relationships → Graph DB                             │
│  │     └── Neo4j, Neptune, JanusGraph, ArangoDB                 │
│  │                                                              │
│  ├── Search + Full-text → Search Engine                         │
│  │     └── Elasticsearch, OpenSearch, Meilisearch, Typesense    │
│  │                                                              │
│  ├── Time-series data → TSDB                                   │
│  │     └── InfluxDB, TimescaleDB, Prometheus, QuestDB           │
│  │                                                              │
│  ├── Key-Value cache/session → In-Memory KV                     │
│  │     └── Redis, Memcached, KeyDB, DragonflyDB                 │
│  │                                                              │
│  └── Append-only events → Log/WAL/Event Store                   │
│        └── Kafka, Pulsar, EventStoreDB, NATS JetStream          │
└─────────────────────────────────────────────────────────────────┘
```

### Comparison Matrix

| Database | Type | Consistency | Scale | Best For |
|----------|------|-------------|-------|----------|
| **PostgreSQL** | RDBMS | Strong (ACID) | Vertical + read replicas | General-purpose, complex queries |
| **MySQL** | RDBMS | Strong (ACID) | Vertical + Vitess sharding | Web apps, OLTP |
| **MongoDB** | Document | Tunable | Sharding built-in | Flexible schema, document model |
| **Cassandra** | Wide-column | Tunable | Horizontal partitioning | High-write workloads designed around known queries |
| **Redis** | In-memory data store | Command execution is local/serialized; replication is normally asynchronous | Cluster mode | Cache, ephemeral state, streams |
| **DynamoDB** | KV + Document | Tunable | Auto-scaling | Serverless, predictable latency |
| **CockroachDB** | Distributed SQL | Strong (serializable) | Horizontal | Global SQL, geo-distribution |
| **TiDB** | Distributed SQL | Strong | Horizontal | MySQL-compatible distributed |
| **Spanner** | Distributed SQL | External consistency | Global | Google-scale workloads |
| **Elasticsearch** | Search | Eventually consistent | Sharding | Full-text, log analytics |
| **ClickHouse** | Columnar OLAP | Strong | Vertical + sharding | Analytics, BI |
| **Snowflake** | Cloud DW | Strong | Serverless | Data warehousing |
| **Neo4j** | Graph | ACID | Clustering | Social, recommendations |
| **InfluxDB** | TSDB | Tunable | Clustering | Metrics, monitoring |
| **Object storage** | Object | Provider-specific consistency and durability contract | Provider-managed | Files, backups, data lake |

---

## 5.2 Relational Database Deep Dive

### PostgreSQL Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  POSTGRESQL ARCHITECTURE                                        │
├─────────────────────────────────────────────────────────────────┤
│  Client Connections (libpq)                                     │
│         │                                                       │
│         ▼                                                       │
│  Postmaster (accepts connections, starts backend processes)     │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                               │
│  │   Parser     │ → Query Tree                                  │
│  ├──────────────┤                                               │
│  │  Analyzer    │ → Query Tree (validated, optimized)            │
│  ├──────────────┤                                               │
│  │  Rewriter    │ → Apply rules (views, RLS)                    │
│  ├──────────────┤                                               │
│  │  Planner     │ → Execution Plan                              │
│  ├──────────────┤                                               │
│  │  Executor    │ → Run query                                   │
│  └──────┬───────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  Storage Layer (Heap, B-tree, GIN, GiST, BRIN indexes)          │
│  WAL (Write-Ahead Log) + Background Writer + Checkpointer       │
│  Buffer Cache (shared_buffers) + OS Page Cache                  │
└─────────────────────────────────────────────────────────────────┘
```

### ACID in PostgreSQL

```sql
-- Atomicity: Transaction commits or rolls back entirely
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;  -- Or ROLLBACK on error

-- Consistency: Constraints enforced
ALTER TABLE accounts ADD CONSTRAINT positive_balance 
  CHECK (balance >= 0);

-- Isolation: Configurable per transaction
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- Durability depends on WAL, fsync, synchronous_commit, storage behavior,
-- replication policy, and which failure scope the requirement covers.
```

### Isolation Levels

```
┌─────────────────────────────────────────────────────────────────┐
│  ISOLATION LEVELS (Strict → Lenient)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  READ UNCOMMITTED ← Weakest                                    │
│    • SQL-standard level; PostgreSQL treats it as READ COMMITTED│
│                                                                 │
│  READ COMMITTED (PostgreSQL default)                            │
│    • Only sees committed data                                  │
│    • Each statement sees a new snapshot                        │
│    • Possible: non-repeatable reads, phantom reads             │
│                                                                 │
│  REPEATABLE READ                                                │
│    • Snapshot at transaction start                              │
│    • PostgreSQL prevents non-repeatable and phantom reads       │
│    • Write skew possible                                        │
│                                                                 │
│  SERIALIZABLE (PostgreSQL uses SSI)                             │
│    • True serializable, no anomalies                           │
│    • May abort conflicting transactions                         │
│    • Requires retry handling for serialization failures        │
│                                                                 │
│  Anomalies to prevent:                                          │
│    • Dirty reads, Non-repeatable reads, Phantom reads          │
│    • Lost updates, Write skew, Read skew                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5.3 Schema Design

### Normalization vs Denormalization

```sql
-- 1NF: Atomic values, no repeating groups
-- 2NF: 1NF + no partial dependencies
-- 3NF: 2NF + no transitive dependencies
-- BCNF: 3NF + every determinant is a candidate key

-- Example: Normalized (3NF)
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255),
  country_id INT REFERENCES countries(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE orders (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id),
  total NUMERIC(10, 2),
  status VARCHAR(20),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE order_items (
  id BIGSERIAL PRIMARY KEY,
  order_id BIGINT REFERENCES orders(id),
  product_id BIGINT REFERENCES products(id),
  quantity INT,
  price NUMERIC(10, 2)
);

-- Denormalized for read performance
CREATE TABLE order_summary (
  order_id BIGINT PRIMARY KEY,
  user_email VARCHAR(255),  -- from users
  user_country VARCHAR(50), -- from countries
  total NUMERIC(10, 2),
  item_count INT,
  last_updated TIMESTAMPTZ
);
```

### Schema Design Best Practices

```sql
-- GOOD PRACTICES:
-- 1. Choose keys from access, locality, exposure, and generation requirements
-- 2. Add lifecycle timestamps only when the domain or operations need them
-- 3. Use TIMESTAMPTZ not TIMESTAMP (timezone-aware)
-- 4. Use NUMERIC for money, never FLOAT
-- 5. Use ENUM sparingly; prefer VARCHAR + check constraints
-- 6. Foreign keys with ON DELETE behavior (CASCADE, RESTRICT, SET NULL)
-- 7. Index foreign keys and queried columns when measured access paths justify it
-- 8. Use partial indexes for sparse data
-- 9. Add comments on tables and key columns
-- 10. Version your schema (use migrations, never ad-hoc)

-- BAD PRACTICES:
-- ✗ Storing comma-separated values in VARCHAR
-- ✗ Storing JSON without structure
-- ✗ Choosing random keys without evaluating index locality and storage cost
-- ✗ Storing dates as strings
-- ✗ Storing money as float/double
-- ✗ Boolean traps (status = 0/1/2/3/4 instead of enum)
```

### Schema Migration Patterns

```python
# Flyway-style migration (numbered SQL files)
# V001__create_users.sql
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL
);

# V002__add_user_name.sql
ALTER TABLE users ADD COLUMN name VARCHAR(255);

# V003__add_index.sql
CREATE INDEX idx_users_email ON users(email);
```

### Online, Backward-Compatible Migrations

```
┌─────────────────────────────────────────────────────────────────┐
│  EXPAND-CONTRACT MIGRATION                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: EXPAND (backward compatible)                           │
│    • Add new column nullable                                   │
│    • Add new table (empty)                                     │
│    • Old code keeps working                                    │
│                                                                 │
│  Step 2: MIGRATE (backfill + dual write)                       │
│    • Backfill new column/table from old                         │
│    • Application writes to BOTH old and new                    │
│    • Reads from old (still primary)                            │
│                                                                 │
│  Step 3: CONTRACT (cleanup)                                    │
│    • Application reads from new                                │
│    • Stop writing to old                                        │
│    • Drop old column/table                                     │
│                                                                 │
│  ✓ Can avoid planned downtime when locks, backfill and deploys are controlled│
│  ✗ Not automatically reversible after destructive writes or cleanup│
│  ✗ Requires discipline and dual-code paths                     │
└─────────────────────────────────────────────────────────────────┘

Example: Rename column "name" → "full_name"
  EXPAND:  ALTER TABLE users ADD COLUMN full_name VARCHAR(255);
  MIGRATE: Backfill in bounded, restartable batches
          App writes both name and full_name
  CONTRACT: UPDATE users SET full_name = name WHERE full_name IS NULL;
           App reads full_name only
           ALTER TABLE users DROP COLUMN name;
```

---

## 5.4 Indexing Strategies

### B-Tree Index (Default, Most Common)

```sql
-- Single column
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- Composite index (column order matters!)
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
-- Optimizes: WHERE user_id = ? AND status = ?
-- Doesn't optimize: WHERE status = ? (without user_id)

-- Descending for ORDER BY DESC queries
CREATE INDEX idx_orders_created_desc ON orders(created_at DESC);

-- Partial index (only index subset)
CREATE INDEX idx_pending_orders ON orders(user_id) 
  WHERE status = 'pending';

-- Expression index
CREATE INDEX idx_users_lower_email ON users(LOWER(email));
```

### Index Types

| Type | Use Case | Example |
|------|----------|---------|
| **B-Tree** | Equality, range, ORDER BY | Default, most cases |
| **Hash** | Equality only | Consider only after measuring against B-tree; fewer access patterns |
| **GIN** | Full-text, JSONB, arrays | `to_tsvector(col)`, JSONB operators |
| **GiST** | Geometric, full-text, ranges | PostGIS, range types |
| **BRIN** | Very large tables with natural order | Time-series logs |
| **Partial** | Sparse data | `WHERE deleted_at IS NULL` |
| **Expression** | Computed values | `LOWER(email)` |
| **Covering** | Include non-indexed columns | `INCLUDE (column)` |

### Query Optimization with EXPLAIN

```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE) 
SELECT * FROM orders 
WHERE user_id = 123 
  AND status = 'pending'
ORDER BY created_at DESC 
LIMIT 20;

-- Look for:
-- • Seq Scan can be optimal for small tables or large result fractions
-- • Index Scan trades index traversal and random heap access for selectivity
-- • Index Only Scan can avoid heap fetches when visibility and coverage permit
-- • Sort (acceptable if small result set)
-- • Nested Loop / Hash Join / Merge Join (depending on data)
-- • Estimated vs actual rows; large differences may indicate stale statistics,
--   correlation, skew, or an expression the planner cannot estimate well

-- Update statistics
ANALYZE orders;
```

### Common Query Patterns

```sql
-- Pagination: Cursor-based (better than OFFSET for large datasets)
SELECT * FROM orders
WHERE user_id = 123 
  AND (created_at, id) < ($last_ts, $last_id)
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- Counters: Use atomic operations
UPDATE counters SET value = value + 1 WHERE key = 'visits';

-- Search: Use GIN for full-text
CREATE INDEX idx_products_search ON products 
  USING GIN (to_tsvector('english', name || ' ' || description));

SELECT * FROM products
WHERE to_tsvector('english', name || ' ' || description) 
  @@ to_tsquery('english', 'laptop & gaming');

-- Time-series aggregation
SELECT date_trunc('hour', created_at) as hr, count(*)
FROM events
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY 1
ORDER BY 1;

-- Use BRIN for very large time-series tables
CREATE INDEX idx_events_created_brin ON events USING BRIN(created_at);
```

---

## 5.5 NoSQL Databases

### Document Store (MongoDB)

```javascript
// MongoDB Document Model
{
  _id: ObjectId("..."),
  username: "alice",
  email: "alice@example.com",
  profile: {
    name: "Alice Smith",
    bio: "Software Engineer",
    location: { city: "Istanbul", country: "TR" }
  },
  posts: [
    { id: 1, title: "First post", createdAt: ISODate("...") },
    { id: 2, title: "Second post", createdAt: ISODate("...") }
  ],
  tags: ["tech", "music"],
  createdAt: ISODate("..."),
  updatedAt: ISODate("...")
}

// Indexing
db.users.createIndex({ email: 1 }, { unique: true })
db.posts.createIndex({ "author.id": 1, createdAt: -1 })
db.posts.createIndex({ 
  title: "text", 
  body: "text" 
}, { weights: { title: 10, body: 1 } })

// Aggregation Pipeline
db.orders.aggregate([
  { $match: { status: "completed", createdAt: { $gte: ISODate("2024-01-01") } } },
  { $group: { _id: "$customer_id", total: { $sum: "$amount" } } },
  { $sort: { total: -1 } },
  { $limit: 100 }
])
```

### Wide-Column (Cassandra)

```cql
-- Keyspace & Table
CREATE KEYSPACE ecommerce WITH replication = {
  'class': 'NetworkTopologyStrategy',
  'dc1': 3,
  'dc2': 3
};

CREATE TABLE orders_by_customer (
  customer_id UUID,
  order_date DATE,
  order_id UUID,
  total DECIMAL,
  status TEXT,
  PRIMARY KEY ((customer_id), order_date, order_id)
) WITH CLUSTERING ORDER BY (order_date DESC, order_id DESC);

-- Query (must include partition key)
SELECT * FROM orders_by_customer 
WHERE customer_id = ? 
  AND order_date >= ? 
  AND order_date <= ?
LIMIT 100;

-- Materialized view for different access pattern
CREATE MATERIALIZED VIEW orders_by_status AS
  SELECT * FROM orders_by_customer
  WHERE status IS NOT NULL AND customer_id IS NOT NULL 
        AND order_date IS NOT NULL AND order_id IS NOT NULL
  PRIMARY KEY ((status), order_date, customer_id, order_id);
```

### In-Memory KV (Redis)

```bash
# Data structures
SET user:123:name "Alice"
HSET user:123 name "Alice" email "alice@example.com" age 30
LPUSH queue:emails "msg1" "msg2" "msg3"
ZADD leaderboard 100 "alice" 95 "bob" 87 "charlie"

# Expiry
SETEX session:abc 3600 "{user_id: 123}"
EXPIRE user:123 60

# Atomic operations
INCR page:views
DECR inventory:item:456

# Pub/Sub
SUBSCRIBE notifications
PUBLISH notifications "New order #123"

# Streams (Kafka-like)
XADD events * type "order_created" order_id "123" amount "100"
XREAD BLOCK 0 STREAMS events $
XLEN events

# Modules
RedisJSON, RedisSearch, RedisGraph, RedisTimeSeries
```

### Cassandra Data Modeling

```
CASSANDRA QUERY-FIRST DESIGN:

1. List all queries the application needs
2. For each query, design a table that satisfies it
3. Denormalize aggressively — multiple tables per entity
4. Use partition key that matches query pattern

Anti-patterns to avoid:
  ✗ Secondary indexes (slow, expensive)
  ✗ Multi-partition queries (no joins)
  ✗ ORDER BY without clustering order match
  ✗ Using ALLOW FILTERING (last resort)
```

---

## 5.6 NewSQL — Distributed SQL

### CockroachDB Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  COCKROACHDB: SQL + Distributed + ACID                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Node 1  │  │  Node 2  │  │  Node 3  │  │  Node N  │        │
│  │ SQL+KV+  │  │ SQL+KV+  │  │ SQL+KV+  │  │ SQL+KV+  │        │
│  │ Raft     │  │ Raft     │  │ Raft     │  │ Raft     │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │             │             │             │               │
│       └─────────────┴─────────────┴─────────────┘               │
│                       │                                         │
│            ┌──────────▼──────────┐                              │
│            │  Distributed KV     │                              │
│            │  (Raft-replicated)  │                              │
│            └─────────────────────┘                              │
│                                                                 │
│  Features:                                                      │
│    • PostgreSQL wire-compatible                                 │
│    • Distributed ACID transactions                              │
│    • Auto-rebalancing shards                                    │
│    • Geo-partitioning for data residency                        │
│    • Survives disk, node, rack, DC failures                     │
└─────────────────────────────────────────────────────────────────┘
```

### TiDB (MySQL-Compatible Distributed)

```sql
-- Use just like MySQL
CREATE TABLE orders (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT,
  total DECIMAL(10, 2),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user (user_id)
);

-- TiDB handles distribution under the hood
-- TiKV stores rows, TiDB computes SQL, PD schedules placement

-- HTAP: Run OLAP queries on same data
SELECT user_id, SUM(total) 
FROM orders 
WHERE created_at > '2024-01-01' 
GROUP BY user_id;
```

---

## 5.7 Specialized Databases

### Time-Series Databases

```sql
-- TimescaleDB (PostgreSQL extension)
CREATE TABLE metrics (
  time TIMESTAMPTZ NOT NULL,
  device_id INT,
  cpu NUMERIC(5, 2),
  memory NUMERIC(5, 2),
  temperature NUMERIC(5, 2)
);

SELECT create_hypertable('metrics', 'time');

-- Continuous aggregates (auto-refresh)
CREATE MATERIALIZED VIEW metrics_hourly
WITH (timescaledb.continuous) AS
SELECT 
  time_bucket('1 hour', time) AS hour,
  device_id,
  AVG(cpu) AS avg_cpu,
  MAX(temperature) AS max_temp
FROM metrics
GROUP BY 1, 2;

-- Compression (10-20x)
ALTER TABLE metrics SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'device_id'
);

SELECT add_compression_policy('metrics', INTERVAL '7 days');
```

```sql
-- InfluxDB (purpose-built TSDB)
INSERT temperature,device=server1 value=23.5
INSERT temperature,device=server1,room=lab value=24.1

SELECT mean(value) 
FROM temperature 
WHERE time > now() - 1h 
GROUP BY time(5m), device
```

### Graph Databases

```cypher
-- Neo4j Cypher
CREATE (alice:Person {name: 'Alice', age: 30})
CREATE (bob:Person {name: 'Bob', age: 32})
CREATE (acme:Company {name: 'ACME Corp'})
CREATE (alice)-[:WORKS_FOR {since: 2020}]->(acme)
CREATE (bob)-[:WORKS_FOR]->(acme)
CREATE (alice)-[:KNOWS {since: 2018}]->(bob)

// Find friends of friends who work at ACME
MATCH (me:Person {name: 'Alice'})-[:KNOWS]-(:Person)-[:KNOWS]-(fof:Person)
      -[:WORKS_FOR]->(c:Company {name: 'ACME Corp'})
WHERE me <> fof
RETURN DISTINCT fof.name
```

### Search Engines

```json
// Elasticsearch Document
PUT /products/_doc/123
{
  "name": "Gaming Laptop",
  "description": "High-performance laptop for gaming",
  "price": 1499.99,
  "category": "electronics",
  "tags": ["laptop", "gaming", "rtx"],
  "specs": {
    "cpu": "i7-13700H",
    "gpu": "RTX 4060",
    "ram_gb": 16
  },
  "in_stock": true,
  "created_at": "2024-01-15T10:00:00Z"
}

// Search with boosting, fuzzy matching
GET /products/_search
{
  "query": {
    "bool": {
      "must": [
        { "multi_match": { 
          "query": "gaming laptop",
          "fields": ["name^3", "description", "tags^2"],
          "fuzziness": "AUTO"
        }}
      ],
      "filter": [
        { "term": { "in_stock": true } },
        { "range": { "price": { "lte": 2000 } } }
      ]
    }
  },
  "highlight": { "fields": { "description": {} } }
}
```

---

## 5.8 Replication Patterns (Detailed)

### PostgreSQL Streaming Replication

```bash
# Primary: postgresql.conf
wal_level = replica
max_wal_senders = 5
wal_keep_size = '1GB'
archive_mode = on
archive_command = 'cp %p /var/lib/pgsql/archive/%f'

# Standby: recovery.conf (now postgresql.auto.conf)
primary_conninfo = 'host=primary port=5432 user=replicator password=...'
restore_command = 'cp /var/lib/pgsql/archive/%f %p'
standby_mode = on

# Promote standby
pg_ctl promote -D /var/lib/pgsql/data
```

### Logical Replication (Selective)

```sql
-- Publication on primary
CREATE PUBLICATION orders_pub FOR TABLE orders, order_items;

-- Subscription on replica
CREATE SUBSCRIPTION orders_sub 
CONNECTION 'host=primary dbname=mydb user=replicator' 
PUBLICATION orders_pub;

-- Use cases:
-- • Selective replication (specific tables)
-- • Cross-version replication
-- • Migration and integration pipelines
-- Native PostgreSQL logical replication is publish/subscribe; bidirectional
-- or multi-writer designs need additional conflict and sequence management.
```

### Synchronous vs Asynchronous Trade-offs

```
SYNCHRONOUS:
  ✓ Can protect acknowledged transactions within the configured failure scope
  ✗ Higher write latency (waits for replica ack)
  ✗ Availability depends on quorum policy and healthy synchronous standbys

ASYNCHRONOUS:
  ✓ Fast writes, high availability
  ✗ Possible data loss on failover (RPO > 0)

SEMI-SYNCHRONOUS:
  ✓ Primary waits for at least one sync replica
  ✓ Reasonable balance
  ✓ Used by MySQL, AWS RDS Multi-AZ

CONFIGURATION:
  PostgreSQL synchronous_standby_names = 'ANY 1 (node2,node3)'
  MySQL terminology and variable names depend on the deployed release;
  verify against that version's official replication documentation.
```

---

## 5.9 Database Performance Tuning

### PostgreSQL Configuration

The following parameters are an investigation checklist, not a production
configuration. Defaults and safe values depend on the PostgreSQL release,
memory concurrency, storage, workload, and failover design. Benchmark changes
with a rollback plan and observe tail latency, WAL, checkpoints, and vacuum.

```ini
# Inspect before changing
SHOW shared_buffers;
SHOW work_mem;                 # budget per sort/hash operation, not per server
SHOW max_connections;
SHOW max_wal_size;
SHOW checkpoint_completion_target;
SHOW random_page_cost;
SHOW effective_io_concurrency;
SHOW autovacuum;

# Pair configuration review with pg_stat_database, pg_stat_bgwriter,
# pg_stat_wal, pg_stat_user_tables, pg_stat_statements, and OS metrics.
```

### Slow Query Investigation

```sql
-- 1. Enable slow query log
ALTER SYSTEM SET log_min_duration_statement = '500ms';
SELECT pg_reload_conf();

-- 2. pg_stat_statements (top queries by time)
SELECT calls, round(mean_exec_time::numeric, 2) as avg_ms, 
       round(total_exec_time::numeric / 1000, 2) as total_sec,
       query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- 3. Lock analysis
SELECT pg_class.relname, pg_locks.mode, pg_locks.granted,
       pg_stat_activity.query, pg_stat_activity.state
FROM pg_locks
JOIN pg_class ON pg_class.oid = pg_locks.relation
JOIN pg_stat_activity ON pg_stat_activity.pid = pg_locks.pid
WHERE NOT pg_locks.granted;

-- 4. Index usage stats
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Connection Management Best Practices

```
APPLICATION SIDE:
  • Use connection pool (HikariCP, PgBouncer, pgx pool)
  • Set pool size based on capacity calculation
  • Use parameterized statements for injection safety; evaluate prepared-plan behavior separately
  • Close connections properly
  • Implement health checks

DATABASE SIDE:
  • Set statement_timeout (e.g., 30s)
  • Set idle_in_transaction_session_timeout (kill stuck txns)
  • Set lock_timeout (fail fast on lock waits)
  • Use logical replication slots carefully
```

---

## 5.10 Database Sharding Strategies (Deep Dive)

### Vitess (MySQL Sharding)

```yaml
# Topology
products/: -80       # Range-based
  00: customer_id in (-9223372036854775808, 0)
  40: customer_id in (0, 167772160)
  80: customer_id in (167772160, 9223372036854775808)

users/-80:           # Hash-based
  keyspace_id: hash(user_id)

# Query routing
# vtgate analyzes query, routes to correct shard
# Cross-shard queries scatter-gather
```

### Citus (PostgreSQL Sharding)

```sql
-- Distribute table
SELECT create_distributed_table('events', 'user_id');
-- Choose: 'hash' or 'append' distribution

-- Reference table (replicated to all nodes)
SELECT create_reference_table('countries');

-- Co-locate tables for JOIN performance
SELECT create_distributed_table('orders', 'user_id');
SELECT create_distributed_table('order_items', 'user_id');
-- JOIN on user_id is now single-shard
```

### MongoDB Sharding

```javascript
// Enable sharding
sh.enableSharding("mydb")

// Shard collection with hashed key
sh.shardCollection("mydb.users", { _id: "hashed" })

// Shard with ranged key
sh.shardCollection("mydb.events", { timestamp: 1, user_id: 1 })

// Configure zones (geo-partitioning)
sh.addShardToZone("shard0000", "EU")
sh.addShardToZone("shard0001", "US")
sh.updateZoneKeyRange("mydb.users", 
  { region: "EU" }, { region: "EU" }, "EU")
```

---

## 5.11 Backup, Recovery & Disaster Recovery

### Backup Strategy (3-2-1 Rule)

```
3-2-1 BACKUP RULE:
  3 copies of data
  2 different media types
  1 off-site (different region/zone)

TYPES OF BACKUPS:
┌─────────────────────────────────────────────────────────────────┐
│  Logical (pg_dump, mysqldump)                                   │
│    • SQL statements to recreate                                 │
│    • Portable, version-independent                              │
│    • Slow for large databases                                    │
│    • Good for: small DBs, migrations                            │
│                                                                 │
│  Physical (pg_basebackup, filesystem snapshot)                  │
│    • Raw binary copy                                             │
│    • Fast restore                                                 │
│    • Version-dependent                                           │
│    • Good for: large DBs, DR                                     │
│                                                                 │
│  Incremental (WAL archiving, xtrabackup)                        │
│    • Only changes since last backup                              │
│    • Very efficient                                              │
│    • Combined with base backup                                   │
│                                                                 │
│  Continuous (PITR, log shipping)                                │
│    • Every change captured                                       │
│    • Restore to any point in time                                │
│    • Most comprehensive, more storage                            │
└─────────────────────────────────────────────────────────────────┘
```

### Recovery Objectives

```
RTO (Recovery Time Objective) — How fast must service restore?
RPO (Recovery Point Objective) — How much data can be lost?

Examples:
  Tier 1 (critical): RTO 1 min, RPO 0 (sync replicas)
  Tier 2 (important): RTO 1 hr, RPO 5 min
  Tier 3 (standard): RTO 4 hr, RPO 1 hr
  Tier 4 (archive): RTO 24 hr, RPO 24 hr

DR Strategies:
  Backup & Restore: usually slower; determined by restore tests and backup cadence
  Pilot Light: core data/services ready, but scale-up and validation take time
  Warm Standby: reduced-capacity stack; failover includes routing and correctness checks
  Hot Standby: near-full capacity; replication and failover can still lose availability
  Multi-Region Active-Active: reduces some failover work but adds conflict,
                              partition, dependency, and correlated-failure risks
```

### Backup Verification

```bash
# 1. Regular restore tests (DON'T skip!)
pg_restore -d test_db /backups/prod_backup.dump

# 2. Checksum verification (create at backup time, verify before restore)
sha256sum -c /backups/prod_backup.sha256

# 3. Point-in-time recovery test
# Restore base backup + replay WAL to specific time
restore_command = 'cp /wal_archive/%f %p'
recovery_target_time = '2026-08-30 14:30:00 UTC'

# 4. Monitor backup success in production
# Alert on missing/failed backups
```

---

## 5.12 Database Anti-Patterns

### Common Mistakes to Avoid

```
┌─────────────────────────────────────────────────────────────────┐
│  DATABASE ANTI-PATTERNS                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✗  SELECT * in application code                                │
│     → Specify needed columns explicitly                         │
│                                                                 │
│  ✗  No indexes (full table scans)                               │
│     → Index based on actual query patterns                      │
│                                                                 │
│  ✗  Indexes on low-cardinality columns (boolean, status)         │
│     → Use partial indexes for hot values                        │
│                                                                 │
│  ✗  N+1 query problem                                           │
│     → Eager load, JOIN, or DataLoader                           │
│                                                                 │
│  ✗  Long-running transactions                                   │
│     → Batch updates, use savepoints                             │
│                                                                 │
│  ✗  SELECT inside loop (in app code)                            │
│     → Bulk fetch, then iterate in memory                        │
│                                                                 │
│  ✗  ORM misuse (lazy loading in loops)                          │
│     → Eager loading, joins, batch fetch                         │
│                                                                 │
│  ✗  Missing ownership of referential integrity                  │
│     → Prefer constraints; document and test deliberate exceptions│
│                                                                 │
│  ✗  Aggregates without a rebuild or reconciliation path         │
│     → Retain a suitable source or define another recovery source│
│                                                                 │
│  ✗  No monitoring or alerting                                   │
│     → Track QPS, latency, connections, locks                    │
│                                                                 │
│  ✗  Connection pool exhaustion                                  │
│     → Pool sizing, timeouts, leak detection                     │
│                                                                 │
│  ✗  No backup verification                                      │
│     → Test restores regularly                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5.13 Choosing the Right Database — Decision Trees

### Decision Tree 1: OLTP Application

```
START: OLTP, structured data, ACID needed?
├─ YES → Single-node needs?
│   ├─ YES → PostgreSQL / MySQL ✓
│   └─ NO (massive scale, global) → Distributed SQL
│       ├─ PostgreSQL compatible → CockroachDB / YugabyteDB
│       ├─ MySQL compatible → TiDB / Vitess
│       └─ Custom → Spanner (Google), FoundationDB
│
└─ NO → Flexible schema?
    ├─ YES → Document store
    │   ├─ MongoDB, DocumentDB
    │   └─ Firestore (serverless)
    │
    └─ NO → Massive write scale, simple reads?
        ├─ YES → Wide-column (Cassandra, ScyllaDB)
        └─ NO → Specialized
            ├─ Search → Elasticsearch
            ├─ Graph → Neo4j
            ├─ Time-series → TimescaleDB / InfluxDB
            └─ Cache/session → Redis
```

### Decision Tree 2: Analytics (OLAP)

```
START: Analytics workload?
├─ YES → Real-time (sub-second)?
│   ├─ YES → ClickHouse, Apache Druid, Apache Pinot
│   └─ NO → Batch processing?
│       ├─ YES → Snowflake, BigQuery, Redshift, Databricks
│       └─ NO → Hybrid (HTAP)?
│           ├─ TiDB (HTAP)
│           └─ SingleStore
│
└─ NO → Use OLTP database
```

---

## 5.14 Exercises

### Exercise 1 — Foundation: Database Selection
For each workload, choose the database and justify:
- Banking transactions (strict ACID, regulatory)
- IoT sensor data (10M devices, high write rate)
- Social network feed (1B users, eventually consistent)
- Product catalog search (full-text, faceted)
- Real-time analytics dashboard (10K events/sec)
- Shopping cart (high concurrency, low latency)

### Exercise 2 — Applied: Schema Design
Design schema for:
- Multi-tenant SaaS (1000 tenants, 10M users total)
- E-commerce with orders, products, inventory
- Time-series IoT with downsampling needs

Include indexes, partitioning strategy, and access patterns.

### Exercise 3 — Advanced: Migration Plan
Plan migration from:
- Single PostgreSQL (10TB, 5K QPS) to CockroachDB
- MySQL with read replicas to Vitess sharded

Include: phase plan, risk analysis, rollback strategy, data verification.

### Exercise 4 — Applied: Performance Investigation
A PostgreSQL query takes 30 seconds:
```sql
SELECT u.email, COUNT(o.id) as order_count
FROM users u LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2020-01-01'
GROUP BY u.id
ORDER BY order_count DESC
LIMIT 100;
```
- Identify potential issues
- Suggest indexes
- Rewrite if needed
- Estimate performance improvement

### Exercise 5 — Advanced: DR Design
For a financial application:
- RTO: 5 minutes
- RPO: 0 (no data loss)
- Multi-region

Design the DR architecture with:
- Replication topology
- Failover mechanism
- Network connectivity
- Testing strategy

---

## 5.15 Further Reading

### Books
- *SQL Antipatterns* — Bill Karwin (must-read)
- *Database Internals* — Alex Petrov
- *Designing Data-Intensive Applications* — Kleppmann (Ch. 5, 7, 9)
- *PostgreSQL: Up and Running* — Regina Obe & Leo Hsu
- *High Performance MySQL* — Baron Schwartz et al.

### Documentation
- [PostgreSQL Official Docs](https://www.postgresql.org/docs/) — Excellent, thorough
- [MongoDB Manual](https://docs.mongodb.com/manual/)
- [Cassandra Documentation](https://cassandra.apache.org/doc/)
- [Redis Documentation](https://redis.io/documentation)
- [Elasticsearch Guide](https://www.elastic.co/guide/)

### Papers
- [The End of an Architectural Era (H-Store/VoltDB)](http://voltdb.com/_pdf/elsevier-paper.pdf)
- [OLTP Through the Looking Glass](https://arxiv.org/abs/1804.00626)
- [DynamoDB's Design](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)
- [Spanner](https://static.googleusercontent.com/media/research.google.com/en//archive/spanner-osdi2012.pdf)
- [TAO: Facebook's Distributed Data Store](https://www.usenix.org/system/files/conference/atc13/atc13-bronson.pdf)

### Online Resources
- [Use The Index, Luke!](https://use-the-index-luke.com/) — SQL indexing guide
- [PGTune](https://pgtune.leopard.in.ua/) — PostgreSQL config wizard
- [Explain Extended](http://explainextended.com/) — Advanced SQL

---

## 5.16 Summary Checklist

- [ ] Can build and validate a database shortlist from workload requirements
- [ ] Understand ACID properties deeply
- [ ] Can design normalized (3NF) schemas
- [ ] Know when to denormalize and how
- [ ] Can create effective indexes (B-tree, GIN, partial)
- [ ] Can use EXPLAIN to optimize queries
- [ ] Understand CAP trade-offs across database types
- [ ] Can implement sync vs async replication
- [ ] Can plan backward-compatible migrations and quantify lock/backfill risk
- [ ] Can design backup and DR strategy
- [ ] Understand connection pooling and management
- [ ] Can validate online migration, rollback, and reconciliation procedures

---

> **Next Chapter**: [Chapter 6: Caching Strategies](../chapters/06-caching-strategies.md) — Make data fast and fresh.
