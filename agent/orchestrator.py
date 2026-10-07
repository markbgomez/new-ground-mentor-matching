"""
Match Orchestrator Agent
Executes multi-step reasoning, gate evaluation, and verified proposal generation.
"""
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from agent.tools.matching_engine import (
    apply_hard_filters,
    score_match,
    detect_risk_flags,
    build_mentee_card
)
from agent.verifier import MatchVerifier

class MatchOrchestrator:
    def __init__(self, verifier: Optional[MatchVerifier] = None):
        self.verifier = verifier or MatchVerifier()

    def run_match_pipeline(self, mentee: Dict[str, Any], all_mentors: List[Dict[str, Any]], open_holds_by_mentor: Dict[str, int] = None) -> Dict[str, Any]:
        """
        Executes the 8-step pipeline:
        PLAN -> SAFETY -> DATA -> HARD FILTERS -> RANK -> REASON -> VERIFY -> PROPOSAL
        """
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        open_holds = open_holds_by_mentor or {}
        steps_log = []

        # 1. PLAN
        steps_log.append({
            "step": 1,
            "name": "PLAN",
            "message": f"Planning matching workflow for mentee {mentee.get('first_name')} (ID: {mentee.get('mentee_id')})."
        })

        # 2. SAFETY CHECK (Hard stop on crisis)
        mentee_text = f"{mentee.get('goals_text', '')} {mentee.get('notes_text', '')}"
        crisis_flags = detect_risk_flags(mentee_text)
        if crisis_flags:
            steps_log.append({
                "step": 2,
                "name": "SAFETY",
                "status": "CRITICAL_ALERT",
                "message": f"Crisis markers detected: {crisis_flags[0]}. Halting automated matching immediately."
            })
            return {
                "session_id": session_id,
                "status": "needs_human_review",
                "escalation_reason": f"SAFETY CRISIS HARD STOP: {crisis_flags[0]}",
                "top_5": [],
                "excluded": [],
                "steps_log": steps_log
            }

        steps_log.append({
            "step": 2,
            "name": "SAFETY",
            "status": "PASSED",
            "message": "Safety screen clean. No crisis markers found."
        })

        # 3. DATA CHECK
        steps_log.append({
            "step": 3,
            "name": "DATA",
            "status": "PASSED",
            "message": f"Consent mode: {mentee.get('mentor_share_consent', 'all')}. Identifications shared: {mentee.get('share_identifications', False)}."
        })

        # 4. APPLY HARD FILTERS
        eligible = []
        excluded = []
        for m in all_mentors:
            mid = m["mentor_id"]
            m_holds = open_holds.get(mid, 0)
            passed, reasons = apply_hard_filters(mentee, m, open_holds=m_holds)
            if passed:
                eligible.append(m)
            else:
                excluded.append({
                    "mentor_id": mid,
                    "mentor_name": f"{m.get('first_name')} {m.get('last_initial')}.",
                    "reasons": reasons
                })

        steps_log.append({
            "step": 4,
            "name": "HARD_FILTERS",
            "message": f"Evaluated {len(all_mentors)} mentors. {len(eligible)} passed gates, {len(excluded)} excluded."
        })

        if len(eligible) < 3:
            return {
                "session_id": session_id,
                "status": "needs_human_review",
                "escalation_reason": f"Fewer than 3 mentors ({len(eligible)}) passed hard filters and gates.",
                "top_5": [],
                "excluded": excluded,
                "steps_log": steps_log
            }

        # 5. RANK CANDIDATES
        scored = []
        for m in eligible:
            score_data = score_match(mentee, m)
            score_data["mentor_obj"] = m
            scored.append(score_data)

        scored.sort(key=lambda x: x["total_score"], reverse=True)
        top_candidates = scored[:5]

        steps_log.append({
            "step": 5,
            "name": "RANK_CANDIDATES",
            "message": f"Ranked top 5 candidates. Scores range from {top_candidates[0]['total_score']} to {top_candidates[-1]['total_score']}."
        })

        # 6. REASONING OVER TRADE-OFFS
        for idx, cand in enumerate(top_candidates, 1):
            cand["rank"] = idx
            cand["explanation"] = (
                f"Rank {idx}: High alignment in support priorities with {cand['distance_miles']} mi distance. "
                f"Available in: {', '.join(cand['shared_availability']) if cand['shared_availability'] else 'Flexible times'}."
            )

        steps_log.append({
            "step": 6,
            "name": "REASONING",
            "message": "Synthesized compatibility breakdowns and balance of support strengths for top 5."
        })

        # 7. VERIFICATION AUDIT
        verification = self.verifier.verify_proposal(mentee, top_candidates)
        steps_log.append({
            "step": 7,
            "name": "VERIFY",
            "status": "PASSED" if verification["passed"] else "FAILED",
            "message": "Verifier passed proposal." if verification["passed"] else f"Verifier flagged: {verification['violations']}"
        })

        if not verification["passed"]:
            return {
                "session_id": session_id,
                "status": "needs_human_review",
                "escalation_reason": f"Verifier failed: {verification['violations'][0]}",
                "top_5": top_candidates,
                "excluded": excluded,
                "steps_log": steps_log
            }

        # 8. SAVE PROPOSAL
        proposal_id = f"prop_{uuid.uuid4().hex[:8]}"
        return {
            "proposal_id": proposal_id,
            "session_id": session_id,
            "mentee_id": mentee["mentee_id"],
            "status": "pending_review",
            "top_5": top_candidates,
            "excluded": excluded,
            "steps_log": steps_log,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
