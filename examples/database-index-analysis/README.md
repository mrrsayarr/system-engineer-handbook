# Database and Index Analysis

This lab demonstrates a safe PostgreSQL workflow: capture a baseline plan,
create a justified index concurrently, compare buffers and timing, then decide
whether the write/storage cost is worth it. It uses only synthetic data.

## Run

```bash
createdb system_engineer_lab
psql system_engineer_lab -f setup.sql
psql system_engineer_lab -f explain-before.sql
psql system_engineer_lab -f create-index.sql
psql system_engineer_lab -f explain-after.sql
```

`EXPLAIN (ANALYZE, BUFFERS)` executes the query, so use representative but safe
data and a bounded query. `CREATE INDEX CONCURRENTLY` avoids the strongest table
write lock but takes longer and cannot run inside a transaction block.

## Review checklist

- Compare planning time, execution time, shared hit/read blocks, rows removed,
  and plan shape; do not accept an index because the plan merely “looks nicer”.
- Confirm the predicate is selective at production cardinality and statistics
  are current (`ANALYZE`).
- Measure insert/update overhead, index size, vacuum behavior, and replica lag.
- Remove an experimental index only after checking dependent plans and a rollback
  window; never drop an index blindly during an incident.
