"""
Offer Writer Agent
Drafts empowering, plain-language offer emails to mentees (6th-8th grade reading level).
"""
from typing import Dict, Any, List

class OfferWriter:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name

    def draft_offer(self, mentee: Dict[str, Any], accepted_mentor_cards: List[Dict[str, Any]], choose_url: str) -> Dict[str, str]:
        first_name = mentee.get("first_name", "Friend")
        subject = f"Exciting News, {first_name}! Your Mentor Options are Ready"

        mentor_summaries = []
        for m in accepted_mentor_cards:
            m_name = f"{m.get('first_name')} {m.get('last_initial')}."
            bio = m.get("bio", "Excited to support your goals.")
            city = m.get("city", "nearby")
            mentor_summaries.append(f"- **{m_name}** ({city}): {bio}")

        profiles_block = "\n\n".join(mentor_summaries)

        body = f"""Hi {first_name},

Great news! We have several wonderful New Ground mentors who have read about your goals and are very excited about the opportunity to walk alongside you.

Here are the mentors who would love to meet you:

{profiles_block}

YOU GET TO CHOOSE!
Take a look at their profiles and pick the person who feels like the best fit for you. If none of these mentors feel right, you can simply click "None of these feel right" and we will gladly find other options for you—no pressure at all!

Click this link to see their full profiles and make your choice:
{choose_url}

We are cheering you on!

Your New Ground Coordinator
Project 1.27
"""
        return {"subject": subject, "body": body}
