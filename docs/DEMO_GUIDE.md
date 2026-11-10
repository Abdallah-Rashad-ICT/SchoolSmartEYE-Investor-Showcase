# Investor Demo Guide

## Suggested 15-minute walkthrough

### 1. Problem and vision — 2 minutes
Explain the goal: a school-focused, local-first intelligence platform connecting selected school workflows, educational AI, and carefully governed safety-oriented research.

### 2. Distributed Local AI Router — 4 minutes
Show the PC1–PC5 architecture. Clearly identify whether the demonstration is a static diagram, metadata-only route-planning test, or live end-to-end execution. Do not describe route planning as completed distributed inference.

### 3. Local knowledge assistant / RAG — 3 minutes
If a working local environment is available, demonstrate retrieval only with approved, non-sensitive sample documents. Show how sources are surfaced. If the environment is not running, present the workflow as a design or prototype—not a live feature.

### 4. Vision and predictive safety research — 3 minutes
Explain current maturity. The preserved vision engine measures luminance changes; it is not a validated occupancy, identity, or fall-detection product. Predictive signals are a research direction, not proven incident forecasts. Any safety-related output requires human review.

### 5. Wearable pathway — 1 minute
Explain that wearable integration is blocked pending schema, security, consent, and governance redesign. Do not present live student biometric monitoring.

### 6. Roadmap — 2 minutes
Present the next milestones: authenticated local execution, reproducible hardware benchmarks, security tests, and a controlled one-school pilot.

## Demo safety checklist

- Use synthetic, non-identifying sample data only.
- Confirm the exact branch and commit being demonstrated.
- Label every screen as live, simulated, static, or research-only.
- Verify local services and dependencies before the meeting.
- Do not expose secrets, tokens, private student records, or internal endpoints.
- Prepare a fallback recording or architecture walkthrough, clearly labelled.
- Do not claim tests passed unless successful logs can be shown with the corresponding commit.

## Suggested opening

"SchoolSmartEYE AI is being built around a local-first approach. Rather than assuming every school needs an expensive dedicated AI server, we are designing a policy-driven layer to coordinate eligible workloads across ordinary school computers. Around that infrastructure, we are developing school knowledge intelligence and researching privacy-conscious safety capabilities. Today I will distinguish what is implemented, what is experimental, and what still needs validation."

## Questions to prepare for

- What runs today, and what is only a design or research prototype?
- What works without internet access?
- Which workloads run on CPU-only devices, and what benchmarks support that?
- How are school boundaries, permissions, and secrets enforced?
- What data is collected, retained, or exported?
- How will false positives and false negatives be evaluated?
- What is the smallest paid pilot that can validate value?
