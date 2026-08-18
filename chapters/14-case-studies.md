# Chapter 14: Real-World Case Studies

> **Estimated Time: 3-4 hours** | **Prerequisites: Chapters 1-13**

---

## Learning Objectives

By the end of this chapter, you will be able to:

1. **Analyze production architectures** beyond textbook diagrams
2. **Trace system evolution** from startup to planetary scale
3. **Identify non-functional requirements** that shaped major architectural decisions
4. **Evaluate trade-offs** companies actually accepted and rejected
5. **Apply lessons learned** to your own designs and interviews
6. **Present case studies** clearly using structured frameworks

---

## 14.1 How to Read a Case Study

### Framework for analysis

```text
FOR EVERY CASE STUDY:
  1. What was the original problem and constraint?
  2. What fundamental requirement drove the architecture?
  3. What alternatives were considered and rejected?
  4. What trade-off was chosen and why?
  5. What surprised the team during production?
  6. What would the team do differently today?
  7. What lessons apply to our context?
```

### Metrics that matter

```text
Scale metrics:
  users, requests per second, data volume
  geographic footprint
  hardware or service footprint

Performance metrics:
  latency targets and observed latency distributions
  throughput and failure rates
  cache hit ratios and database replication lag

Operational metrics:
  deployment frequency
  mean time to recovery
  error budget burn
  on-call and operational burden
```

---

## 14.2 URL Shortener (TinyURL, Bitly, Firebase Dynamic Links)

### Problem statement

```text
"Given a long URL, create a short one that redirects back to the long form."

Requirements:
  high read to write ratio
  redirect must be fast
  links must persist indefinitely by default
  custom aliases optional
  analytics optional
  global reach
```

### Architecture evolution

```text
DESIGN 1: MONOLITHIC
  web server appends to database
  redirect queries database by key
  single database becomes bottleneck at scale

DESIGN 2: SHARDED KEY-VALUE STORE
  write path updates primary shard
  read path serves from replicated shards
  add caching at web tier for hot keys
  improve latency but still limits shard write throughput

DESIGN 3: CACHED AND GEOGRAPHIC
  API gateway with geo routing
  rome or stack writes to nearest region
  cache at every layer absorbs hot reads
  metrics and business features separated
```

### Key lessons

```text
- read to write ratio determines caching importance
- stateless web tier allows effortless horizontal scale
- consistent hashing enables gradual resharding
- hot key detection is necessary for cache sizing
- persistence requirements decide storage class
```

---

## 14.3 Pastebin and File Sharing

### Problem statement

```text
"Upload text or files with auto expiry and shareable links."

Requirements:
  write once read many for public content
  short expiry and long expiry options
  bandwidth dominates operational cost
  large files must be supported
```

### Architecture choices

```text
STORAGE:
  object store with CDN fronted public read path
  signed URLs for private or expiring content
  lifecycle policies to delete expired blobs

KEY GENERATION:
  random key with collision retry
  base62 encoded for URL friendliness
  essential to scale write throughput independently

CACHING:
  CDN absorbs hot public reads
  backend sees only cold reads
  reduce origin load and network cost
```

### Key lessons

```text
- bandwidth is often the dominant operational cost
- CDN offload requires cache invalidation strategy
- short keys require collision retry, not idempotency
- expiry metadata drives lifecycle automation
```

---

## 14.4 News Feed (Facebook, X, LinkedIn)

### Problem statement

```text
"Return feed items from people and topics a user follows."

Requirements:
  fanout on write or fanout on read
  real time updates and low freshness
  personalization and ranking
  massive write fanout at posting moment
```

### Evolution to fanout on write

```text
FANOUT ON READ:
  query all followees on read
  simple to implement
  fails when followee graph grows large

FANOUT ON WRITE:
  expand posts to followers asynchronously when created
  reads become lookups on precomputed feed
  writes become heavier with fanout jobs
  requires robust queue and fanout workers
```

### Modern complications

```text
RANKING:
  feed is precomputed then reranked per user
  engagement model targets relevance over recency
  requires ML feature pipelines and low latency embeddings

LOAD SHEDDING:
  social graphs produce highly uneven load
  celebrity accounts define scaling limits
  dedicated pipeline and cached timelines for hot actors
```

### Key lessons

```text
- write amplification pays for read latency improvements at scale
- celebrity or celebrity-like accounts require special handling
- cache each composite feed rather than recomputing
- synthetic requests and caching reduce dependency chain latency
```

---

## 14.5 Netflix Streaming

### Problem statement

```text
Stream high quality video to millions of concurrent viewers globally.

Requirements:
  buffer underrun minimization
  ABR and adaptive bitrate streaming decisions
  personalization on home screen and playback start
  massive scale and cost sensitive
  reliability across devices, networks, and regions
```

### Architecture highlights

```text
CDN:
  Open Connect appliances at ISP locations
  reduce upstream costs and latency
  keep popular content very close to users

ENCODING:
  per title encoding reduces average bitrate while preserving quality
  multi variant manifests for ABR
  reduces CDN egress and improves startup time

PLAYER LOGIC:
  client or server driven ABR decisions
  buffer based models minimize rebuffer
  startup time and bitrate are opposing goals often
```

