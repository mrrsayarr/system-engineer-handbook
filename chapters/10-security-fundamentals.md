# Chapter 10: Security Fundamentals

> **Estimated Time: 3-4 hours** | **Prerequisites: Chapters 1-9**

---

## Learning Objectives

By the end of this chapter, you will be able to:

1. **Map threats to boundaries** across identity, network, host, and application
2. **Implement zero-trust controls** with mTLS, SPIFFE, and policy-based access
3. **Design secure deployment pipelines** and harden hosts and containers
4. **Select and configure encryption** for data in transit and at rest
5. **Detect intrusions and anomalies** using logs, EDR, and runtime security
6. **Respond to incidents** with containment, evidence preservation, and communication
7. **Apply compliance frameworks** such as SOC 2 and ISO 27001 to operational practices

---

## 10.1 Threat Modeling

### STRIDE model

```text
SPOOFING
  - attacker pretends to be another user or system
  - mitigations: strong authentication, tokens, certificates

TAMPERING
  - attacker modifies data in transit or at rest
  - mitigations: signatures, checksums, integrity checks

REPUDIATION
  - attacker denies actions without trace
  - mitigations: audit logs, non-repudiation proofs

INFORMATION DISCLOSURE
  - attacker reads data without authorization
  - mitigations: encryption, access control, minimal data exposure

DENIAL OF SERVICE
  - attacker exhausts resources or availability
  - mitigations: rate limits, queuing, redundancy, load shedding

ELEVATION OF PRIVILEGE
  - attacker gains unauthorized capabilities
  - mitigations: least privilege, role separation, authorization checks
```

### Dataflow diagram for threat modeling

```text
CLOUD           PERIMETER         INTERNAL
                                       users
                                         |
                                   Auth / SSO
                                         |
               internet ----► DMZ ----► INTERNAL NETWORK
                             |               |
                         WAF/API GW      APP SERVERS
                             |               |
                         Ingress          DATA TIER
                             |               |
                          CDN             OBSERVABILITY
```

Identify trust boundaries:
- internet to edge
- edge to services
- service to database
- tenant to tenant
- human to machine

For each boundary, define trust assumptions and enforce controls that do not depend on upstream correctness.

---

## 10.2 Identity and Access Management

### Authentication, authorization, and identity

```text
AUTHENTICATION:
  who are you?
  password, OTP, hardware key, certificate, biometric

AUTHORIZATION:
  what may you do?
  role-based, attribute-based, relationship-based, policy-based

IDENTITY:
  stable subject across systems
  human identity vs workload identity vs service account
```

### Zero trust for systems

```text
ASSUMPTION:
  no implicit trust based on network location
  verify explicitly every request and workload identity

CONTROLS:
  - mTLS between services
  - identity-aware proxy
  - fine-grained access policies
  - continuous verification with contextual signals
  - audit every grant and deny
```

```text
EXAMPLE WORKLOAD IDENTITY FLOW:
  pod requests short-lived certificate from SPIFFE Workload API
  certificate contains SPIFFE ID
  downstream services verify peer certificate in mTLS handshake
  policy engine enforces allowed client IDs per route
```

---

## 10.3 Network Security

### Zero-trust network segmentation

```text
Traditional:
  internal is trusted, external is hostile
  flat network inside perimeter

Zero trust:
  every connection requires authentication and authorization
  east-west traffic is inspected
  default deny policy posture
  implicit trust is removed
```

### mTLS and policy enforcement

```text
mTLS for service communication:
  authenticate both sides of connection
  encrypt traffic without explicit application changes
  avoid relying only on TLS for perimeter traffic

POLICY EXAMPLE:
  allow:
    billing service to call payment service
    order service to call inventory service
  deny:
    web tier to direct database port
    any service to DNS or metadata unless approved
    cross-tenant database access
```

### Firewalls and rulesets

```text
GOAL:
  minimize allowed paths
  every allowed path must have a justification
  logs for deny events as well as allow events

STRUCTURE:
  management plane rules allowlisted explicitly
  data plane rules narrow and ordered
  review rules on a documented schedule
```

---

