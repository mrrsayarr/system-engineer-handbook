# Capstone Project Guide

> **Estimated Time: 20-40 hours** | **Prerequisites: All Chapters (1-15)**

---

## Overview

This capstone project synthesizes everything you've learned. You'll design, document, and present a production-ready system from requirements through operational readiness.

---

## Project: Global Ride-Hailing Platform

### Problem Statement

Design a ride-hailing platform (like Uber/Lyft) supporting:
- **10M daily active riders** across 50 cities globally
- **2M active drivers** with real-time location updates
- **50K concurrent rides** at peak
- **Sub-second dispatch latency** (match rider to driver)
- **99.99% availability** for dispatch and payments
- **Multi-region active-active** with < 30s failover
- **PCI DSS compliance** for payments
- **GDPR compliance** for EU rider data

---

## Deliverables

### 1. Requirements Document (2-3 pages)
- Functional requirements (user stories)
- Non-functional requirements with specific targets
- Scale estimates with back-of-the-envelope calculations
- Constraints and assumptions

### 2. Architecture Design (4-6 pages)
- High-level component diagram (C4 Level 1-2)
- API contracts for core flows (REST/gRPC)
- Data models with access patterns
- Technology choices with justification
- Cross-region topology

### 3. Deep Dive Analyses (3-4 pages each, choose 3)
Choose **three** from:
- **Dispatch System**: Geospatial indexing, matching algorithm, real-time pipeline
- **Payment System**: PCI scope, tokenization, saga for charge+refund, idempotency
- **Real-time Location**: Driver GPS ingestion, WebSocket/HTTP2, fanout to riders
- **Pricing Engine**: Surge calculation, ML feature store, A/B experimentation
- **Notifications**: Multi-channel (push, SMS, email), preference management, delivery guarantees
- **Fraud Detection**: Real-time scoring, feature store, model deployment

### 4. Operational Readiness (2-3 pages)
- SLIs/SLOs/error budgets for critical paths
- Observability design (metrics, logs, traces, dashboards)
- Alerting strategy with runbook examples
- CI/CD pipeline with progressive delivery
- Disaster recovery plan (RPO/RTO, failover procedure)
- Security controls (mTLS, secrets, encryption, WAF)
- Cost model with optimization strategies

### 5. ADRs (3-5 records)
Document key architectural decisions using the [ADR template](../appendices/adr-templates.md).

### 6. Presentation (20 minutes)
- 5 min: Problem and requirements
- 5 min: Architecture overview
- 5 min: Deep dive on one component
- 5 min: Operational readiness and trade-offs

---

## Evaluation Rubric

| Criterion | Weight | Excellent (5) | Good (4) | Satisfactory (3) | Needs Work (1-2) |
|-----------|--------|---------------|----------|------------------|------------------|
| **Requirements Clarity** | 10% | Complete, quantified, prioritized | Clear with minor gaps | Basic coverage | Missing key NFRs |
| **Architecture Soundness** | 25% | Cohesive, well-justified, scalable | Solid with minor issues | Functional but fragile | Major gaps or contradictions |
| **Deep Dive Depth** | 25% | Production-grade detail, trade-offs | Good technical depth | Covers basics | Superficial |
| **Operational Maturity** | 20% | Comprehensive SLOs, runbooks, DR | Solid ops coverage | Basic monitoring | Missing key areas |
| **Decision Quality (ADRs)** | 10% | Clear context, alternatives, consequences | Good structure | Basic documentation | Missing or vague |
| **Communication** | 10% | Clear diagrams, confident presentation | Well-organized | Understandable | Hard to follow |

---

## Suggested Timeline

### Week 1: Requirements & High-Level Design
- Days 1-2: Requirements gathering, scale estimation
- Days 3-4: Component diagram, API contracts, data models
- Days 5-7: Technology selection, cross-region topology

### Week 2: Deep Dives
- Days 8-10: Deep Dive 1 (Dispatch or Payments)
- Days 11-13: Deep Dive 2 (Real-time or Pricing)
- Days 14-15: Deep Dive 3 (Notifications or Fraud)

### Week 3: Operational Readiness & ADRs
- Days 16-18: SLIs/SLOs, observability, alerting, CI/CD
- Days 19-20: DR, security, cost, ADRs

### Week 4: Polish & Present
- Days 21-23: Integrate, review, refine diagrams
- Days 24-26: Practice presentation
- Day 27: Final review and submission

---

## Reference Architectures (For Inspiration Only)

> **Do not copy** — use as reference for patterns and vocabulary.

- **Uber Engineering Blog**: Dispatch, marketplace, pricing, fraud
- **Lyft Engineering**: Real-time, streaming, ML platform
- **Grab Engineering**: Southeast Asia scale, superapp architecture
- **DoorDash Engineering**: Logistics, dispatch, ML
- **Netflix Tech Blog**: Resilience, chaos, observability (patterns transfer)

---

## Stretch Goals (Bonus)

- Implement a **minimal prototype** of one component (dispatch, pricing, or notifications)
- Add **chaos engineering experiments** for your design
- Create **terraform modules** for core infrastructure
- Write **contract tests** for service interfaces
- Design **multi-cloud deployment** strategy

---

## Submission

Create a GitHub repository with:
```
/capstone
  /docs
    requirements.md
    architecture.md
    deep-dive-1.md
    deep-dive-2.md
    deep-dive-3.md
    operational-readiness.md
    adrs/
      001-dispatch-platform.md
      002-payment-system.md
      ...
  /presentation
    slides.pdf
  /prototype (optional)
    /dispatch-service
    /pricing-engine
  README.md
```

Share the repository link for review.

---

## Resources

- [System Design Checklist](../appendices/system-design-checklist.md)
- [ADR Templates](../appendices/adr-templates.md)
- [Case Studies](../chapters/14-case-studies.md)
- [Interview Guide](../chapters/15-interview-preparation.md)

---

> **Remember**: The goal is not a perfect system — it's demonstrating structured thinking, trade-off analysis, and production awareness. Document your uncertainties and what you'd explore next.

> **Good luck!** This is where the handbook becomes yours.