# Chapter 8: Load Balancing & Traffic Management

> **Estimated Time:** 4–6 hours | **Prerequisites:** Chapters 1–7<br>
> **Last reviewed:** 2026-08-31 | **Level:** Foundation → applied → production judgment

---

## Learning Objectives

By the end of this chapter, you will be able to:

1. **Distinguish L4 vs L7 load balancing** and choose correctly
2. **Select the right algorithm** (round robin, least connections, consistent hashing, weighted)
3. **Design health checks** that prevent cascading failures
4. **Configure reverse proxies** (NGINX, HAProxy, Envoy, Traefik)
5. **Implement global load balancing** using DNS, Anycast, and geolocation
6. **Route traffic safely** with canary, blue-green, and shadow patterns
7. **Detect and mitigate** common misconfigurations before they become incidents

---

## 8.1 Why Load Balancing

### The problem load balancing solves

```text
Single server problems:
  - single point of failure
  - cannot use resources beyond one host
  - deployment requires downtime
  - locality of adverse load spikes

Load balancer goals:
  - distribute traffic across healthy instances
  - contain some backend failures when enough healthy capacity remains
  - support disruption-minimized deployments with readiness and draining
  - support session affinity where needed
  - terminate TLS at the edge
```

### Traffic flow without and with load balancing

```text
CLOUD / EDGE

Without LB:
  clients ---> backend (single host)

With LB:
  clients ---> load balancer ---> backend pool
                                        ├─ host-a
                                        ├─ host-b
                                        └─ host-c
```

```text
PLACEMENT OPTIONS:

  L7 inside VPC:
    - hosts and LB share subnets
    - cost: internal traffic only
    - complexity: low
    - visibility: full payload inspection possible

  L4 near clients:
    - LB sits closer to clients
    - cost: hairpin traffic or cross-AZ
    - complexity: higher
    - visibility: limited to transports
```

---

## 8.2 OSI Layer Perspective

### Layer 4 vs Layer 7

```text
LAYER 4 (TCP/UDP):
  - inspects only IP and port
  - fast, simple forwarding
  - no payload awareness
  - good for TCP passthrough or UDP
  - examples: AWS NLB, GCP TCP/UDP LB, HAProxy TCP mode

LAYER 7 (HTTP/gRPC):
  - inspects headers and body
  - can route by host, path, method, header
  - can rewrite, retry, buffer, transform
  - can enforce auth, rate limits, WAF
  - examples: AWS ALB/API Gateway, GCP HTTP(S) LB, NGINX, Envoy, HAProxy HTTP mode

CHOOSING:
  Use L4 when:
    - protocol is not HTTP
    - maximum throughput and minimum latency matter
    - protocol is TCP and TLS termination is handled by backend

  Use L7 when:
    - path-based routing is required
    - header or cookie aware routing is needed
    - mutual TLS, mTLS, or advanced auth are required
    - fine-grained rate limiting and WAF should be enforced centrally
```

---

## 8.3 Algorithms

### Common algorithms

```text
ROUND ROBIN:
  - each request goes to the next backend in sequence
  - simple, predictable
  - treats all backends as equals
  - ignore weights and current load

WEIGHTED ROUND ROBIN:
  - round robin with configurable weights
  - useful when hosts differ in capacity
  - still naive about instant load

LEAST CONNECTIONS:
  - route to backend with the fewest active connections
  - better for long-lived sessions
  - best for mixed request durations

WEIGHTED LEAST CONNECTIONS:
  - least connections adjusted by weight
  - balances capacity and current load

LEAST RESPONSE TIME:
  - combine active connections and recent latency
  - slow hosts receive less traffic

IP HASH:
  - hash client IP modulo backend count
  - yields sticky behavior without cookies
  - breaks when scaling pool size
  - NAT and proxies reduce effectiveness

CONSISTENT HASHING:
  - hash client or key into ring
  - add or remove backend with minimal remap
  - suitable for stateful caches and distributed storage

RANDOM:
  - probabilistic but often good enough at scale
  - simple and resistant to synchronized load spikes
```

### Algorithm quick reference

```text
SCENARIO                           RECOMMENDED ALGORITHM
stateless APIs with short requests     round robin or weighted least connections
long-lived TCP connections             least connections
stateful cache or session affinity     consistent hashing or IP hash
heterogeneous host capacities          weighted round robin or weighted least connections
mixed latency characteristics          least response time
```

---

## 8.4 Health Checks

### Active vs passive health checks

