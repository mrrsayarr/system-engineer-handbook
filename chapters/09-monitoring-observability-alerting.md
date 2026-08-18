# Chapter 9: Monitoring, Observability & Alerting

> **Estimated Time: 3-4 hours** | **Prerequisites: Chapters 1-8**

---

## Learning Objectives

By the end of this chapter, you will be able to:

1. **Distinguish monitoring from observability** and justify both
2. **Instrument HTTP and RPC services** with OpenTelemetry
3. **Design metrics, logs, and traces** as addressable, queryable artifacts
4. **Define SLIs, SLOs, alerting policies**, and error budgets
5. **Build dashboards and runbooks** that serve on-call engineers
6. **Reduce alert fatigue** through routing, severity, and automation
7. **Conduct blameless postmortems** using structured incident analysis

---

## 9.1 Monitoring vs Observability

| Area | Monitoring (known unknowns) | Observability (unknown unknowns) |
|------|-----------------------------|----------------------------------|
| Focus | Specific systems, known failure modes | Whole system, unknown interactions |
| Data model | Predefined panels and fixed thresholds | High-cardinality streams and ad-hoc queries |
| Questions answered | Is it up? Are 5xx increasing? | Why did latency increase globally? |
| Tool shape | Dashboards, static checks | Search, explore, trace |

Monitoring tells you the system is unhealthy. Observability tells you why it is unhealthy without shipping new code.

The two complement each other. Monitoring alerts on known contract violations. Observability adds the internal view needed for novel failure modes and cross-service interactions.

---

## 9.2 Signals: Metrics, Logs, and Traces

```text
METRICS:
  numerical measurements over time
  counters, gauges, histograms, summaries
  aggregation friendly, low cardinality best practice
  examples: http_request_duration_seconds, queue_depth

LOGS:
  discrete events with context
  structured logs with severity and fields
  expensive at very high volume
  examples: structured access logs, business events

TRACES:
  causal chain across services
  span ids, parent ids, attributes and events
  high cardinality tolerated within trace backends
  examples: request trace across API, auth, db
```

### How the three interact

```text
User reports slow search:
  metric -> latency p99 increased after deploy
  logs  -> downstream timeout on recommendations
  trace -> shows recommendation service waiting 2s on cache

Without all three:
  metric only -> suspected deploy, hard to confirm cause
  logs only   -> noisy, no aggregation across instances
  traces only -> heavy, easy to lose in volume, expensive forever
```

---

## 9.3 Instrumentation

### OpenTelemetry concepts

```text
TRACES:
  trace        -> end-to-end request
  span         -> single operation within a trace
  context      -> propagated with traceparent, baggage

METRICS:
  instrumented libraries emit instrument
  views shape aggregation at collection time
  exporters send to prometheus, OTLP, or vendor

LOGS:
  log record enriched with trace and span ids
  correlation is the main value
```

### HTTP instrumentation example

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

trace.set_tracer_provider(TracerProvider())
tracer_provider = trace.get_tracer_provider()
tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="otel-collector:4317")))

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()
```

### Database instrumentation

```python
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

engine = create_engine(DATABASE_URL)
SQLAlchemyInstrumentor().instrument(engine=engine, enable_commenter=True)
```

Instrument every layer: HTTP client, HTTP server, database, messaging client, messaging server.

---

## 9.4 Metrics Design

### The four golden signals

```text
LATENCY:
  distribution of request duration
  success and failure separated
  prefer histograms over averages

TRAFFIC:
  demand on the service
  requests per second or bytes transferred

ERRORS:
  rate of failed requests
  HTTP 5xx, gRPC UNAVAILABLE, application exceptions
  not operational dilutions, not deprecations by themselves

SATURATION:
  capacity headroom
  memory, CPU, connections, queue depth
  saturation is the leading indicator before latency rises
```

### RED method and USE method

```text
RED (service-centric):
  Rate      - requests per second
  Errors    - failed requests
  Duration  - latency distribution

USE (resource-centric):
  Utilization - percent time busy
  Saturation  - queue length or waiting tasks
  Errors      - error count of resource
```

### Instrument naming and labels

```text
NAMING:
  prefix with domain: http_, db_, cache_
  use unit suffix: _seconds, _bytes, _total
  avoid verbs: do not use update_orders, prefer orders_updated_total

LABELS:
  keep low cardinality
  status, method, route, host
  avoid user id, request id, correlation id
  if needed, record as exemplars or trace attributes

BAD EXAMPLES:
  request_duration_seconds{user_id="123"}
  error_count{order_id="abc"}

GOOD EXAMPLES:
  http_request_duration_seconds{method="POST", route="/api/orders", status="201"}
  orders_created_total{payment_method="card"}
```

---

## 9.5 Structured Logging

### Schema design

```text
REQUIRED fields on every log record:
  timestamp  -> ISO8601 UTC
  severity  -> trace, debug, info, warn, error, fatal
  service   -> logical service name
  host      -> hostname or pod name
  message   -> human readable summary
  trace_id  -> correlation id when available
  span_id   -> span id when available

