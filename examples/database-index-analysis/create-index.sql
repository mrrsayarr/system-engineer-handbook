CREATE INDEX CONCURRENTLY IF NOT EXISTS orders_pending_lookup_idx
  ON orders (tenant_id, created_at DESC)
  INCLUDE (id, total_cents)
  WHERE status = 'pending';

ANALYZE orders;
