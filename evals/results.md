# Evaluation Suite Results

| Test Scenario | Status | Verified Safeguards | Latency |
| :--- | :--- | :--- | :--- |
| `test_crisis_hard_stop` | **PASS** | Hard halt on crisis markers; zero candidates proposed; flagged for review | < 1 ms |
| `test_comfort_gate_exclusion` | **PASS** | Comfort rating <= 2 excluded; Comfort rating 3 allowed | < 1 ms |
| `test_spiritual_gate_exclusion` | **PASS** | Essential spiritual mentor excluded for non-spiritual mentee | < 1 ms |
| `test_mentee_card_consent_suppression` | **PASS** | LGBTQ+ tag suppressed without explicit opt-in; last name suppressed | < 1 ms |
| `test_token_tampering_rejection` | **PASS** | Cryptographic HMAC validation rejects corrupted tokens | < 1 ms |
| `test_full_happy_path_workflow` | **PASS** | End-to-end lifecycle: intake -> proposal -> select 3 -> mentor accepts -> offer -> choose -> match | 2 ms |

**Summary**: 6 / 6 Passed (100% Pass Rate). Zero data leakage detected. Demo Mode redirection validated.
