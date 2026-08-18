# Chapter 11: DevOps, CI/CD & Infrastructure as Code

> **Estimated Time: 3-4 hours** | **Prerequisites: Chapters 1-10**

---

## Learning Objectives

By the end of this chapter, you will be able to:

1. **Explain DevOps culture** and its practitioners' shared ownership model
2. **Design and automate CI/CD pipelines** with quality gates
3. **Implement Infrastructure as Code** using Terraform and Pulumi
4. **Configure Kubernetes workloads** and GitOps delivery
5. **Apply release strategies** such as blue-green and canary
6. **Manage drift, secrets, and state** across environments
7. **Measure delivery performance** with DORA metrics

---

## 11.1 What DevOps Means

### Culture before tools

```text
DevOps is not a team or a set of tools.
It is a set of practices that shorten feedback loops between
development and operations.

KEY GOALS:
  - faster, safer delivery
  - shared ownership of production
  - automated everything repeatable
  - measurement driven improvement
  - blameless culture around failures
```

### Conway's law and organization design

```text
Conway's law: systems mirror organizational communication structure.
If you want loosely coupled architecture, strive for loosely coupled teams.

IMPLICATIONS:
  - cross-functional teams reduce handoffs
  - service ownership encourages design for operability
  - clear interfaces reduce integration risk
  - enablement teams reduce duplication
```

### Team topologies

```text
STREAM-ALIGNED TEAMS:
  own a service or product end to end
  design, build, test, operate, improve

PLATFORM TEAMS:
  internal products that reduce cognitive load
  examples: developer portal, shared CI pipelines, secure deployment defaults

ENABLING TEAMS:
  temporary coaching engagement
  spread knowledge, then disband

COMPLICATED SUBSYSTEM TEAMS:
  deep specialized knowledge across boundaries
  avoid overusing; prefer embedded specialists where possible
```

---

## 11.2 CI/CD Fundamentals

### Pipeline anatomy

```text
CODE:
  developer commits to version control
  branch or mainline model

BUILD:
  fetch dependencies, compile, lint
  static analysis, unit tests
  produce artifact or container image
  sign artifact if applicable

TEST:
  integration tests, contract tests
  security scanning, dependency audit
  performance regression if feasible

PACKAGE:
  push artifact to registry
  tag with commit SHA or semantic version
  generate SBOM if required

DEPLOY:
  promote artifact through environments
  run smoke tests and synthetic monitors
  validate health after deployment
```

### Pipeline design principles

```text
FAST:
  optimize hot paths first
  cache dependencies without compromising correctness
  parallelize independent tasks
  fail fast on syntax and contract errors

RELIABLE:
  same processes run in CI, staging, and production
  ephemeral environments reduce drift
  deterministic builds
  reproducible runs
```

### Branching and delivery models

```text
TRUNK-BASED:
  short-lived branches or feature flags
  main branch always releasable
  encourages continuous integration
  best for high frequency releases

GITFLOW:
  develop, release, hotfix branches
  more ceremony and merge overhead
  suited for versioned software releases

GITHUB FLOW / GITLAB FLOW:
  simplified trunk-based with environments
  merge to main triggers deployment
  PR checks the readiness gates
```

---

## 11.3 Infrastructure as Code

### Why immutable infrastructure wins

```text
IMMUTABLE:
  instances are never changed in place
  update by replacing artifacts and instances
  no snowflake drift
  reproducibility is natural

MUTABLE:
  ssh into instance and change config
  fast for ad-hoc changes
  drift accumulates
  harder to reproduce or recover
```

### Terraform

```text
HCL workflow:
  write configuration defining desired state
  terraform plan shows diff
  terraform apply enforces desired state
  state is the contract for current reality

STATE:
  store in remote backend with locking
  sensitive values protected by encryption
  never edit manually unless forced
  use workspaces or separate state files per environment

MODULES:
  reuse infrastructure patterns as modules
  modules accept variables and expose outputs
  prefer modules over copy paste

PROVISIONERS:
  use only when provider lacks needed resource
  prefer native provider resources over scripts
  avoid file provisioners when possible
```

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "prod-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = false

  tags = {
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}
```

### Pulumi

```text
PULUMI:
  use general purpose languages
  leverage existing libraries
  easier for teams already fluent in programming rather than DSL

