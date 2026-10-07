# New Ground Match Agent

**Gloo AI Hackathon · Track 1: Agents of Flourishing**  
**Partner Organization:** Project 1.27 (Aurora, Colorado)  
**Google Cloud Project:** `new-ground-mentor-matching` (Project Number: `672069369633`)

The **New Ground Match Agent** assists the New Ground Program Coordinator at Project 1.27 in matching volunteer adult mentors with young adults (ages 18–24) transitioning out of foster care.

---

## Key Innovations

1. **Two-Tier Volunteer Review (Agency Without Rejection)**:
   - Mentors review the mentee profile and **accept or decline first**.
   - Only mentors who have already enthusiastically agreed are presented to the young adult.
   - The mentee chooses their mentor on a mobile-friendly portal, knowing every candidate has already said yes.
2. **Strict Human-in-the-Loop Architecture**:
   - The AI agent performs safety screening, data normalization, hard filtering, multi-factor ranking, and draft generation.
   - The agent **cannot** send emails, invite candidates, create offers, or transition statuses. Only authenticated coordinators can trigger actions.
3. **Privacy & Consent Boundaries**:
   - Contact tables (`mentor_contact`, `mentee_contact`) are completely quarantined and never accessible to Gemini.
   - Mentee self-disclosures (LGBTQ+, recovery, immigration, parenting, legal history, developmental) are governed by strict Section 6 consent.
4. **Demo Mode Safety**:
   - All outgoing communications in demo mode are redirected to `mgomez@project127.org` with visual role tags.

---

## Directory Structure

```
├── app/                  # Coordinator FastAPI service + UI templates
├── portal/               # Public Response Portal for single-use mentor/mentee links
├── agent/                # ADK matching engine, tools, verifier, writers, prompts
│   ├── tools/            # Deterministic distance, filtering, and scoring logic
│   └── prompts/          # Versioned Gemini prompts
├── bq/                   # BigQuery schema, views, and synthetic data generator
├── ui/                   # Project 1.27 brand stylesheets (theme.css, components.css)
├── infra/                # GCP setup, deployment, authorization, and teardown scripts
├── evals/                # Automated evaluation suite and results
├── docs/                 # Build documentation (agent_build_document.md), intake mapping, brand guide
└── config/               # Matching weights, access allow-list, messaging settings
```

---

## Documentation

- [**Agent Build Document**](docs/agent_build_document.md) — Comprehensive hackathon build document covering the user burden, architecture, verbatim prompts, GCP stack & lifecycle costs, security/permissions, 7-scenario evaluation suite, and full reproduction instructions.
- [**Intake Mapping Matrix**](docs/intake_mapping.md) — Mentor and mentee questionnaire fields and scoring weights.

---

## Quickstart

### 1. Run the Evaluation Suite
```bash
PYTHONPATH=. python3 -m unittest evals/test_matching_suite.py
```

### 2. Run the Coordinator App & Response Portal
```bash
uvicorn app.main:app --port 8080 --reload
```
Open [http://localhost:8080](http://localhost:8080) to access the coordinator pipeline.

### 3. Deploy to Google Cloud Run
See `infra/MANUAL_STEPS.md` for pre-requisite OAuth console setup, then execute:
```bash
bash infra/setup.sh
bash infra/deploy.sh
```