```text
ACTIVE HEALTH CHECKS:
  load balancer probes backends on schedule
  HTTP, HTTPS, TCP, TLS handshake, gRPC health
  possible observations: expected status, timeout, refused or reset connection
  failure threshold -> mark unhealthy -> stop sending traffic
  recovery threshold -> mark healthy -> resume traffic

PASSIVE HEALTH CHECKS:
  observe real client traffic for errors
  connection failures, timeouts, 5xx responses
  retries and circuit breaking feed into backend scoring
  reduces artificial probe load
```

### HTTP health check example

```text
PATH:        /healthz or /ready
METHOD:      GET
SUCCESS:     200 OK
FAILURE:     non-2xx, timeout, connection refused
INTERVAL:    derive from detection-time objective and probe cost
TIMEOUT:     below interval and based on healthy latency distribution
HEALTHY FOR: consecutive successes or a recovery window
UNHEALTHY:   failures sufficient to avoid flapping but meet detection objective
```

### Readiness vs liveness

```text
READINESS:
  - is the instance able to serve traffic?
  - include only dependencies required to serve this traffic class
  - failing readiness stops new traffic but does not kill pod

LIVENESS:
  - is the process healthy?
  - failing liveness may restart container
  - must be tolerant to temporary load

WRONG USE:
  using liveness probe for dependency failures -> restart loop
  using readiness probe for process health -> stuck behind LB
```

---

## 8.5 Session Persistence

### Sticky sessions

```text
USE STICKY SESSIONS WHEN:
  - server-side session state is expensive to replicate
  - session state lives in memory and is not shared
  - protocol needs connection-level affinity

AVOID STICKY SESSIONS WHEN:
  - horizontal scaling is a goal
  - session state can be externalized
  - scaling events cause session pinning to draining hosts
```

```text
COOKIE-BASED PERSISTENCE:
  LB inserts cookie on response
  next request carries cookie
  simple, works behind proxies

SOURCE IP AFFINITY:
  hash source IP to backend
  fails with carrier NAT and mobile networks

APPLICATION-COOKIE INSERTION:
  application sets dedicated cookie for routing
  application controls removal and lifecycle
```

---

## 8.6 Reverse Proxies

### NGINX

```nginx
http {
    upstream api {
        least_conn;
        server app1:8080 weight=3;
        server app2:8080;
        server app3:8080 backup;
        keepalive 32;
    }

    server {
        listen 80;
        server_name api.example.com;

        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            proxy_connect_timeout 3s;
            proxy_send_timeout 10s;
            proxy_read_timeout 10s;

            proxy_next_upstream error timeout invalid_header http_500;
            proxy_next_upstream_tries 2;
        }
    }
}
```

### HAProxy

```haproxy
frontend fe_http
    bind *:80
    bind *:443 ssl crt /etc/haproxy/cert.pem alpn h2,http/1.1
    acl is_api path_beg /api
    use_backend api if is_api
    default_backend web

backend api
    balance leastconn
    option httpchk GET /healthz
    http-check expect status 200
    server api1 10.0.0.1:8080 check weight 3 inter 3s fall 2 rise 2
    server api2 10.0.0.2:8080 check inter 3s fall 2 rise 2
    timeout connect 3s
    timeout server 30s
    retries 2
```

### Envoy

```yaml
static_resources:
  listeners:
    - name: listener_0
      address:
        socket_address: { address: 0.0.0.0, port_value: 8080 }
      filter_chains:
        - filters:
            - name: envoy.filters.network.http_connection_manager
              typed_config:
                "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
                stat_prefix: ingress_http
                route_config:
                  name: local_route
                  virtual_hosts:
                    - name: backend
                      domains: ["*"]
                      routes:
                        - match: { prefix: "/api" }
                          route:
                            cluster: api_cluster
                            timeout: 5s
                            retry_policy:
                              retry_back_off:
                                base_interval: 0.1s
                                max_interval: 1s
                              num_retries: 3
                http_filters:
                  - name: envoy.filters.http.router
  clusters:
    - name: api_cluster
      connect_timeout: 0.5s
      type: STRICT_DNS
      lb_policy: LEAST_REQUEST
      load_assignment:
        cluster_name: api_cluster
        endpoints:
          - lb_endpoints:
              - endpoint:
                  address:
                    socket_address: { address: app1, port_value: 8080 }
```

### Traefik

