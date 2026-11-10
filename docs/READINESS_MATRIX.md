# Capability Readiness Matrix

This is an investor-facing summary of current engineering maturity, not a certification or deployment acceptance record.

| Capability | Current status | What can be stated | What must not be claimed yet |
|---|---|---|---|
| Local AI Router | Experimental foundation | Metadata-only local route selection and authorization-aware planning primitives exist. | No authenticated end-to-end PC1-to-PC5 execution or production deployment claim. |
| PC1–PC5 topology | Target architecture / experimental | Roles are documented as an intended distributed design. | No validated five-device school deployment or accepted worker enrollment. |
| Identity and authorization | Foundation / integration work | Internal security primitives and service foundations are present. | No complete browser-authenticated school application claim. |
| Local RAG | Candidate / experimental | Local retrieval and model-runtime experiments are part of the development direction. | No fully governed, production-approved ingestion pipeline claim. |
| Computer Vision | Experimental | A preserved engine measures luminance changes in image regions. | No validated occupancy, identity recognition, behavior interpretation, or reliable incident detection claim. |
| Temporal / Fall Detection | Research / experimental | Research direction and preserved prototypes exist. | No validated school safety alarm or field-accuracy claim. |
| Predictive Risk Intelligence | Planned research direction | Architecture contemplates cautious, human-reviewed risk indicators. | No proven prediction accuracy or reliable future-incident prediction claim. |
| Smart Wearable | Blocked | Prior design work exists. | Not a working production integration; no student biometric monitoring claim. |
| Complete School Application | Not yet accepted in V3 | V3 consolidates foundations and prototypes. | Do not present V3 as a complete, production-ready school platform. |
| CI validation | Not verified | Workflow attempts have encountered startup failures. | Do not claim green CI or passing repository-wide tests. |

## Evidence required to advance maturity

For each capability promoted to beta or production, record:
- exact source commit and scope;
- reproducible test command and successful logs;
- threat model and privacy review where applicable;
- hardware and dataset details for performance claims;
- field validation and human-review process for safety-related features;
- known limitations, failure modes, and rollback procedure.
