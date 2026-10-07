# New Ground Match Agent — Project Context and Rules

You are helping build "New Ground Match Agent" for the Gloo AI Hackathon, Track 1: Agents of Flourishing.

## THE USER AND THE BURDEN
- Named user: the New Ground Program Coordinator at Project 1.27 (Aurora, Colorado), who matches volunteer mentors with young adults ages 18-24 transitioning out of foster care. Today this is done by hand from Mentor and Mentee Intake Questionnaires.

## END-TO-END WORKFLOW (the agent prepares; humans decide)
1. Coordinator enters/imports a mentee intake.
2. AGENT: safety screen -> data check/normalize -> hard filters -> score/rank -> reason -> verify -> save a proposal of the TOP 5 mentors (or escalate).
3. COORDINATOR: selects exactly 3 of the 5 to invite (fewer only with a written reason).
4. AGENT: drafts a "possible match" invitation email for each of the 3 mentors. Each contains the mentee profile built ONLY from mentee-consented fields, plus a single-use, expiring Accept/Decline link. The verifier checks each invitation for leakage.
5. COORDINATOR: reviews/edits and clicks "Approve & Send Mentor Invitations". This is the ONLY path that sends them. Invited mentors are placed on hold.
6. MENTORS: open their link, review the mentee profile, and Accept or Decline (with an optional private reason). Decline reasons are never shown to the mentee.
7. AGENT (follow-up): tracks responses. For each decline or expired invitation, it releases the hold and proposes a backfill from the remaining #4/#5 candidates (or a re-run if none remain). The coordinator approves any backfill invitation. Reminders to non-responding mentors are drafted for coordinator approval.
8. COORDINATOR: when all invitations are resolved (or earlier, once at least min_accepted_to_offer mentors have accepted), clicks "Prepare Mentee Offer".
9. AGENT: drafts the mentee offer email containing ONLY mentors who accepted (consented mentor fields + bio) and a single-use link. The verifier checks it.
10. COORDINATOR: clicks "Approve & Send to Mentee". This is the ONLY path that sends it.
11. MENTEE: chooses one mentor, or "None of these feel right" with an optional reason. Every option they see has already said yes, so they never face rejection.
12. COORDINATOR: confirms the match -> status "matched". The agent drafts (a) a confirmation to the chosen mentor and (b) a gracious "not selected this time" note to the other accepted mentors. The coordinator approves sending both. All holds are released.
13. FOLLOW-UP AGENT (daily, Cloud Scheduler): reminders, expirations, hold releases, backfills, and none-fit re-runs. It drafts only and never sends.

## CORE PRINCIPLE: MENTEE PREFERENCES COME FIRST
- Mentee must-have preferences are HARD FILTERS; other mentee preferences carry the highest weight.
- Mentor-side preferences about a mentee are low-weight tie-breakers (mentor gender preference is a hard filter only if config says so).
- Protective gates: comfort gate (mentee selected an area and mentor rated it 1-2 of 5 -> exclude; 3 -> concern; 4-5 -> bonus) and spiritual gate (mentor "Essential" + mentee "Prefer a non-spiritual focus" -> exclude).
- Mentor acceptance protects the mentee from rejection. The mentee only ever sees mentors who said yes.

## NON-NEGOTIABLE GUARDRAILS
- Synthetic data only, labeled synthetic.
- The agent prepares, ranks, explains, drafts, and routes. It cannot send anything, cannot invite, cannot create offers, cannot change statuses to invited/offer_sent/matched. Only coordinator UI actions (logged with IAP identity) do that.
- No counseling, diagnosis, or pastoral judgment.
- Never infer sensitive attributes. Mentee contact PII (name, DOB, email, phone, street address) is never sent to Gemini and never shown to mentors.
- Mentor invitations show ONLY mentee-consented fields. The mentee's sensitive self-disclosures (LGBTQ+, substance recovery, immigration, parenting, legal history, developmental) appear only if the mentee explicitly consented to share them with potential mentors. Mentee first name only.
- Mentee offers show ONLY accepted mentors and only mentor-consented fields (mentor intake Section 7). Never comfort ratings, mentor preferences, background-check status, last names, decline information, or how many mentors declined.
- Escalate (needs_human_review + reason) when: fewer than 3 mentors pass the hard filters; confidence is below threshold; data is missing/contradictory; crisis indicators appear; a must-have is unmet; the verifier fails twice; or fewer than min_accepted_to_offer mentors accept after backfills are exhausted.
- Every agent step is logged to BigQuery (agent_steps) for audit.

## GOOGLE CLOUD STACK (project new-ground-mentor-matching, number 672069369633)
- Agent: Google Agent Development Kit (ADK, Python) with Gemini on Vertex AI (google-genai SDK, vertexai=True, Application Default Credentials). Model IDs are config values: a Flash-class model for orchestrator, normalizer, writers, and follow-up; a Pro-class model for the verifier.
- Data: BigQuery dataset "new_ground" (location US). BigQuery GIS for distance; zip centroids from the BigQuery public dataset geo_us_boundaries.
- Hosting (us-central1):
  * coordinator-app (Cloud Run, FastAPI + UI + agents), protected by IAP.
  * response-portal (Cloud Run, public): serves single-use signed links for mentors (/m/{token}: accept/decline) and mentees (/o/{token}: choose).
- Coordinator access (IAP allow-list, exactly): mgomez@project127.org, adudrey@project127.org, akuykendall@project127.org (/config/access.yaml).
- Messaging: email via the Gmail API (scope gmail.send only), sent from mgomez@project127.org; refresh token in Secret Manager (gmail-sender-oauth). DEMO MODE ON BY DEFAULT: every email redirected to mgomez@project127.org with subject prefix "[DEMO → intended: {first name}, {mentor|mentee}]" and hard allow-list [mgomez@project127.org]. Fallback to simulated outbox with visible banner if auth missing.
- Secrets: Secret Manager. Scheduling: Cloud Scheduler -> Cloud Run job. Deploy: Cloud Build -> Artifact Registry -> Cloud Run.

## ENGINEERING RULES
- Deterministic logic (filters, distance, scoring, state transitions) lives in Python/SQL. Gemini orchestrates, normalizes free text, reasons over trade-offs, writes explanations and emails, and self-checks. Gemini never invents scores or changes state.
- Unit tests use BigQuery fakes; integration tests use dataset new_ground_dev.
- Maintain DECISIONS.md, PROMPTS.md, FAILURES.md, COSTS.md.
- Never hardcode secrets; never log tokens, signed URLs, or email addresses of mentees/mentors.

## BRAND (Project 1.27)
- Colors: --p127-red (#ec1847), --p127-red-dark (#ac1234), --p127-slate (#333745), --p127-blue (#00aeef), --p127-blue-dark (#009fda), --p127-green (#82c341), --p127-sky (#e1eff5), --p127-ink (#2a2a2a).
- Montserrat for headings, Open Sans for body. Square corners. WCAG AA contrast everywhere.