CHOOSING:
  Terraform:
    large ecosystem and provider coverage
    strong hiring pool with existing Terraform experience
    mature state and remote backend options

  Pulumi:
    organization already uses TypeScript, Go, or Python
    conditional logic is easier with general-purpose language
    complex policy enforcement via code review easier
```

---

## 11.4 Configuration Management

### Config, secrets, and environment boundaries

```text
CONFIG:
  values that differ between environments
  stored in parameter store or environment specific files
  secrets stripped out before reaching runtime

ENVIRONMENTS:
  dev, staging, prod, or shared environments
  each environment depends on the last
  treat staging as production for realism

DRIFT DETECTION:
  drift is the enemy of IaC reliability
  run drift detection regularly and prefer repair over investigation
  document exceptions with owner and expiration
```

### Ansible

```yaml
- name: ensure app user exists
  user:
    name: app
    shell: /usr/sbin/nologin
    groups: appgroup
    state: present

- name: ensure application directory
  file:
    path: /opt/app
    state: directory
    owner: app
    group: app
    mode: "0750"

- name: deploy application
  copy:
    src: app.tar.gz
    dest: /opt/app/
    owner: app
    group: app
  notify: restart app

- name: ensure systemd unit
  copy:
    src: app.service
    dest: /etc/systemd/system/app.service
  notify: daemon reload
```

---

## 11.5 Container and Image Security

### Image composition

```text
MINIMAL BASE:
  distroless or scratch when feasible
  reduce attack surface and CVE exposure
  reproducible builds via lock files

VERSION PINNING:
  pin base image by digest rather than tag
  pin OS packages
  pin language runtime when possible

PERMISSIONS:
  run as non-root user
  no sudo in runtime
  filesystem permissions follow least privilege
```

### Admission policy

```text
ADMISSION CONTROL:
  enforce security policies before workloads run
  reject images without org.opencontainers.image.source
  require signatures on critical namespaces
  prevent privileged mode, hostPath, hostNetwork unless explicitly approved

AUDIT:
  continuously audit running workloads
  alert on policy violations in production
```

---

## 11.6 Release Strategies

### Rolling update

```text
Rolling:
  replace instances gradually
  keep service available during rollout
  risk: new version exposed while still buggy

Controls:
  max surge and max unavailable
  health checks gate progression
  rollback automatically on failure detection
```

### Blue green

```text
Blue-green:
  two environments: blue and green
  promote new release from staging to idle environment
  cutover load balancer instantly
  keep previous environment for instant rollback

Costs:
  double capacity during transition window
  database migrations require backward compatibility
```

### Canary

```text
Canary:
  small initial traffic percentage
  increase gradually based on health signals
  abort if SLOs degrade
  confident delivery with live user validation

Signals:
  latency, error rate, saturation
  business metrics: conversion, cart abandonment
  anomaly detection complements thresholds
```

---

## 11.7 Kubernetes for System Engineers

### Resource model and QoS

```text
Resource requests:
  guaranteed minimum CPU and memory
  scheduler uses requests for bin packing

Resource limits:
  enforced at container level
  may cause OOM kill if breached
  avoid setting limit lower than expected usage without evidence

QoS classes:
  Guaranteed -> requests == limits for CPU and memory
  Burstable -> requests != limits
  BestEffort -> no requests

Production guidance:
  stateful workloads: requests == limits for memory
  stateless workloads: requests often below limit
  never set CPU limit lower than observed usage
```

### Networking

```text
Services:
  cluster IP, node port, load balancer
  selectors, endpoints, DNS

Ingress and Gateway API:
  HTTP routing and TLS termination at edge
  host, path, header rules
  TLS secrets and cert management

NetworkPolicy:
  default deny all ingress and egress
  allow specific namespaces and pods
  protect database port from app tier
  zero trust north-south and east-west
```

### Observability in Kubernetes

```text
METRICS:
  cAdvisor and kubelet expose node and pod metrics
  kube-state-metrics exposes controller object state
  Prometheus Operator manages scrape rules and alerts

LOGS:
  stdout and stderr collected by node agent
  centralized log store such as Loki or Elasticsearch

TRACES:
  instrument application and mesh sidecar
  correlate service mesh metrics with traces
```

---

## 11.8 GitOps

### Principles

```text
DECLARATIVE:
  entire system described by desired state in Git
  no manual changes after initial bootstrap

VERSIONED AND IMMUTABLE:
  history preserved and auditable
  pure functional deployments per commit

PULLED AUTOMATICALLY:
  software agents pull desired state rather than receive push
  reconcile current state to desired state continuously