## 10.4 Host and Container Security

### Hardening checklist

```text
OS:
  - minimal base image
  - disable unused services and ports
  - enable automatic security updates
  - enforce same authentication policy for console and remote
  - use read-only root filesystem where possible

CONTAINER:
  - run as non-root user
  - drop capabilities and block privilege escalation
  - use seccomp and apparmor profiles
  - do not run containers in privileged mode
  - resource limits enforced at pod level
  - image scanning in CI and registry admittance
  - sign images and verify signature at admission
```

### Runtime protection

```text
RUNTIME SECURITY:
  detect unexpected exec calls, file writes, and network connections
  use Falco or equivalent runtime security tool
  alert on sensitive path access
  detect crypto miners and unexpected shells
  enforce allowed executable policy
```

---

## 10.5 Data Protection

### Data classification

```text
PUBLIC:
  - public marketing, support documents
  - no special controls

INTERNAL:
  - internal wiki, non-sensitive dashboards
  - access control to authenticated staff

CONFIDENTIAL:
  - customer PII, financial data, business plans
  - encryption at rest and in transit
  - strict access control and audit logs

RESTRICTED:
  - secrets, encryption keys, compliance regulated data
  - hardware security modules for top secret keys
  - strict need-to-know, break-glass procedures
```

### Encryption in transit

```text
INTERNAL TRAFFIC:
  - prefer mTLS for service mesh
  - disable HTTP and plaintext listeners on internal ports
  - validate certificate properties at runtime

EXTERNAL TRAFFIC:
  - TLS 1.3 minimum
  - strong cipher suites only
  - certificate rotation automated
  - HSTS header for browsers
```

### Encryption at rest

```text
DATABASE:
  enable transparent data encryption when supported
  manage encryption keys outside database host
  rotate keys regularly

OBJECT STORAGE:
  default encryption enabled
  control access with bucket policies and KMS

BACKUPS:
  encrypt all backups with separate keys
  test restoration with encryption enabled
  apply same classification controls as source
```

---

## 10.6 Secrets Management

### Principles

```text
PRINCIPLES:
  - secrets never in code, config files, or logs
  - secret values visible only at runtime
  - access to secret management is tightly controlled
  - audit all secret access

STORAGE:
  - external secret store with access policy
  - short-lived credentials preferred over long-lived
  - automatic rotation where possible
  - support failure recovery without exposing secrets
```

### Runtime injection examples

```text
ENV vs VOLUME:
  env var -> visible in process listings, secure in modern orchestrators
  volume mount -> file path avoids env variable exposure
  prefer volume mount for sensitive values in suspicious environments

RUNTIME:
  vault agent injector
  AWS Secrets Manager with IAM
  GCP Secret Manager with Workload Identity
  Azure Key Vault with managed identity
  Kubernetes external secrets or CSI driver
```

---

## 10.7 Application Security

### Injection prevention

```text
COMMON INJECTION ATTACKS:
  SQL injection -> use parameterized queries or ORM
  command injection -> avoid shell interpretation, use library calls
  path traversal -> validate and canonicalize paths
  LDAP injection -> use parameterized LDAP filters
  header injection -> validate and sanitize all headers
  XML external entity -> disable external entity parsing
```

### Cross-site and request forgery

```text
XSS:
  escape output according to sink
  use template engines that auto-escape
  set Content-Type and X-Content-Type-Options
  implement CSP where feasible

CSRF:
  require custom headers for state-changing requests
  same-site cookies and CSRF tokens
  validate Origin or Referer for dangerous operations
```

### Input validation

```text
DEFENSE IN DEPTH:
  - validate at entry point
  - validate again at business logic
  - validate third-party inputs even after authentication

TYPES:
  type checking, length limits, format validation
  enum allowlists, regex where bounded
  file validation by magic bytes, not extensions
  JSON schema validation for structured inputs
```

---

## 10.8 API Security

### Authentication and authorization

```text
TOKEN CHOICES:
  short-lived access tokens with refresh tokens
  opaque tokens vs self-contained JWT
  validate JWT signature, issuer, audience, expiry
  reject tokens without explicit algorithm
```