### Key lessons

```text
- user perceived quality is dominated by rebuffer and startup time
- network distribution at ISP scale reduces cost and improves reliability
- encoding cost is justified by bandwidth savings and quality gain
- complexity moves to client when it improves global scaling economics
```

---

## 14.6 Airbnb Search and Booking

### Problem statement

```text
Search homes globally with filters, pricing, availability, and recommendations.

Requirements:
  low search latency
  flexible filters and facets
  host controlled calendar and pricing automation
  trust and safety signals
  ranking over raw keyword match
```

### Architecture highlights

```text
SEARCH:
  Elasticsearch cluster with denormalized listing documents
  ranking model evaluates many signals
  geo distance and availability require heavy joins or precompute

PRICING:
  pricing recommendations aggregate comparable listing data
  nightly and seasonal pricing strategies
  demand prediction and dynamic uplift

PHOTOGRAPH OPTIMIZATION:
  large media collection requires CDN and transformation
  image optimization improves page load and SEO
```

### Key lessons

```text
- search relevance requires ongoing signal enrichment
- availability joins are expensive and often worth denormalizing
- recommendation and search pipelines share signals often
- image optimization is first order for user experience
```

---

## 14.7 Uber Dispatch

### Problem statement

```text
Match riders and drivers in real time with low latency and high throughput.

Requirements:
  geospatial queries by location
  real time availability
  ETA estimation
  event driven dispatch matching decisions
  global scale with regional compliance
```

### Architecture highlights

```text
GEOSPATIAL INDEXING:
  geohash or S2 cell based partitioning
  nearest driver queries at scale

REAL TIME PIPELINE:
  driver GPS messages routed to stream processing
  dispatch state updated in streaming database
  ETA uses road network aware routing

MATCHING:
  matching logic executed in stream processing or graph engine
  state kept lightweight to enable fast decisions
```

### Key lessons

```text
- geospatial indexing and partitioning choices affect query semantics
- throughput requirements dominate persistence engine choice
- event driven systems are natural fit for real time dispatch
- road aware routing is necessary for quality estimation
```

---

## 14.8 Uber Eats Recommendation

### Problem statement

```text
Rank restaurants for a user and time with taste and context.

Requirements:
  immediate ranking on request
  catalog of many restaurants
  per user signals and contextual signals
  online learning and rapid experimentation
```

### Key lessons

```text
- ranking systems need online evaluation to detect distribution shift
- feature freshness and feature store design affect model quality
- offline metrics do not guarantee user value
- experimentation framework separates signal from noise
```

---

## 14.9 Circuit Breaker and Fallback Patterns

### Problem statement

```text
Distributed systems frequently experience partial failures without full outage.

Requirements:
  fail fast rather than queue under saturation
  fallback behavior for unavailable dependency
  recover automatically when dependency recovers
  observability for circuit state changes
```

### Design examples

```text
API GATEWAY:
  circuit breaker per upstream route
  fallback response or cached alternative
  half open probes resume traffic gradually

SERVICE MESH:
  sidecar manages circuit per destination
  standardized timeout, retry, outlier detection
  dependency aware load balancing

APPLICATION:
  resilience libraries implement bulkhead and retry
  distinguish retryable from non retryable errors
  limit retry budget to protect downstream
```

### Key lessons

```text
- hiding failure from users is better than increasing latency to unavailable dependency
- half open probes should be slow enough to prevent thundering recovery
- bulkhead and circuit breaker solve related but distinct problems
- observability on state transitions is necessary to debug cascades
```

---

## 14.10 Exercises

### Exercise 1

Use the case study framework to analyze Twitter's transition from Ruby on Rails monolith to microservices. Present distilled lessons applicable to an engineering team designing their first microservice extraction.

### Exercise 2

Compare and contrast the news feed approaches of Facebook and X. Identify where divergent requirements produced different architectural choices.

### Exercise 3

For a travel booking aggregator, apply lessons learned from Airbnb and Uber to design search and dispatch across flights, hotels, and car rentals. Identify the highest risk architectural decisions and their mitigations.

### Exercise 4

Select a real production outage from public postmortems. Map its cause to patterns discussed in this book. Recommend a control that would have prevented, reduced, or shortened the incident.

---

## 14.11 Further Reading

- *Designing Data-Intensive Applications* — Martin Kleppmann
- *System Design Interview* — Alex Xu
- High Scalability blog
- Netflix Tech Blog
- Uber Engineering Blog
- Airbnb Engineering and Data Science Blog
- Twitter Engineering public postmortems
- Google SRE Book

---

## 14.12 Summary Checklist

- [ ] can analyze why platform scale forces specific architectural choices
- [ ] can identify scalability patterns in real products
- [ ] can translate product requirements into non-functional requirements
- [ ] can evaluate trade-offs presented in public architectures
- [ ] can apply lessons to new designs and interview answers
- [ ] can structure case study analysis using a repeatable framework

---

> Next: [Chapter 15: Interview Preparation Guide](./15-interview-preparation.md)