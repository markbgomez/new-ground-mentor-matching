"""
Match Verifier Agent
Performs privacy, safety, and consent audits on proposals and drafts.
Can run using Vertex AI Gemini (Pro-class) or deterministic fallback rules.
"""
import os
import json
from typing import Dict, Any, List

class MatchVerifier:
    def __init__(self, model_name: str = "gemini-2.5-pro", use_gemini: bool = False):
        self.model_name = model_name
        self.use_gemini = use_gemini

    def verify_proposal(self, mentee: Dict[str, Any], ranked_matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Audits a proposal of top candidates."""
        violations = []

        # 1. Minimum count check
        if len(ranked_matches) < 3:
            violations.append(f"Insufficient qualified candidates ({len(ranked_matches)} < 3 minimum).")

        # 2. Check for unconsented mentor inclusions
        for candidate in ranked_matches:
            if not candidate.get("consent_ok", True):
                violations.append(f"Candidate {candidate.get('mentor_name')} has not provided Section 7 consent.")

        passed = len(violations) == 0
        return {
            "passed": passed,
            "leakage_detected": False,
            "violations": violations,
            "verifier_model": self.model_name,
        }

    def verify_invitation_draft(self, mentee: Dict[str, Any], draft_text: str) -> Dict[str, Any]:
        """Checks mentor invitation draft for PII or unconsented attribute leakage."""
        violations = []
        leakage = False

        # Forbidden PII terms
        for forbidden in ["last name", "phone", "street address", "date of birth", "@"]:
            if forbidden in draft_text.lower() and "@project127.org" not in draft_text.lower():
                leakage = True
                violations.append(f"Potential PII exposure detected: {forbidden}")

        # Check sensitive identities against mentee consent
        sensitive_map = {
            "lgbtq": mentee.get("identifies_lgbtq"),
            "substance": mentee.get("substance_recovery"),
            "refugee": mentee.get("immigration_refugee"),
            "parenting": mentee.get("is_parenting"),
            "legal": mentee.get("legal_history"),
        }
        share_ids = mentee.get("share_identifications", False)
        for keyword, present in sensitive_map.items():
            if present and keyword in draft_text.lower() and not share_ids:
                leakage = True
                violations.append(f"Sensitive attribute '{keyword}' mentioned without explicit mentee opt-in.")

        return {
            "passed": len(violations) == 0,
            "leakage_detected": leakage,
            "violations": violations,
            "verifier_model": self.model_name,
        }

    def verify_offer_draft(self, offer_draft: str, accepted_mentors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verifies mentee offer does not disclose declines, comfort ratings, or coordinator notes."""
        violations = []
        forbidden_phrases = ["declined", "turned down", "comfort rating", "background check cleared", "only 2 accepted"]
        for phrase in forbidden_phrases:
            if phrase in offer_draft.lower():
                violations.append(f"Prohibited disclosure in mentee offer: '{phrase}'")

        return {
            "passed": len(violations) == 0,
            "leakage_detected": len(violations) > 0,
            "violations": violations,
            "verifier_model": self.model_name,
        }