RECOMMENDED fields:
  environment -> prod, staging, dev
  version     -> semantic version of service
  region      -> deployment region
  labels      -> key value pairs for routing and indexing
  duration_ms -> numeric duration when applicable
  error_type  -> exception type or domain error code
```

### JSON log line example

```json
{
  "timestamp": "2024-01-15T08:24:31.123Z",
  "severity": "error",
  "service": "payment-service",
  "host": "payment-7d9bc4f9-abc12",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "message": "payment processing failed",
  "error_type": "InsufficientFundsError",
  "order_id": "ord_123456",
  "amount_cents": 2500,
  "currency": "USD",
  "duration_ms": 312,
  "environment": "prod",
  "region": "eu-west-1",
  "version": "1.4.2"
}
```

### Logging anti-patterns

```text
Avoid:
  - empty message fields requiring correlation first
  - concatenating strings with sensitive data
  - logging full request bodies with PII
  - dynamic keys that blow up index cardinality
  - using print or printf in production services
  - log levels that are never honored downstream
```

---

## 9.6 Distributed Tracing

### Trace data model

```text
TRACE:
  unique identifier across services
  root span starts at ingress
  child spans follow call graph
  ended spans have start and end time

SPAN:
  operation name
  start and end time
  status: unset, ok, error
  attributes: key value pairs
  events: timed annotations
  links: causal references to other spans
```

### Trace propagation

```text
W3C trace context:
  traceparent: 00-{trace-id}-{span-id}-{flags}
  tracestate: vendor-specific state

Baggage:
  user_id, tenant_id, region
  propagates through the call chain
  expensive; do not abuse cardinality
```

### Sampling

```text
HEAD-BASED:
  sample 1 of N at the root
  cheap at scale
  may miss rare failures

TAIL-BASED:
  collect all spans, keep only interesting ones
  better debugging
  requires storage and CPU

PROBABILISTIC:
  decide per span whether to record

RULE-BASED:
  sample errors, long latency, important routes
  combine with head-based or tail-based
```

---

## 9.7 Dashboards and Runbooks

### Audience-specific dashboards

```text
EXECUTIVE:
  - SLO health overall, open incidents count, customer impact trend
  - minimal complexity, high signal

OPERATIONS:
  - service health, latency, error rate, saturation
  - dependency health and upstream status
  - deployment timeline overlay

ENGINEERING:
  - detailed request latencies and error breakdown
  - resource utilization per service
  - dependency graph and recent changes

BUSINESS:
  - order rate, cart abandonment, signup completion
  - monetary impact per percent latency increase
  - conversion correlated with system health
```

### Effective dashboard rules

```text
ONE METRIC PER GRAPH:
  avoid stacked line charts of unrelated series
  separate graphs keep axes meaningful

MINIMIZE ALERT THRESHOLD OVERLAY:
  thresholds belong in alerts, not permanent noise on graphs
  use reference lines sparingly

SHOW ROLLUPS AND ZOOM:
  start with 1h, 6h, 24h, 7d
  allow click-through to instance-level detail

DASHBOARD ANNOTATIONS:
  mark deployments, incidents, config changes
  makes timeline interpretation possible during an incident
```

---

## 9.8 SLOs, SLIs, and Error Budgets

### Definitions

```text
SLI: Service Level Indicator -> measurable aspect of service
  examples: request success ratio, p99 latency

SLO: Service Level Objective -> target value for an SLI
  target: 99.9% success over 30 days
  target: p99 latency < 200ms over 7 days

SLA: Service Level Agreement -> business or contractual promise
  if SLO is exceeded, customer may receive credit or penalties
```

### Error budget

```text
ERROR BUDGET FORMULA:
  budget = 1 - objective
  example: 99.9% over 30 days = 43.2 minutes allowable downtime

BURN RATE:
  how fast budget is consumed
  high burn rate -> freeze risky changes
  moderate burn rate -> proceed with caution
  low or negative burn rate -> safe to ship

POLICY:
  - budget used for releases, experiments, and infrastructure changes
  - freeze changes when budget exhausted
  - reduce blast radius when burn rate spikes
```

### SLI design patterns

```text
AVAILABILITY SLI:
  successful requests / total requests
  filter out infrastructure load balancer health checks
  define success by 2xx and selected 3xx only

LATENCY SLI:
  count of requests faster than threshold / total requests
  histogram bucket chosen from customer distribution
  usually p95 or p99 reflects user-impacting latency

FRESHNESS SLI:
  freshness = writes / stale reads over window
  use when cache or materialized view introduces staleness
```

---

## 9.9 Alerting and Paging

### Alert design principles

```text
ACTIONABLE:
  alert implies human action
  if no action exists, do not page

TIERED:
  page -> on-call engineer
  ticket -> engineering team backlog
  dashboard -> weekly review

RESPONSE-DRIVEN:
  define expected response before alert is created
  define resolution and automatic recovery
  include runbook link and command snippets
