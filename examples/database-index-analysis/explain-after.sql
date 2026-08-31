EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT id, tenant_id, total_cents
FROM orders
WHERE tenant_id = 42
  AND status = 'pending'
  AND created_at >= now() - interval '30 days'
ORDER BY created_at DESC
LIMIT 100;

SELECT pg_size_pretty(pg_relation_size('orders_pending_lookup_idx')) AS index_size;
