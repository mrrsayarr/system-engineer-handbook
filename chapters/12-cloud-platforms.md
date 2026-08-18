# Chapter 12: Cloud Platforms (AWS, GCP, Azure)

> **Estimated Time: 4-5 hours** | **Prerequisites: Chapters 1-11**

---

## Learning Objectives

By the end of this chapter, you will be able to:

1. **Choose the right service category** across AWS, GCP, and Azure for any workload
2. **Design multi-account, multi-region architectures** with shared responsibility
3. **Implement compute, storage, and networking** with cost and operations in mind
4. **Use managed services** for databases, messaging, and event streaming
5. **Apply security controls** in the cloud identity and access layer
6. **Design observability and governance** across three cloud vendors
7. **Evaluate trade-offs** in cost, compliance, and operational overhead

---

## 12.1 Cloud Mindset

### Shared responsibility

```text
CLOUD PROVIDER:
  physical data centers and hardware
  global network backbone
  hypervisor or container runtime isolation
  compliance certifications for facilities

CUSTOMER:
  operating system hardening when applicable
  identity and access management
  data protection and encryption
  network configuration and firewall rules
  application security
  compliance for data processing and privacy

THIS MODEL VARIES:
  IaaS shifts more responsibility to customer
  PaaS and serverless shift more to provider
  SaaS shifts nearly all responsibility except data and users
```

### Well-architected pillars

```text
OPERATIONAL EXCELLENCE:
  monitor, automate, improve
  Infrastructure as Code
  runbooks and incident response

SECURITY:
  identity, detective controls, infrastructure protection
  data protection, incident response

RELIABILITY:
  fault isolation, recovery planning
  handling change, automation for recovery
  testing recovery procedures

PERFORMANCE EFFICIENCY:
  select right resources and architecture
  scale globally, monitor to detect regressions
  consider trade-offs for lasting performance

COST OPTIMIZATION:
  consume only what is needed
  analyze expenditure over time
  managed services reduce operational cost
```

---

## 12.2 Compute Services

### AWS

```text
EC2:
  general purpose, burstable, memory optimized, accelerated computing
  spot, reserved, savings plans for cost optimization
  placement groups for network-intensive workloads

ECS:
  managed containers on AWS-managed or customer EC2
  simpler than Kubernetes on AWS

EKS:
  managed Kubernetes control plane
  worker nodes self-managed or Fargate
  strongest Kubernetes ecosystem compatibility
```

### GCP

```text
COMPUTE ENGINE:
  similar to EC2
  sustained use discounts automatically applied

GKE:
  Kubernetes native integration
  Autopilot removes node management burden

CLOUD RUN:
  fully managed container execution
  scale to zero
  suited for HTTP services and batch jobs
```

### Azure

```text
VIRTUAL MACHINES:
  broad selection of sizes and accelerators

AKS:
  managed Kubernetes
  integrates with Azure AD for identity

CONTAINER APPS:
  serverless containers with scale-to-zero and Dapr integration
  smoother adoption path from Web Apps to containers
```

---

## 12.3 Storage

### Object storage

```text
OBJECT STORAGE ACROSS VENDORS:
  AWS S3
  GCP Cloud Storage
  Azure Blob Storage

KEY PROPERTIES:
  virtually unlimited capacity
  strong durability typically 11 nines
  lifecycle policies for cost management
  versioning and replication for compliance
  presigned URLs for temporary access without credentials
```

```text
USE CASES:
  static assets, backups, data lake, artifacts, logs

DESIGN:
  bucket per environment or by data domain
  lifecycle transitions between access tiers
  encryption at rest and in transit
  versioning and delete protection for critical buckets
  cross-region replication for DR
```

### Block and file storage

```text
AWS EBS:
  gp3 for general purpose
  io2 for high durability and performance
  snapshot for backup and migration

AWS EFS:
  managed NFS
  suited for shared file system needs

AZURE DISKS:
  managed block with snapshot capability

GCP PERSISTENT DISK:
  zonal or regional for HA
  balanced, SSD, and extreme performance tiers
```

---

## 12.4 Networking

### Virtual private clouds

```text
AWS VPC:
  subnets, route tables, NACL, security groups
  internet gateway, NAT gateway, VPC endpoints

GCP VPC:
  global routing, regional subnets
  shared VPC for multi-project isolation

AZURE VNET:
  address spaces, subnets, NSG, route tables
  VNet peering and private endpoints
```

### Global and hybrid connectivity

```text
AWS:
  - CloudFront and Route53 for edge
  - Transit Gateway for hub and spoke
  - Direct Connect for dedicated connectivity

GCP:
  - Cloud CDN and Global External HTTP(S) Load Balancer
  - Cloud Router and Interconnect for hybrid

AZURE:
  - Front Door and Traffic Manager
  - ExpressRoute for private connectivity
  - Virtual WAN for global transit
```