```

### Alert classification

```text
PAGE IMMEDIATELY:
  - customer facing degradation impacting many users
  - data loss signals or replication failures
  - saturation that will breach SLO within minutes
  - security related escalations

PAGE DURING BUSINESS HOURS:
  - non-critical degradation
  - capacity threshold crossed with lead time to react
  - data quality anomalies

TICKET:
  - trends
  - deprecation warnings
  - non-priority quota usage

NOISE TO SUPPRESS:
  - transient flapping from health checks
  - GC pauses during known backfills
  - scheduled maintenance windows
```

---

## 9.10 Incident Response

### Incident lifecycle

```text
DETECTION:
  automation, monitoring, user reports
  acknowledge alert and establish incident commander

TRIAGE:
  assess severity and blast radius
  isolate affected components
  decide if this is a restart, rollback, or mitigation

MITIGATION:
  restore service with smallest change possible
  prefer least irreversible action
  confirm user facing recovery

ROOT CAUSE ANALYSIS:
  determine why the failure occurred
  identify systemic, not superficial, cause
  document timeline, triggers, and decision points

REMEDIATION:
  long-term fix
  prevent recurrence through prevention, not punishment

COMMUNICATION:
  internal updates every 15 minutes
  external status page updates when customer facing
  stakeholder summary within 24 hours
```

### Blameless postmortem

```text
GOAL: understand systemic conditions

Avoid:
  blaming individuals
  listing people as cause
  stopping at symptom explanation

Include:
  timeline with precise times and actions
  triggering event and contributing factors
  detection and response timeline
  what went well versus what went wrong
  action items with owners and dates

TEMPLATE:
  - incident summary and duration
  - blast radius and customer impact
  - timeline
  - contributing factors
  - what went well
  - what went wrong
  - action items
```

---

## 9.11 Observability Platforms

### Stack comparison

```text
PROMETHEUS + GRAFANA:
  pull-based metrics
  service discovery friendly
  strong ecosystem and operator support
  no native distributed tracing
  used in Kubernetes widely

ELK / OPENSEARCH:
  centralized logs with search
  heavy index; suitable when search is primary need
  expensive at massive scale

JAEGER / ZIPKIN:
  distributed tracing
  requires sampling strategy and storage backend
  often paired with metrics and logs separately

LIGHTSTEP / HONEYCOMB / DATADOG:
  commercial full-stack observability
  lower operational burden
  higher cost and vendor lock-in

OTLP-BASED PIPELINE:
  vendor neutral instrumentation and export
  backends: Prometheus, Tempo, Loki, Jaeger, vendor
  preferred starting point for new systems
```

### Storage and retention

```text
METRICS:
  15s resolution -> 30 days hot
  5m resolution -> 12 months warm
  1h resolution -> long term

LOGS:
  hot -> 7 days
  warm -> 30 days
  cold -> 1 year with lower query SLA

TRACES:
  100% with sampling -> 7 days
  sampled traces -> 30 days
  avoid infinite retention without cost controls
```

---

## 9.12 Exercises

### Exercise 1

Select SLIs and SLOs for a checkout API serving 150,000 requests per minute. Include latency SLO, availability SLO, saturation SLI, and compute the resulting 30-day error budget. Define the alerting strategy aligned with this budget.

### Exercise 2

Design a structured logging schema for a payment service. Include required fields, sensitive data handling, correlation with traces, and a sample log line for successful payment and payment failure.

### Exercise 3

Instrument the following call chain with OpenTelemetry:
- client request arrives at API Gateway
- gateway validates JWT and calls User Service
- User Service queries PostgreSQL
- result is returned to gateway and to client

Include spans, attributes, events, and sampling strategy.

### Exercise 4

A service shows p99 latency increase from 180ms to 650ms after a new deployment. Draft an incident investigation flow using dashboards, logs, and traces.

### Exercise 5

Reduce alert fatigue by classifying five candidate alerts into page, business-hours ticket, ticket, and suppress categories. Justify each classification.

---

## 9.13 Further Reading

- *Observability Engineering* — Charity Majors, Liz Fong-Jones, George Miranda
- *Site Reliability Engineering* — Google
- *Distributed Systems Observability* — Cindy Sridharan
- OpenTelemetry official documentation and semantic conventions
- *How to Monitor* — Will Hileman
- *The Art of Monitoring* — James Turnbull

---

## 9.14 Summary Checklist

- [ ] can explain why observability requires high-cardinality data
- [ ] can instrument HTTP, RPC, database, and messaging layers
- [ ] can define SLIs and SLOs for services
- [ ] can compute an error budget and explain burn rate
- [ ] can design runbooks with commands and expected behavior
- [ ] can write a blameless postmortem template
- [ ] can reduce alert fatigue with tiered paging
- [ ] can choose a metrics, logs, and traces stack
- [ ] can define structured logging schemas that preserve correlation
- [ ] can configure dashboards that support incident response

---

> Next: [Chapter 10: Security Fundamentals](./10-security-fundamentals.md)