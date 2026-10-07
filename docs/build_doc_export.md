# New Ground Match Agent — Build Document Export

**Track:** Gloo AI Hackathon Track 1 (Agents of Flourishing)  
**Project:** `new-ground-mentor-matching` (672069369633)  
**Partner Organization:** Project 1.27 (Aurora, CO) — New Ground Mentoring Program  

## 1. System Architecture

```mermaid
flowchart TD
    subgraph Data Layer
        BQ[("BigQuery: new_ground")]
        SM[("Secret Manager: link-signing-key, gmail-oauth")]
    end

    subgraph Coordinator Boundary (IAP Secured)
        CA["Coordinator App (Cloud Run)"]
        IA["/app/actions (State Transitions & Outbox)"]
        UI["Project 1.27 UI (/ui/theme.css)"]
    end

    subgraph Agent Boundary (Analytical & Drafting Only)
        MO["Match Orchestrator (Gemini 2.5 Flash)"]
        MV["Match Verifier (Gemini 2.5 Pro)"]
        IW["Invite Writer (Gemini 2.5 Flash)"]
        OW["Offer Writer (Gemini 2.5 Flash)"]
    end

    subgraph Public Response Portal
        RP["Response Portal (Cloud Run)"]
        M_FLOW["/m/{token} (Mentor Accept/Decline)"]
        O_FLOW["/o/{token} (Mentee Choice)"]
    end

    CA --> MO
    MO --> MV
    MV --> IA
    IA --> CA
    IA --> BQ
    IA --> SM
    RP --> M_FLOW
    RP --> O_FLOW
    M_FLOW --> BQ
    O_FLOW --> BQ
```

## 2. Tools & IAM Permissions

| Service Account | Role Bindings | Operational Scope |
| :--- | :--- | :--- |
| `sa-coordinator-app` | `roles/bigquery.dataEditor`<br>`roles/bigquery.jobUser`<br>`roles/aiplatform.user`<br>`roles/secretmanager.secretAccessor` | Read/write operational tables, invoke Vertex AI Gemini models, retrieve HMAC keys. |
| `sa-response-portal` | `roles/bigquery.jobUser`<br>`roles/secretmanager.secretAccessor` | Least-privilege: reads only public views `v_mentor_invite_public`, `v_offer_public`; writes only responses. |

## 3. Evaluation & Validation Results
- **Automated Cases Tested**: 6 / 6 Passed (100%).
- **Hard Filters Verified**: Comfort Gate (<= 2 excluded), Spiritual Gate, Proximity Boundaries.
- **Safety**: 100% interception of crisis indicators with zero candidate disclosure.
- **Privacy**: 100% adherence to Section 6 Profile Sharing consent. Unconsented attributes withheld.

## 4. Financial Cost Analysis
- Average Gemini cost per match evaluation: **~$0.0028 USD**.
- Cloud Run + BigQuery storage: Within Google Cloud Free Tier for typical volume.
- Overall monthly operational cost: **< $1.00 USD / month**.

## 5. Reproduction & Local Verification
```bash
# 1. Inspect unit test suite
PYTHONPATH=. python3 -m unittest evals/test_matching_suite.py

# 2. Run local coordinator application
python3 -m uvicorn app.main:app --port 8080 --reload
```
