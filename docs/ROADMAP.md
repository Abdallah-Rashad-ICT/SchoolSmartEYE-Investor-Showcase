# Development Roadmap

This roadmap describes proposed milestones. It is not a statement that each milestone is already funded, scheduled, or complete.

## Phase 1 — Secure local foundation
- Stabilize PC1 identity and school-level authorization.
- Complete authenticated service-to-service execution.
- Add durable replay protection and restart/concurrency tests.
- Establish repeatable CI and security checks.

**Exit evidence:** reproducible green tests, threat-model review, and documented local setup.

## Phase 2 — One-school local AI prototype
- Define supported hardware profiles for ordinary school computers.
- Enroll local worker nodes securely.
- Benchmark model inference, retrieval, latency, resource use, and failure recovery.
- Demonstrate a local knowledge assistant using approved sample documents.

**Exit evidence:** repeatable measurements on named hardware and a documented end-to-end demo.

## Phase 3 — School workflow integration
- Integrate a minimal, useful school workflow.
- Add document approval and source-grounded RAG.
- Add role-based access, auditability, and retention controls.

**Exit evidence:** acceptance tests using synthetic or approved data and school-user feedback.

## Phase 4 — Safety research validation
- Define narrow, consented and privacy-reviewed use cases.
- Evaluate visual and temporal signals on suitable, lawfully obtained datasets.
- Measure false positives, false negatives, and environmental limitations.
- Keep all consequential decisions under human review.

**Exit evidence:** independent evaluation and documented limitations before any pilot use.

## Phase 5 — Wearable redesign (optional)
- Redesign data schema, device enrollment, security, consent, and governance.
- Limit any future signals to clearly justified, opt-in purposes.
- Do not infer emotion, attention, comprehension, or mental state.

**Exit evidence:** security and privacy review plus explicit pilot approval.

## Phase 6 — Controlled one-school pilot
- Deploy only accepted capabilities.
- Train designated staff and document incident handling.
- Measure usability, reliability, operational cost, and support burden.
- Decide whether evidence supports expansion.

**Exit evidence:** pilot report, risk review, and go/no-go decision for additional schools.