### Rate limiting and abuse prevention

```text
CLIENT IDENTIFICATION:
  authenticated identity over IP when available
  fallback to IP with allowlist for known proxies

RATE LIMITS:
  per route, per method, per client
  global and per resource
  return Retry-After on limit

ABUSE DETECTION:
  unusual request patterns
  credential stuffing
  scraping
  sequential enumeration
```

---

## 10.9 Compliance and Auditing

### Common frameworks

```text
SOC 2 TYPE II:
  trust service criteria: security, availability, processing integrity,
  confidentiality, privacy
  requires evidence of control over time
  system description, controls, testing by auditor

ISO 27001:
  information security management system
  risk assessment and treatment
  documented controls across people, process, technology

PCI DSS:
  cardholder data environment controls
  network segmentation applies
  quarterly scans and annual assessment

GDPR:
  data minimization, purpose limitation
  consent and right to erasure
  data protection impact assessment for high risk
```

### Audit logging requirements

```text
EVENTS TO LOG:
  authentication success and failure
  authorization grant and denial
  administrative actions
  configuration changes
  data access to sensitive classes
  privilege escalation events
  deletion or export actions

LOG PROTECTION:
  append-only storage for critical logs
  separate logging from application writers
  protect against deletion and tampering
  retain according to regulatory minimums
```

---

## 10.10 Security Operations

### Vulnerability management

```text
LIFECYCLE:
  discovery -> triage -> remediation -> validation -> closure

PRIORITY:
  critical remote code execution first
  authentication bypasses second
  then privilege escalation
  then information disclosure with impact
  then low severity and informational

AUTOMATION:
  container image scanning in CI
  dependency scanning in every build
  SAST and DAST in pipelines
  SCA for known vulnerable packages
```

### Incident response for security events

```text
CLASSIFICATION:
  - triage severity and data exposure scope
  - determine if legal notification required

CONTAINMENT:
  - isolate affected systems
  - preserve evidence
  - disable compromised identities
  - rotate secrets immediately

ERADICATION:
  - remove attacker access
  - patch exploited vulnerability
  - rebuild affected systems if needed

RECOVERY:
  - restore from clean backup
  - restore operations under observation
  - monitor for resumption of activity

LESSONS LEARNED:
  - review detection gap that allowed dwell time
  - update threat model
  - improve monitoring coverage
```

---

## 10.11 Exercises

### Exercise 1

Threat model a payment API. Identify trust boundaries, list threats per STRIDE category, and propose mitigations with implementation notes.

### Exercise 2

Design zero trust access for internal admin interfaces. Include workload identity, policy engine integration, authentication for humans, logging requirements, and breach containment controls.

### Exercise 3

Design secrets lifecycle for a service with database, Redis, external payment gateway, and third-party analytics. Include provisioning, rotation, fallback behavior, and audit trails.

### Exercise 4

Design a secrets audit and rotation process for production. Include automation scope, manual exceptions, human approval threshold, and fallback when secret management is unavailable.

---

## 10.12 Further Reading

- *Zero Trust Networks* — Evan Gilman and Doug Barth
- *Practical Cloud Security* — Chris Dotson
- *Threat Modeling: Designing for Security* — Adam Shostack
- *Security Engineering* — Ross Anderson
- OWASP Top 10, ASVS, and Cheat Sheet Series
- NIST Cybersecurity Framework
- ISO 27001 and SOC 2 official documentation

---

## 10.13 Summary Checklist

- [ ] can apply STRIDE to a service or integration
- [ ] can explain zero trust and workload identity
- [ ] can design mTLS-based service communication
- [ ] can harden hosts and containers
- [ ] can implement secrets management with rotation
- [ ] can classify data and select controls
- [ ] can detect injection, XSS, and CSRF defenses
- [ ] can design API authentication and authorization
- [ ] can define audit logging requirements
- [ ] can describe vulnerability management lifecycle
- [ ] can lead a security incident response simulation

---

> Next: [Chapter 11: DevOps, CI/CD & Infrastructure as Code](./11-devops-cicd-iac.md)