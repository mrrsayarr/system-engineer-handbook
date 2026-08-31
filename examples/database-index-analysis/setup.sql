DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
  id BIGSERIAL PRIMARY KEY,
  tenant_id BIGINT NOT NULL,
  status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  total_cents INTEGER NOT NULL CHECK (total_cents >= 0)
);

INSERT INTO orders (tenant_id, status, created_at, total_cents)
SELECT (g % 1000) + 1,
       CASE WHEN g % 20 = 0 THEN 'pending' ELSE 'completed' END,
       now() - ((g % 365) || ' days')::interval,
       100 + (g % 10000)
FROM generate_series(1, 200000) AS g;

ANALYZE orders;
