"""
Application State & Storage Repository
Supports both in-memory local state (with synthetic data preloaded)
and BigQuery integration for cloud operation.
"""
import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from agent.tools.matching_engine import build_mentee_card, build_mentor_card
from agent.orchestrator import MatchOrchestrator
from agent.verifier import MatchVerifier
from agent.invite_writer import InviteWriter
from agent.offer_writer import OfferWriter
from portal.tokens import generate_signed_token

class AppState:
    def __init__(self):
        self.mentees: Dict[str, Dict[str, Any]] = {}
        self.mentors: Dict[str, Dict[str, Any]] = {}
        self.proposals: Dict[str, Dict[str, Any]] = {}
        self.selections: Dict[str, Dict[str, Any]] = {}
        self.invitations: Dict[str, Dict[str, Any]] = {}
        self.mentor_responses: Dict[str, Dict[str, Any]] = {}
        self.offers: Dict[str, Dict[str, Any]] = {}
        self.offer_responses: Dict[str, Dict[str, Any]] = {}
        self.matches: Dict[str, Dict[str, Any]] = {}
        self.mentor_holds: Dict[str, Dict[str, Any]] = {} # mentor_id -> {invitation_id, created_at}
        self.coordinator_actions: List[Dict[str, Any]] = []
        self.outbox: List[Dict[str, Any]] = []

        self.orchestrator = MatchOrchestrator()
        self.verifier = MatchVerifier()
        self.invite_writer = InviteWriter()
        self.offer_writer = OfferWriter()

        self.load_initial_data()

    def load_initial_data(self):
        json_path = os.path.join(os.path.dirname(__file__), "..", "bq", "synthetic_data.json")
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                data = json.load(f)
                for m in data.get("mentors", []):
                    self.mentors[m["mentor_id"]] = m
                for m in data.get("mentees", []):
                    self.mentees[m["mentee_id"]] = m

    def record_action(self, actor: str, action: str, entity_id: str, details: Dict[str, Any]):
        act = {
            "action_id": f"act_{uuid.uuid4().hex[:8]}",
            "ts": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "action": action,
            "entity_id": entity_id,
            "details": details
        }
        self.coordinator_actions.append(act)
        return act

    def run_matching(self, mentee_id: str, actor: str) -> Dict[str, Any]:
        mentee = self.mentees.get(mentee_id)
        if not mentee:
            raise ValueError(f"Mentee {mentee_id} not found")

        open_holds = {m_id: 1 for m_id in self.mentor_holds.keys()}
        result = self.orchestrator.run_match_pipeline(mentee, list(self.mentors.values()), open_holds)

        if result.get("proposal_id"):
            self.proposals[result["proposal_id"]] = result
            mentee["status"] = "proposed"
            self.record_action(actor, "run_matching", result["proposal_id"], {"status": result["status"]})
        else:
            mentee["status"] = "needs_review"
            self.record_action(actor, "run_matching_escalated", mentee_id, {"reason": result.get("escalation_reason")})

        return result

    def select_3_mentors(self, proposal_id: str, mentor_ids: List[str], actor: str, override_reason: Optional[str] = None) -> Dict[str, Any]:
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        mentee_id = proposal["mentee_id"]
        mentee = self.mentees[mentee_id]
        selection_id = f"sel_{uuid.uuid4().hex[:8]}"

        drafts = []
        for rank, m_id in enumerate(mentor_ids, 1):
            mentor = self.mentors[m_id]
            inv_id = f"inv_{uuid.uuid4().hex[:8]}"
            token = generate_signed_token({"invitation_id": inv_id, "mentor_id": m_id, "mentee_id": mentee_id})
            portal_url = f"/m/{token}"

            m_card = build_mentee_card(mentee)
            draft = self.invite_writer.draft_invitation(mentor, m_card, {}, portal_url)

            # Verification check
            ver_res = self.verifier.verify_invitation_draft(mentee, draft["body"])

            invitation_record = {
                "invitation_id": inv_id,
                "selection_id": selection_id,
                "mentee_id": mentee_id,
                "mentor_id": m_id,
                "mentor_name": f"{mentor['first_name']} {mentor['last_initial']}.",
                "rank": rank,
                "subject": draft["subject"],
                "body": draft["body"],
                "token": token,
                "portal_url": portal_url,
                "verifier_passed": ver_res["passed"],
                "status": "draft",
            }
            self.invitations[inv_id] = invitation_record
            drafts.append(invitation_record)

        self.selections[selection_id] = {
            "selection_id": selection_id,
            "proposal_id": proposal_id,
            "mentee_id": mentee_id,
            "mentor_ids": mentor_ids,
            "drafts": drafts,
            "selected_by": actor,
        }
        self.record_action(actor, "select_3", selection_id, {"mentor_ids": mentor_ids})
        return self.selections[selection_id]

    def approve_and_send_invitations(self, selection_id: str, actor: str) -> List[Dict[str, Any]]:
        selection = self.selections.get(selection_id)
        if not selection:
            raise ValueError(f"Selection {selection_id} not found")

        mentee = self.mentees[selection["mentee_id"]]
        sent_messages = []

        for inv in selection["drafts"]:
            inv_id = inv["invitation_id"]
            mentor_id = inv["mentor_id"]
            mentor = self.mentors[mentor_id]

            inv["status"] = "sent"
            inv["approved_by"] = actor
            inv["sent_at"] = datetime.now(timezone.utc).isoformat()

            # Place mentor on hold
            self.mentor_holds[mentor_id] = {"invitation_id": inv_id, "created_at": inv["sent_at"]}

            # Demo redirect routing
            msg = {
                "message_id": f"msg_{uuid.uuid4().hex[:8]}",
                "kind": "mentor_invite",
                "intended_role": "mentor",
                "intended_first_name": mentor["first_name"],
                "delivered_to": "mgomez@project127.org", # Hardcoded safety redirect
                "subject": f"[DEMO → intended: {mentor['first_name']}, mentor] {inv['subject']}",
                "body": inv["body"],
                "approved_by": actor,
                "sent_at": inv["sent_at"],
                "delivery_mode": "gmail (demo redirect)",
                "gmail_message_id": f"g_mock_{uuid.uuid4().hex[:6]}"
            }
            self.outbox.append(msg)
            sent_messages.append(msg)

        mentee["status"] = "mentor_review"
        self.record_action(actor, "approve_send_invites", selection_id, {"invitations_count": len(sent_messages)})
        return sent_messages

    def record_mentor_response(self, invitation_id: str, response: str, decline_reason: Optional[str] = None):
        inv = self.invitations.get(invitation_id)
        if not inv:
            raise ValueError("Invitation not found")
        if inv["status"] in ["accepted", "declined"]:
            raise ValueError("Response already submitted")

        inv["status"] = "accepted" if response == "accept" else "declined"
        inv["decline_reason_private"] = decline_reason
        inv["responded_at"] = datetime.now(timezone.utc).isoformat()

        self.mentor_responses[invitation_id] = {
            "invitation_id": invitation_id,
            "response": response,
            "decline_reason": decline_reason,
            "responded_at": inv["responded_at"]
        }

        # If declined, release hold
        if response == "decline":
            if inv["mentor_id"] in self.mentor_holds:
                del self.mentor_holds[inv["mentor_id"]]

        # Check if mentee is ready to offer
        mentee = self.mentees[inv["mentee_id"]]
        sel = self.selections[inv["selection_id"]]
        accepted_count = sum(1 for item in sel["drafts"] if self.invitations[item["invitation_id"]]["status"] == "accepted")
        if accepted_count >= 2:
            mentee["status"] = "ready_to_offer"

    def prepare_mentee_offer(self, mentee_id: str, actor: str) -> Dict[str, Any]:
        mentee = self.mentees.get(mentee_id)
        # Find all accepted mentors for this mentee
        accepted_mentors = []
        for inv in self.invitations.values():
            if inv["mentee_id"] == mentee_id and inv["status"] == "accepted":
                mentor = self.mentors[inv["mentor_id"]]
                accepted_mentors.append(mentor)

        if len(accepted_mentors) < 2:
            raise ValueError(f"Need at least 2 accepted mentors (current: {len(accepted_mentors)})")

        offer_id = f"off_{uuid.uuid4().hex[:8]}"
        token = generate_signed_token({"offer_id": offer_id, "mentee_id": mentee_id})
        portal_url = f"/o/{token}"

        mentor_cards = [build_mentor_card(m) for m in accepted_mentors]
        draft = self.offer_writer.draft_offer(mentee, mentor_cards, portal_url)

        ver_res = self.verifier.verify_offer_draft(draft["body"], accepted_mentors)

        offer_record = {
            "offer_id": offer_id,
            "mentee_id": mentee_id,
            "accepted_mentor_ids": [m["mentor_id"] for m in accepted_mentors],
            "mentor_cards": mentor_cards,
            "subject": draft["subject"],
            "body": draft["body"],
            "token": token,
            "portal_url": portal_url,
            "verifier_passed": ver_res["passed"],
            "status": "draft"
        }
        self.offers[offer_id] = offer_record
        self.record_action(actor, "prepare_offer", offer_id, {"mentor_count": len(accepted_mentors)})
        return offer_record

    def approve_and_send_offer(self, offer_id: str, actor: str) -> Dict[str, Any]:
        offer = self.offers.get(offer_id)
        if not offer:
            raise ValueError(f"Offer {offer_id} not found")

        mentee = self.mentees[offer["mentee_id"]]
        offer["status"] = "sent"
        offer["approved_by"] = actor
        offer["sent_at"] = datetime.now(timezone.utc).isoformat()

        msg = {
            "message_id": f"msg_{uuid.uuid4().hex[:8]}",
            "kind": "mentee_offer",
            "intended_role": "mentee",
            "intended_first_name": mentee["first_name"],
            "delivered_to": "mgomez@project127.org",
            "subject": f"[DEMO → intended: {mentee['first_name']}, mentee] {offer['subject']}",
            "body": offer["body"],
            "approved_by": actor,
            "sent_at": offer["sent_at"],
            "delivery_mode": "gmail (demo redirect)",
            "gmail_message_id": f"g_mock_{uuid.uuid4().hex[:6]}"
        }
        self.outbox.append(msg)
        mentee["status"] = "offer_sent"
        self.record_action(actor, "approve_send_offer", offer_id, {})
        return msg

    def record_offer_response(self, offer_id: str, response: str, chosen_mentor_id: Optional[str] = None, none_fit_reason: Optional[str] = None):
        offer = self.offers.get(offer_id)
        if not offer:
            raise ValueError("Offer not found")
        if offer["status"] == "responded":
            raise ValueError("Offer already responded to")

        offer["status"] = "responded"
        offer["response"] = response
        offer["chosen_mentor_id"] = chosen_mentor_id
        offer["none_fit_reason"] = none_fit_reason

        mentee = self.mentees[offer["mentee_id"]]
        if response == "chose_mentor":
            mentee["status"] = "mentee_selected"
            mentee["selected_mentor_id"] = chosen_mentor_id
        else:
            mentee["status"] = "declined_all"

    def confirm_match(self, mentee_id: str, mentor_id: str, actor: str) -> Dict[str, Any]:
        mentee = self.mentees.get(mentee_id)
        mentor = self.mentors.get(mentor_id)
        match_id = f"mat_{uuid.uuid4().hex[:8]}"

        # Release all holds for this mentee
        for m_id in list(self.mentor_holds.keys()):
            del self.mentor_holds[m_id]

        mentor["current_mentee_count"] = mentor.get("current_mentee_count", 0) + 1
        mentee["status"] = "matched"

        match_record = {
            "match_id": match_id,
            "mentee_id": mentee_id,
            "mentor_id": mentor_id,
            "confirmed_by": actor,
            "confirmed_at": datetime.now(timezone.utc).isoformat()
        }
        self.matches[match_id] = match_record

        # Generate confirmation email to matched mentor
        conf_msg = {
            "message_id": f"msg_{uuid.uuid4().hex[:8]}",
            "kind": "mentor_confirmation",
            "intended_role": "mentor",
            "intended_first_name": mentor["first_name"],
            "delivered_to": "mgomez@project127.org",
            "subject": f"[DEMO → intended: {mentor['first_name']}, mentor] Congratulations! You've Been Matched in New Ground",
            "body": f"Dear {mentor['first_name']},\n\nWe are overjoyed to share that {mentee['first_name']} has selected you as their New Ground mentor!\nOur coordinator will connect with you shortly to schedule your introduction meeting.\n\nProject 1.27",
            "approved_by": actor,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "delivery_mode": "gmail (demo redirect)"
        }
        self.outbox.append(conf_msg)
        self.record_action(actor, "confirm_match", match_id, {"mentor_id": mentor_id})
        return match_record

app_state = AppState()
