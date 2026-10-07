# System Guardrails Specification

### 1. Human-in-the-Loop Governance
- The AI Agent (`/agent`) operates strictly in an advisory, analytical, and drafting capacity.
- **No Agent Mutations**: Agent code possesses zero database write privileges for operational state tables and cannot trigger messaging.
- **Exclusive Human Path**: State transitions to `sent`, `offer_sent`, and `matched` occur exclusively via coordinator actions in `/app/actions/*.py` under authenticated IAP sessions.

### 2. Privacy & PII Quarantine
- **Isolated Contact Tables**: `mentor_contact` and `mentee_contact` tables (holding phone numbers, physical addresses, dates of birth, and mentee last names) are strictly quarantined and never referenced in agent prompts or Gemini API calls.
- **First Name Only**: Mentee and mentor initial representations are restricted to first name and last initial.

### 3. Consent-Driven Data Boundaries (Intake Section 6 & 7)
- **Mentee Profile Sharing**:
  - `all`: Shares basic demographics (first name, age, city, general goals, schedule) but **excludes** sensitive identifications by default.
  - `selected`: Shares strictly the checked field subset.
  - `none`: Suppresses all personal details; provides only high-level summary goals.
  - `not_asked` (legacy): Safe defaults applied with visual badge.
- **Explicit Sensitive Opt-In**: Identifications (LGBTQ+, substance recovery, immigration, parenting, legal history, developmental) require `share_identifications=true`.
- **Offer Boundary**: Mentee offers feature ONLY mentors who have already accepted. Never reveals decline statistics, comfort scores, or background check status.

### 4. Demo Messaging Safety Shield
- **Universal Redirect**: Every email (invitation, reminder, offer, confirmation) is forcibly redirected to `mgomez@project127.org`.
- **Recipient Allow-List**: Any attempt to dispatch to an unapproved address is intercepted and blocked.
- **Visual Prepend**: Subject lines and email bodies are explicitly tagged with `[DEMO → intended: {first name}, {mentor|mentee}]`.

### 5. Access Control
- Identity-Aware Proxy (IAP) validates Google Workspace identity against `config/access.yaml`. Unauthorized users receive HTTP 403.

### 6. Crisis & Safety Interception
- Pre-screening filter executes before matching logic.
- Presence of self-harm or crisis terminology triggers an immediate hard halt, marks the case `needs_human_review`, and blocks automated matching.
