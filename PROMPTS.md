# System Prompts Changelog & Versioning

### Orchestrator Prompt (v1)
- Model: `gemini-2.5-flash`
- File: `/agent/prompts/orchestrator_v1.md`
- Role: Deterministic step planning, safety screening, hard filtering coordination, multi-factor ranking, transparent trade-off reasoning.
- Notes: Requires human-in-the-loop review for all final selections.

### Verifier Prompt (v1)
- Model: `gemini-2.5-pro`
- File: `/agent/prompts/verifier_v1.md`
- Role: Independent privacy & safety auditor. Validates proposals and outgoing invitation/offer drafts against strict consent rules and exclusion boundaries.
- Notes: Evaluates without access to restricted contact PII.

### Invite Writer Prompt (v1)
- Model: `gemini-2.5-flash`
- File: `/agent/prompts/invite_writer_v1.md`
- Role: Drafts warm, dignified, low-pressure invitations to prospective mentors using only consented profile details.

### Offer Writer Prompt (v1)
- Model: `gemini-2.5-flash`
- File: `/agent/prompts/offer_writer_v1.md`
- Role: Plain-language, empowering presentation of accepted mentors to the mentee (6th-8th grade reading level).

### Follow-up Agent Prompt (v1)
- Model: `gemini-2.5-flash`
- File: `/agent/prompts/follow_up_v1.md`
- Role: Evaluates reminder schedules, invitation expirations, hold releases, and backfill recommendations.
