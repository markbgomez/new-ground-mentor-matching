# Architecture & Implementation Decisions

1. **Two-Tier Review Workflow (v4 Upgrade)**:
   - Mentors review mentee profile and accept/decline FIRST before mentee is presented choices.
   - Mentee only ever sees mentors who have already enthusiastically said "Yes", guaranteeing that the young adult transitioning from foster care never experiences rejection.
   - Declines from initial 3 selections trigger automated backfill proposals from ranked candidates #4/#5 for coordinator approval.

2. **Strict Separation of Agent Reasoning and Mutation**:
   - `/agent` code is strictly analytical, explanatory, and drafting-only.
   - No agent module has the authority to transition database status or send emails.
   - All state transitions and communications are initiated exclusively by authenticated human coordinators through `/app/actions/*.py`.

3. **Restricted Contact Tables & PII Shielding**:
   - `mentor_contact` and `mentee_contact` tables are physically quarantined.
   - Gemini models and public portals never receive contact information (phone, street address, personal email, mentee last name).
   - Only mentee first name and consented fields are exposed in invitation cards.

4. **Consent-Gated Data Exposure (Intake Section 6 & 7)**:
   - Mentee Section 6: "all", "selected", "none", or "not_asked" (legacy defaults).
   - Sensitive self-disclosures (LGBTQ+, substance recovery, immigration, parenting, legal history, developmental) require an explicit secondary opt-in `share_identifications=true`. "all" does NOT include them by default.

5. **Demo Mode Safety & Outbox Routing**:
   - `demo_mode=true` redirects all communications to `mgomez@project127.org` with clear visual prefixes: `[DEMO → intended: {first name}, {mentor|mentee}]`.
   - Hardcoded recipient allow-list ensures accidental leaks to real emails are impossible.
   - In case of missing/expired Gmail tokens, system seamlessly falls back to simulated in-memory/DB outbox.

6. **Identity-Aware Proxy (IAP) on Cloud Run**:
   - Protected endpoints on coordinator service inspect `X-Goog-Authenticated-User-Email` and verify against `config/access.yaml`.
   - Response portal runs publicly without authentication using cryptographically signed single-use HMAC tokens.
