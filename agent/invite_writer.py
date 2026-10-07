"""
Invite Writer Agent
Drafts personalized, respectful mentor invitations.
"""
from typing import Dict, Any

class InviteWriter:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name

    def draft_invitation(self, mentor: Dict[str, Any], mentee_card: Dict[str, Any], match_meta: Dict[str, Any], token_url: str) -> Dict[str, str]:
        """Creates email draft for prospective mentor."""
        first_name = mentor.get("first_name", "Mentor")
        mentee_first = mentee_card.get("first_name", "a young adult")
        goals = mentee_card.get("goals", "identifying career goals and personal growth")
        area = mentee_card.get("general_area", "the Denver metro area")

        subject = f"Potential Mentoring Match with New Ground: {mentee_first}"

        body = f"""Dear {first_name},

Thank you for your ongoing commitment as a volunteer mentor with Project 1.27's New Ground program!

We are reaching out because we believe you could be a wonderful match for {mentee_first}, who is living in {area} and is focused on:
"{goals}"

Based on your shared schedule and interests, we would love for you to consider this potential match.

WHAT ACCEPTING MEANS:
If you feel this could be a good fit and accept, we will share your mentor profile with {mentee_first}. In New Ground, our young adults make the final selection of their mentor. There is no commitment until {mentee_first} selects you and our coordinator connects you.

Declining is completely okay! Your comfort and capacity come first, and declining will not impact future opportunities.

Please review the profile and let us know your decision within 3 days by clicking below:
{token_url}

Warmly,
The New Ground Team
Project 1.27
"""
        return {"subject": subject, "body": body}