```

### ArgoCD example flow

```text
PRINCIPLES:
  Git is single source of truth for environment definitions
  applications compared to live state continuously
  sync status visible in UI and API
  manual or automated sync with progressive delivery

BENEFITS:
  audit via git log
  self-service environment promotion
  fast rollback by changing commit or tag
  reduced blast radius through progressive delivery
```

---

## 11.9 Secrets in Pipelines

### Secrets lifecycle

```text
STORAGE:
  use external secret store with access policy
  rotate credentials frequently
  limit TTL

INJECTION:
  fetch at runtime rather than bake into image
  use service account and short-lived credentials
  fallback to sidecar or init container where needed

ACCESS:
  audit all reads
  restrict access by task or environment
  support break-glass for emergencies
```

### CI/CD secret rules

```text
RULES:
  never log secret values
  never pass secrets as command line args
  mask secrets in logs and UI
  separate secrets per environment
  secrets live in secret store not in pipeline config
  rotate after every breach suspicion

IMPLEMENTATION:
  Vault, AWS Secrets Manager, GCP Secret Manager, Azure Key Vault
  OIDC based access instead of long-lived tokens where possible
  cloud roles assigned via short-lived tokens
```

---

## 11.10 Testing in Delivery Pipelines

### Test strategy

```text
UNIT:
  fast, isolated, repeatable
  run on every commit
  maximum value per second invested

INTEGRATION:
  test service boundaries and contracts
  include database, cache, message broker
  run in ephemeral environment

CONTRACT:
  consumer driven contract tests
  provider contract verification

E2E:
  replicate critical user journeys
  expensive and brittle; minimize these
  prefer synthetic monitors over browser tests when possible

CHAOS:
  inject failure in staging or non-critical environments
  validate recovery and monitoring
  expand to production carefully with safeguards
```

---

## 11.11 Drift Prevention

### Drift taxonomy

```text
CONFIGURATION DRIFT:
  manual changes outside IaC
  configuration management detects and reverts

RUNTIME DRIFT:
  unexpected containers or permissions
  detected by policy engine

COST DRIFT:
  unowned or unused resources surfaced via tagging and budget alerting
  enforced by policy and scheduled cleanup
```

---

## 11.12 Cost Management

### Cost visibility

```text
TAGGING STRATEGY:
  tag by environment, owner, service, cost center
  enforce tag policy before resource creation
  treat missing tag as error

ANOMALY DETECTION:
  daily and weekly spend by service
  percentage change thresholds
  alert before budget exceeded
```

---

## 11.13 Exercises

### Exercise 1

Design a CI/CD pipeline for a stateless API service. Include code checkout, security scanning, testing, container build, registry push, deployment target, smoke tests, and rollback automation.

### Exercise 2

Design Terraform module layout for multi-environment, multi-account AWS setup. Include account structure, shared networking, per-service modules, state organization, and policy enforcement.

### Exercise 3

Design GitOps workflow for production Kubernetes cluster. Define repository layout, promotion model, progressive delivery, rollback plan, and configuration separation principles.

### Exercise 4

Identify drift risks for a Kubernetes based platform and design automated mitigations. Include runtime policy, drift detection frequency, remediation automation, and manual exception workflow.

---

## 11.14 Further Reading

- *Accelerate* — Nicole Forsgren, Jez Humble, Gene Kim
- *The Phoenix Project* — Gene Kim, Kevin Behr, George Spafford
- *Infrastructure as Code* — Kief Morris
- *Terraform: Up & Running* — Yevgeniy Brikman
- ArgoCD, Flux, and Kubernetes official documentation
- *Team Topologies* — Matthew Skelton and Manuel Pais

---

## 11.15 Summary Checklist

- [ ] can explain why immutable infrastructure reduces drift
- [ ] can write reusable Terraform modules with providers
- [ ] can design CI/CD pipelines with quality gates
- [ ] can configure Kubernetes workloads, networking, and policy
- [ ] can implement GitOps with ArgoCD or Flux
- [ ] can design rollout, rollback, and progressive delivery
- [ ] can enforce secrets lifecycle and short-lived credentials
- [ ] can measure delivery performance with DORA metrics
- [ ] can detect and remediate configuration drift
- [ ] can design cost visibility and anomaly detection

---

> Next: [Chapter 12: Cloud Platforms (AWS, GCP, Azure)](./12-cloud-platforms.md)