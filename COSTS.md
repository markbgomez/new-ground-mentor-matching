# Cost Breakdown & Pricing Links

Estimates based on Google Cloud US-central1 official pricing (no fabricated figures).

### 1. Compute & Hosting: Cloud Run (fully managed serverless)
- **Coordinator App & Response Portal**:
  - Cloud Run free tier provides 2 million requests/month, 360,000 vCPU-seconds, and 180 GiB-seconds of memory.
  - Typical demonstration / low-volume non-profit workload stays well within the free tier.
  - [Cloud Run Pricing](https://cloud.google.com/run/pricing)

### 2. Data Warehouse: BigQuery
- **Storage**:
  - Active storage: $0.02 per GB per month (first 10 GB/month free).
- **Queries**:
  - On-demand analysis: $6.25 per TB (first 1 TB/month free).
  - Given queries scan < 10 MB per match evaluation, cost is effectively $0.00 / month.
  - [BigQuery Pricing](https://cloud.google.com/bigquery/pricing)

### 3. AI & LLM: Vertex AI (Gemini 2.5 Flash & Pro)
- **Gemini 2.5 Flash** (Orchestrator, Normalizer, Writers, Follow-up):
  - Input: ~$0.075 per 1M tokens (prompts under 128k)
  - Output: ~$0.30 per 1M tokens
  - Cost per full match cycle: ~0.0003 USD.
- **Gemini 2.5 Pro** (Verifier):
  - Input: ~$1.25 per 1M tokens
  - Output: ~$5.00 per 1M tokens
  - Cost per verifier run: ~0.0025 USD.
  - [Vertex AI Pricing](https://cloud.google.com/vertex-ai/pricing)

### 4. Ancillary Services
- **Secret Manager**:
  - 6 active secret versions free / month; $0.06 per additional 10k operations.
  - [Secret Manager Pricing](https://cloud.google.com/secret-manager/pricing)
- **Cloud Scheduler**:
  - 3 free jobs per Google Cloud billing account / month.
  - [Cloud Scheduler Pricing](https://cloud.google.com/scheduler/pricing)
- **Gmail API**:
  - Free quota within Google Workspace / standard API daily quotas.

### Summary
Monthly operational cost for development and demo operation: **< $1.00 USD / month**.
