# Failure Modes and Mitigations

| Failure Mode | Trigger / Scenario | Automated Mitigation / System Response |
| :--- | :--- | :--- |
| **Insufficient Candidates** | < 3 mentors pass hard filters | Orchestrator halts; escalates to `needs_human_review` with specific filter bottlenecks identified. |
| **Data Leakage in Invitation** | Non-consented mentee fields or PII in draft | Pro-class verifier checks draft against `mentor_share_fields`; rejects draft (up to 2 retry loops). |
| **Offer Leakage** | Draft contains decline count or mentor preferences | Verifier blocks offer email; replaces with sanitized plain-language template. |
| **Unapproved Mutation Attempt** | Agent code attempts to transition state or send email | Architecture forbids agent writes to operational tables; throws runtime error; logged to `agent_steps`. |
| **Token Tampering / Reuse** | Altered token or repeated submission on portal | Portal HMAC verification fails; displays expired/invalid security notice; no response written. |
| **Gmail OAuth Token Expiry** | 7-day expiration in GCP Testing mode | App detects missing/expired refresh token; gracefully falls back to simulated outbox with visible UI warning banner. |
| **Crisis Detection** | Mentee text contains suicide/harm indicators | Hard stop before filtering; immediately triggers escalation `needs_human_review` with crisis intervention notes. |