```yaml
api:
  dashboard: true

entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
  file:
    filename: dynamic.yml

http:
  routers:
    api:
      rule: "Host(`api.example.com`)"
      entryPoints: [websecure]
      service: api
      tls:
        certResolver: myresolver

  services:
    api:
      loadBalancer:
        servers:
          - url: "http://app1:8080"
          - url: "http://app2:8080"
        healthCheck:
          path: /healthz
          interval: 10s
          timeout: 3s
```

---

## 8.7 Kubernetes Load Balancing

### Service types

```text
ClusterIP:
  internal service IP within cluster
  no external access by default
  use for internal service mesh

NodePort:
  expose on every node at static port 30000-32767
  suitable for small clusters and testing
  not for production internet-facing services

LoadBalancer:
  provisions external LB through cloud controller
  integrates with cloud vendor load balancer
  most common production choice

ExternalName:
  maps service to DNS name via CNAME
  no ports or pods
  use for legacy integration and external DNS aliases
```

### Ingress vs Gateway API

```text
INGRESS:
  Kubernetes resource for L7 routing
  annotation driven, vendor APIs differ
  limited to L7, no TCP/UDP
  deprecated concepts replaced by Gateway API

GATEWAY API:
  newer, role-oriented API
  GatewayClass, Gateway, HTTPRoute, TCPRoute, TLSRoute
  vendor-neutral yet extensible
  supports split traffic, weighted routing, header-based routing

WHEN TO USE WHAT:
  existing clusters widely supporting Ingress -> continue when stable
  new clusters initially standardized -> prefer Gateway API
  need TCP/UDP, TLS passthrough, advanced routing -> Gateway API
```

---

## 8.8 Global Load Balancing

### DNS-based routing

```text
GEO-DNS:
  resolve based on client resolver IP or Anycast ingress location
  route to nearest DC or PoP
  examples: Route 53 geolocation, Cloudflare Load Balancing

LATENCY-BASED ROUTING:
  measure round-trip times from probes to regions
  route to fastest region dynamically
  examples: Route 53 latency routing, GCP global load balancer

WEIGHTED ROUTING:
  distribute by policy weights
  use for canary and blue-green at global scale
  examples: Route 53 weighted, Cloudflare weighted
```

### Anycast

```text
Anycast announces the same prefix from multiple locations.
BGP routes clients to nearest or best path automatically.

Use cases:
  - DNS (Google 8.8.8.8, Cloudflare 1.1.1.1)
  - CDN PoPs
  - DDoS scrubbing centers
  - hybrid global API endpoints

Benefits:
  - automatic failover and load distribution
  - resilience to link and node failures
  - low latency by proximity

Considerations:
  - stateful services need careful session handling
  - routing policy must align with backend topology
  - BGP hijacking risk requires RPKI and prefix filtering
```

---

## 8.9 Traffic Management Patterns

### Rate limiting

```text
GOALS:
  - protect services from abuse
  - enforce quotas and tiers
  - prevent cascading overload

TYPES:
  - per client or per identity
  - per IP or per authenticated user
  - per route or per API method
  - global vs distributed

IMPLEMENTATION:
  - NGINX limit_req_zone
  - Envoy rate limit filter
  - API gateway rate limiters
  - application or middleware envelope
```

### WAF and edge policy

```text
WAF:
  - inspect HTTP payload for SQL injection, XSS, path traversal
  - managed rulesets (OWASP Top 10) and custom rules
  - block, challenge, or log only

EDGE POLICIES:
  - CORS policy at ingress
  - bot management
  - IP allowlisting and geo-blocking
  - request size limits
```

### Retry, timeout, and circuit breaker

```text
These belong near clients and gateway, not only in application code.

RETRY:
  - retry idempotent operations only
  - exponential backoff with jitter
  - avoid retry storms

TIMEOUT:
  - deadlines must be shorter than the caller's remaining budget
  - overly short timeouts create retries and false failures; measure distributions

CIRCUIT BREAKER:
  - fail fast when backend is unhealthy
  - half-open probe to recover
  - per route or per backend
```

---

## 8.10 High Availability and Failover

### Redundancy patterns

```text
ACTIVE-PASSIVE:
  - primary handles traffic, standby waits
  - failover requires state migration or promotion
  - better for databases and stateful services
  - measured RTO includes detection, decision, promotion, routing, and validation

ACTIVE-ACTIVE:
  - multiple backends receive traffic simultaneously
  - failover is mostly automatic
  - requires stateless or synchronized state
  - routing may be fast, but state/dependency recovery still determines RTO

MULTI-AZ:
  - replicate across zones in a region
  - LB spans AZs and avoids failed zones
   - common when the service and all critical dependencies tolerate zone failure

MULTI-REGION:
  - global load balancing across regions
  - async or sync replication for data
  - fallback regions for major outages
```