---

## 12.5 Managed Data Services

### Relational databases

```text
AWS:
  RDS for managed PostgreSQL and MySQL
  Aurora for MySQL and Postgres compatible managed service
  DynamoDB for serverless key-value and document

GCP:
  Cloud SQL for managed MySQL and PostgreSQL
  Cloud Spanner for globally distributed relational
  Firestore for document model with strong consistency

AZURE:
  Azure SQL, managed PostgreSQL and MySQL
  Cosmos DB for globally distributed multi-model
```

### Messaging and real-time

```text
AWS:
  SQS for queues
  SNS for pub/sub
  EventBridge for event bus and schema registry
  MSK for managed Kafka

GCP:
  Pub/Sub for messaging
  Dataflow for stream and batch processing

AZURE:
  Service Bus for queues and topics
  Event Hubs for high throughput event ingestion
  Event Grid for event routing
```

---

## 12.6 Identity and Security

### Identity providers

```text
AWS IAM:
  users, groups, roles, policies
  identity center for SSO and federation
  permission boundaries and service control policies

GCP IAM:
  identity and access management with google identity integration
  workload identity for service accounts in GKE

AZURE AD:
  enterprise identity platform
  conditional access and identity protection
```

### Security controls

```text
VENDOR TOOLS:
  AWS GuardDuty, Security Hub, Config
  GCP Security Command Center
  Azure Defender and Microsoft Sentinel

INVESTIGATION:
  enable audit logging on all control planes
  centralize logs with retention policy
  automate response with playbooks
```

---

## 12.7 Observability and Management

### Management and governance

```text
AWS:
  CloudWatch for metrics, logs, alarms, dashboards
  X-Ray for distributed tracing
  Config for inventory and compliance
  Organizations for multi-account governance

GCP:
  Cloud Monitoring and Cloud Logging
  Cloud Trace and Cloud Profiler
  Organization Policy and Forseti for governance

AZURE:
  Monitor for metrics, logs, alerts, autoscale
  Application Insights for application telemetry
  Policy for governance across subscriptions
```

---

## 12.8 Migration and Modernization

### Migration strategy

```text
REHOST:
  lift and shift to cloud VMs
  fastest initial migration
  does not address optimization

REPLATFORM:
  move to managed services without architecture change
  replace self-managed DB with RDS or equivalent
  replace VMs with containers

REFACTOR:
  redesign for cloud native patterns
  serverless, event driven, microservices
  highest long term value and cost

RETIRE:
  identify systems that can be decommissioned
  reduce ongoing cost and complexity
```

---

## 12.9 Cost Optimization

### FinOps principles

```text
VISIBILITY:
  show cost by team, environment, service, and feature
  tag consistently and enforce in policy

OPTIMIZATION:
  right-size based on utilization
  reserved and committed use discounts for steady workloads
  spot and preemptible for fault tolerant batch workloads
  schedule non-production environments
```

---

## 12.10 Exercises

### Exercise 1

Design a multi-tier application on AWS with public and private tiers, database, messaging, caching, and global traffic routing. Explain which services you choose and why.

### Exercise 2

Design multi-region failover for a payment API. Include region topology, database replication, global routing, data residency, and failover procedure.

### Exercise 3

Design multi-cloud governance model for three environments with separate accounts and central networking. Include account strategy, network connectivity, identity federation, and cost visibility.

### Exercise 4

Migrate a self-managed PostgreSQL and Kafka deployment to managed cloud services. Include migration steps, cutover plan, rollback criteria, and data verification.

---

## 12.11 Further Reading

- *Cloud Design Patterns* — Microsoft Patterns & Practices
- *AWS Well-Architected Framework* — AWS official documentation
- *Google Cloud Architecture Framework* — GCP documentation
- *Azure Architecture Center* — Microsoft
- *The Phoenix Project* and *Accelerate* — operational foundation reading
- Vendor blogs on managed service updates

---

## 12.12 Summary Checklist

- [ ] can explain shared responsibility across IaaS, PaaS, SaaS
- [ ] can select compute, storage, and networking services for requirements
- [ ] can design multi-account or multi-project architecture
- [ ] can choose managed data service over self-managed
- [ ] can implement identity and security guardrails in a cloud provider
- [ ] can configure observability and governance platforms
- [ ] can plan migration strategy aligned to business constraints
- [ ] can design multi-region failover and DR
- [ ] can explain trade-offs among managed services across AWS, GCP, and Azure

---

> Next: [Chapter 13: System Engineer Cheat Sheets](./13-cheat-sheets.md)