"""
Evaluation Suite & Automated Test Runner (unittest)
Tests match algorithms, guardrails, comfort/spiritual gates, PII quarantine, and leakage prevention.
"""
import unittest
from app.state import AppState
from agent.tools.matching_engine import apply_hard_filters, score_match, detect_risk_flags, build_mentee_card
from agent.verifier import MatchVerifier
from portal.tokens import generate_signed_token, verify_signed_token

class TestMatchingSuite(unittest.TestCase):

    def test_crisis_hard_stop(self):
        """Validates that crisis indicators trigger an immediate hard halt."""
        state = AppState()
        result = state.run_matching("demo_crisis", "coordinator@project127.org")
        self.assertEqual(result["status"], "needs_human_review")
        self.assertIn("CRISIS", result["escalation_reason"])
        self.assertEqual(len(result["top_5"]), 0)

    def test_comfort_gate_exclusion(self):
        """Validates that mentor comfort rating <= 2 triggers hard exclusion."""
        mentee = {
            "mentee_id": "test_m1",
            "zip": "80010",
            "identifies_lgbtq": True,
            "spiritual_alignment": "Open",
            "open_to_virtual": True
        }
        # Mentor rating 2 -> MUST BE EXCLUDED
        mentor_rating_2 = {
            "mentor_id": "m_test_2",
            "zip": "80010",
            "status": "active",
            "background_check_cleared": True,
            "training_completed": True,
            "profile_share_consent": "all",
            "comfort_lgbtq": 2,
            "max_travel_bucket": "10_to_20"
        }
        passed_2, reasons_2 = apply_hard_filters(mentee, mentor_rating_2)
        self.assertFalse(passed_2)
        self.assertTrue(any("Comfort Gate" in r for r in reasons_2))

        # Mentor rating 3 -> PASSES (with potential concern note)
        mentor_rating_3 = mentor_rating_2.copy()
        mentor_rating_3["comfort_lgbtq"] = 3
        passed_3, _ = apply_hard_filters(mentee, mentor_rating_3)
        self.assertTrue(passed_3)

    def test_spiritual_gate_exclusion(self):
        """Validates that Essential spiritual mentor + non-spiritual mentee is excluded."""
        mentee = {
            "mentee_id": "test_m2",
            "zip": "80010",
            "spiritual_alignment": "Prefer a non-spiritual focus",
            "open_to_virtual": True
        }
        mentor = {
            "mentor_id": "m_test_sp",
            "zip": "80010",
            "status": "active",
            "background_check_cleared": True,
            "training_completed": True,
            "profile_share_consent": "all",
            "spiritual_conversation_importance": "Essential",
            "max_travel_bucket": "10_to_20"
        }
        passed, reasons = apply_hard_filters(mentee, mentor)
        self.assertFalse(passed)
        self.assertTrue(any("Spiritual Gate" in r for r in reasons))

    def test_mentee_card_consent_suppression(self):
        """Validates that unconsented sensitive attributes are never exposed."""
        mentee = {
            "first_name": "Jordan",
            "last_initial": "K",
            "age": 20,
            "city": "Denver",
            "identifies_lgbtq": True,
            "mentor_share_consent": "selected",
            "mentor_share_fields": ["first_name", "city"],
            "share_identifications": False # Did NOT opt in to share sensitive identity
        }
        card = build_mentee_card(mentee)
        self.assertNotIn("consented_identifications", card)
        self.assertEqual(card["first_name"], "Jordan")
        self.assertNotIn("last_initial", card)

    def test_token_tampering_rejection(self):
        """Validates cryptographic signature verification on single-use portal tokens."""
        token = generate_signed_token({"invitation_id": "inv_123"})
        # Valid token passes
        payload = verify_signed_token(token)
        self.assertEqual(payload["invitation_id"], "inv_123")

        # Tampered token fails
        tampered = token[:-4] + "AAAA"
        with self.assertRaises(ValueError):
            verify_signed_token(tampered)

    def test_full_happy_path_workflow(self):
        """Validates complete matching lifecycle from intake to match."""
        state = AppState()
        # 1. Match
        match_res = state.run_matching("demo_happy", "mgomez@project127.org")
        self.assertEqual(match_res["status"], "pending_review")
        self.assertEqual(len(match_res["top_5"]), 5)
        prop_id = match_res["proposal_id"]

        # 2. Select 3
        sel = state.select_3_mentors(prop_id, [c["mentor_id"] for c in match_res["top_5"][:3]], "mgomez@project127.org")
        self.assertEqual(len(sel["drafts"]), 3)

        # 3. Approve and send
        outbox_msgs = state.approve_and_send_invitations(sel["selection_id"], "mgomez@project127.org")
        self.assertEqual(len(outbox_msgs), 3)
        self.assertTrue(all(m["delivered_to"] == "mgomez@project127.org" for m in outbox_msgs))

        # 4. Mentors accept
        inv_ids = [d["invitation_id"] for d in sel["drafts"]]
        state.record_mentor_response(inv_ids[0], "accept")
        state.record_mentor_response(inv_ids[1], "accept")

        # 5. Prepare offer
        offer = state.prepare_mentee_offer("demo_happy", "mgomez@project127.org")
        self.assertEqual(len(offer["mentor_cards"]), 2)

        # 6. Approve and send offer
        state.approve_and_send_offer(offer["offer_id"], "mgomez@project127.org")

        # 7. Mentee chooses
        chosen_id = offer["accepted_mentor_ids"][0]
        state.record_offer_response(offer["offer_id"], "chose_mentor", chosen_mentor_id=chosen_id)

        # 8. Confirm match
        match_rec = state.confirm_match("demo_happy", chosen_id, "mgomez@project127.org")
        self.assertEqual(match_rec["mentee_id"], "demo_happy")
        self.assertEqual(state.mentees["demo_happy"]["status"], "matched")

    def test_portal_preview_and_mentee_simulation(self):
        """Validates /portal-preview/{mentee_id} redirection and mentee simulation flow."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.state import app_state

        client = TestClient(app)

        # 1. Before offer exists: should return 404 with clear detail
        res = client.get("/portal-preview/demo_happy", follow_redirects=False)
        self.assertEqual(res.status_code, 404)
        self.assertIn("No active offer found", res.json()["detail"])

        # 2. Advance demo_happy through selection and invitations to offer_sent
        match_res = app_state.run_matching("demo_happy", "mgomez@project127.org")
        prop_id = match_res["proposal_id"]
        sel_mentors = [m["mentor_id"] for m in match_res["top_5"][:3]]
        sel = app_state.select_3_mentors(prop_id, sel_mentors, "mgomez@project127.org")
        app_state.approve_and_send_invitations(sel["selection_id"], "mgomez@project127.org")

        # Two mentors accept
        inv_ids = [d["invitation_id"] for d in sel["drafts"]]
        app_state.record_mentor_response(inv_ids[0], "accept")
        app_state.record_mentor_response(inv_ids[1], "accept")

        # Prepare and approve offer
        offer = app_state.prepare_mentee_offer("demo_happy", "mgomez@project127.org")
        app_state.approve_and_send_offer(offer["offer_id"], "mgomez@project127.org")

        # 3. /portal-preview/demo_happy should redirect (303) to /o/{token}
        res_preview = client.get("/portal-preview/demo_happy", follow_redirects=False)
        self.assertEqual(res_preview.status_code, 303)
        portal_url = res_preview.headers["location"]
        self.assertTrue(portal_url.startswith("/o/"))

        # 4. Visiting portal URL should render mentee view successfully
        res_portal = client.get(portal_url)
        self.assertEqual(res_portal.status_code, 200)
        self.assertIn("Your Potential Mentors", res_portal.text)

        # 5. Mentee submits choice via /o/respond
        token = portal_url.replace("/o/", "")
        chosen_id = offer["accepted_mentor_ids"][0]
        res_submit = client.post("/o/respond", data={"token": token, "chosen_mentor_id": chosen_id})
        self.assertEqual(res_submit.status_code, 200)
        self.assertIn("Choice Confirmed!", res_submit.text)
        self.assertIn("Return to Coordinator Pipeline", res_submit.text)

        # 6. Mentee state is now mentee_selected
        self.assertEqual(app_state.mentees["demo_happy"]["status"], "mentee_selected")

if __name__ == "__main__":
    unittest.main()