### Graceful shutdown and connection draining

```text
INSTANCE SHUTDOWN:
  - stop accepting new connections
  - finish in-flight requests up to deadline
  - deregister from LB before termination
  - heartbeat cancellation and readiness probe failure

LB BEHAVIOR:
  - respect connection drain timeout
  - stop forwarding after expiry
  - TCP FIN/RST to backends initiates close
```

---

## 8.11 Observability for Traffic Management

### Key signals

```text
REQUEST METRICS:
  request rate by route, status, host
  latency histograms p50/p95/p99/p999
  error rate and status classification
  upstream response sizes

CONNECTION METRICS:
  active and idle connections per backend
  connection establishment and teardown rate
  TLS handshake latency
  keepalive efficiency

HEALTH METRICS:
  backend healthy versus unhealthy count
  health check success rate
  time since last successful check
  LB internal error rate
```

### Logging and tracing

```text
ACCESS LOG FORMAT:
  timestamp remote_addr request_method request_uri
  status response_time bytes_sent upstream_status
  upstream_response_time tls_version

TRACES:
  propagate traceparent across backends
  track L7 LB latency separately from upstream latency
  record LB route and backend host in span attribute
```

---

## 8.12 Common Pitfalls

```text
MISCONFIGURATIONS TO AVOID:

1. Health checks too lenient
   marking unhealthy backends as healthy
   leading to cascading 5xx

2. Health checks too strict
   transient blips cause backend removal
   loss of capacity under load

3. Missing timeouts
   slow clients pin backends indefinitely
   thread or coroutine pool exhaustion

4. Session pinning during scale events
   sticky sessions pinned to drained pods
   user experience degraded during deployment

5. L7 LB for non-HTTP protocol
   excessive latency and protocol violations
   consider L4 passthrough instead

6. No retry budget or backoff
   retry amplification under failure
   load increases instead of absorbing it

7. Ignoring backend cold start
   new backends receive traffic without warm caches
   spikes in p99 latency after scale-out

8. Inadequate probe coverage
   failing to exercise the real dependency path
   probes pass while production traffic fails

9. Trust based only on network location
   edge TLS does not authenticate every internal workload
   choose workload identity, authorization, segmentation, and encryption from the threat model
```

---

## 8.13 Exercises

### Exercise 1 — Foundation: Algorithm Selection

A platform has 12 app servers behind a load balancer. Requests are 50ms on average, but some take up to 4 seconds. The team wants to add 6 servers. Choose the most suitable load balancing algorithm and justify your choice.

### Exercise 2 — Applied: Health Checks

Design a health check strategy for a service depending on PostgreSQL and Redis. Include success criterion, interval, timeout, thresholds, and probe isolation.

### Exercise 3 — Advanced: Global Routing

You operate API in three regions: US, EU, and APAC. Database is active in US and read-only in others. Design a global route strategy that routes write traffic to US and read traffic regionally while supporting failover.

### Exercise 4 — Applied: Performance Investigation

A release causes endpoint latency to increase from 120ms to 800ms after scaling. List likely causes and a structured debug process from the LB outward.

### Exercise 5 — Advanced: Proxy Design

Design a reverse proxy configuration for:
- HTTP to HTTPS redirect
- path-based routing to three services
- rate limiting per client
- WAF rules for OWASP Top 10
- health checks and graceful draining
- observability with access logs and metrics

---

## 8.14 Further Reading

- *The Art of Capacity Planning* — John Allspaw
- *Site Reliability Engineering* — Google (chapter on load balancing and hardware)
- NGINX, HAProxy, Envoy, and Traefik official documentation
- Cloud provider documentation on global load balancing
- *The Tail at Scale* — Dean and Barroso

---

## 8.15 Summary Checklist

- [ ] can explain when to prefer L4 vs L7
- [ ] can choose an algorithm for given traffic patterns
- [ ] can design active and passive health checks
- [ ] can configure NGINX, HAProxy, Envoy, or Traefik
- [ ] can explain session persistence trade-offs
- [ ] can design global routing with DNS, Anycast, and geolocation
- [ ] can design safe canary and rollback procedures
- [ ] can identify common load balancing failure modes
- [ ] can collect logs and metrics that explain traffic behavior

---

> Next: [Chapter 9: Monitoring, Observability & Alerting](./09-monitoring-observability-alerting.md)
