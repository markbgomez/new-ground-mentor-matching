"""
Deterministic Matching Engine & Tools
Implements exact scoring weights, hard filters, comfort/spiritual gates,
and card generators per Project 1.27 specifications.
"""
import math
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

# Default coordinates for Colorado zip centroids
ZIP_COORDINATES = {
    "80010": (39.7392, -104.8694), # Aurora
    "80011": (39.7422, -104.8317), # Aurora
    "80012": (39.6997, -104.8317), # Aurora
    "80014": (39.6644, -104.8430), # Aurora
    "80202": (39.7539, -104.9997), # Denver Downtown
    "80205": (39.7610, -104.9723), # Denver Five Points
    "80210": (39.6788, -104.9653), # Denver South
    "80214": (39.7425, -105.0744), # Lakewood
    "80120": (39.6014, -105.0064), # Littleton
    "80112": (39.5936, -104.8872), # Centennial
    "80134": (39.5186, -104.7614), # Parker
    "80229": (39.8655, -104.9789), # Thornton
    "80031": (39.8617, -105.0503), # Westminster
    "80302": (40.0150, -105.2705), # Boulder
    "80903": (38.8339, -104.8214), # Colorado Springs
    "81501": (39.0639, -108.5506), # Grand Junction
    "81416": (38.7422, -108.0690), # Delta
    "81401": (38.4783, -107.8762), # Montrose
}

def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great Circle distance in miles between two latitude/longitude points."""
    r = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c

def geocode_zip(zip_code: str) -> Tuple[float, float]:
    """Returns (lat, lon) for given zip code or default Denver metro centroid."""
    return ZIP_COORDINATES.get(str(zip_code).strip(), (39.7392, -104.9903))

def detect_risk_flags(text: str) -> List[str]:
    """Scans text for safety, harm, or crisis markers requiring immediate escalation."""
    if not text:
        return []
    flags = []
    text_lower = text.lower()
    crisis_keywords = ["suicide", "kill myself", "end it all", "self-harm", "overdose", "hurt myself", "weapons", "abuse right now"]
    for kw in crisis_keywords:
        if kw in text_lower:
            flags.append(f"CRISIS_ALERT: Mention of '{kw}' detected")
    return flags

def apply_hard_filters(mentee: Dict[str, Any], mentor: Dict[str, Any], open_holds: int = 0) -> Tuple[bool, List[str]]:
    """
    Applies non-negotiable gates:
    - Active, cleared, trained
    - Section 7 consent != 'none'
    - Capacity check: (current_mentee_count + open_holds) < max_mentees
    - Comfort gate: Mentee checked area and mentor rated comfort <= 2 -> EXCLUDE
    - Spiritual gate: Mentor 'Essential' + Mentee 'Prefer a non-spiritual focus' -> EXCLUDE
    - Proximity & virtual reachability
    """
    reasons = []

    # 1. Eligibility & Screening
    if not mentor.get("background_check_cleared", True):
        return False, ["Background check not cleared"]
    if not mentor.get("training_completed", True):
        return False, ["Training not completed"]
    if mentor.get("status", "active") != "active":
        return False, [f"Mentor status is {mentor.get('status')}"]
    if mentor.get("profile_share_consent") == "none":
        return False, ["Mentor has not consented to share profile (Section 7)"]

    # 2. Capacity
    max_m = mentor.get("max_mentees", 1)
    curr_m = mentor.get("current_mentee_count", 0)
    if (curr_m + open_holds) >= max_m:
        return False, [f"Mentor at capacity ({curr_m} current + {open_holds} holds >= {max_m} max)"]

    # 3. Spiritual Gate
    mentor_spirit = mentor.get("spiritual_conversation_importance", "")
    mentee_spirit = mentee.get("spiritual_alignment", "")
    if mentor_spirit == "Essential" and mentee_spirit == "Prefer a non-spiritual focus":
        return False, ["Spiritual Gate: Mentor requires spiritual focus but mentee prefers non-spiritual"]

    # 4. Comfort Gate (<= 2 is an automatic hard exclusion)
    comfort_checks = [
        ("identifies_lgbtq", "comfort_lgbtq", "LGBTQ+ support"),
        ("substance_recovery", "comfort_substance", "Substance recovery"),
        ("immigration_refugee", "comfort_immigration", "Immigration/refugee status"),
        ("is_parenting", "comfort_parenting", "Parenting support"),
        ("legal_history", "comfort_legal", "Legal history navigation"),
        ("developmental", "comfort_developmental", "Developmental support"),
    ]
    for mentee_field, mentor_field, label in comfort_checks:
        if mentee.get(mentee_field):
            comfort_rating = mentor.get(mentor_field, 3)
            if comfort_rating <= 2:
                return False, [f"Comfort Gate: Mentee identifies {label}, but mentor comfort rating is {comfort_rating}/5 (<= 2 excluded)"]

    # 5. Distance and Transportation
    mentee_lat, mentee_lon = geocode_zip(mentee.get("zip", "80010"))
    mentor_lat, mentor_lon = geocode_zip(mentor.get("zip", "80010"))
    distance = haversine_miles(mentee_lat, mentee_lon, mentor_lat, mentor_lon)

    travel_bucket = mentor.get("max_travel_bucket", "10_to_20")
    bucket_limit = 10.0 if travel_bucket == "under_10" else (20.0 if travel_bucket == "10_to_20" else 25.0)

    mentee_transit = mentee.get("transportation", "has_car")
    open_virtual = mentee.get("open_to_virtual", False) and mentor.get("open_to_virtual", False)

    if mentee_transit == "has_car":
        # Meet-halfway allowance: combined travel up to bucket + 15 mi
        max_dist = bucket_limit + 15.0
    else:
        # Transit dependent or rides needed: relies on mentor's travel bucket alone
        max_dist = bucket_limit

    if distance > max_dist:
        if not open_virtual:
            return False, [f"Distance Gate: {distance:.1f} mi exceeds reachable limit of {max_dist:.1f} mi (Virtual not available)"]

    return True, []

def score_match(mentee: Dict[str, Any], mentor: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes weighted score out of 100 with nuanced differentiation:
    mentee_preferences: 30
    proximity_transport: 20
    support_area_fit: 15
    availability: 15
    comfort_depth: 5
    faith_alignment: 5
    interests_goals: 5
    mentor_preferences: 5
    """
    sub_scores = {}

    # 1. Proximity & Transport (Max 20.0)
    mentee_lat, mentee_lon = geocode_zip(mentee.get("zip", "80010"))
    mentor_lat, mentor_lon = geocode_zip(mentor.get("zip", "80010"))
    dist = haversine_miles(mentee_lat, mentee_lon, mentor_lat, mentor_lon)

    # Smooth distance decay
    if dist <= 2.5:
        prox_score = 20.0
    elif dist <= 25.0:
        prox_score = max(5.0, round(20.0 - (dist * 0.55), 1))
    else:
        prox_score = 5.0 if (mentee.get("open_to_virtual") and mentor.get("open_to_virtual")) else 2.0
    sub_scores["proximity_transport"] = prox_score

    # 2. Support Area Fit (Max 15.0)
    support_fields = [
        ("need_personal_growth", "support_personal_growth"),
        ("need_career_education", "support_career_education"),
        ("need_spiritual_growth", "support_spiritual_growth"),
        ("need_financial_life_skills", "support_financial_life_skills"),
        ("need_emotional_wellbeing", "support_emotional_wellbeing"),
        ("need_relationships_family", "support_relationships_family"),
        ("need_health_wellness", "support_health_wellness"),
    ]
    total_weights = 0.0
    earned_points = 0.0
    strength_multipliers = {5: 1.0, 4: 0.82, 3: 0.58, 2: 0.30, 1: 0.10}

    for mentee_k, mentor_k in support_fields:
        need = mentee.get(mentee_k, 3)
        strength = mentor.get(mentor_k, 3)
        weight = need / 5.0  # Weight areas higher if mentee has higher need
        total_weights += weight
        earned_points += weight * strength_multipliers.get(strength, 0.58)

    if total_weights > 0:
        sub_scores["support_area_fit"] = round((earned_points / total_weights) * 15.0, 1)
    else:
        sub_scores["support_area_fit"] = 11.5

    # 3. Availability & Scheduling (Max 15.0)
    mentee_blocks = set(mentee.get("schedule_blocks", []))
    mentor_blocks = set(mentor.get("schedule_blocks", []))
    common_blocks = mentee_blocks.intersection(mentor_blocks)

    if len(common_blocks) >= 3:
        avail_score = 14.0
    elif len(common_blocks) == 2:
        avail_score = 12.5
    elif len(common_blocks) == 1:
        avail_score = 9.5
    else:
        avail_score = 4.5 if (mentee.get("open_to_virtual") or mentor.get("open_to_virtual")) else 2.0

    # Alignment on meeting frequency bonus
    if mentee.get("meeting_frequency") == mentor.get("meeting_frequency"):
        avail_score = min(15.0, avail_score + 1.0)
    sub_scores["availability"] = round(avail_score, 1)

    # 4. Comfort Depth (Max 5.0)
    comfort_checks = [
        ("identifies_lgbtq", "comfort_lgbtq"),
        ("substance_recovery", "comfort_substance"),
        ("immigration_refugee", "comfort_immigration"),
        ("is_parenting", "comfort_parenting"),
        ("legal_history", "comfort_legal"),
        ("developmental", "comfort_developmental"),
    ]
    all_comfort_ratings = [mentor.get(cf, 3) for _, cf in comfort_checks]
    avg_comfort = sum(all_comfort_ratings) / len(all_comfort_ratings)
    base_comfort = (avg_comfort / 5.0) * 3.5

    specific_bonus = 0.0
    for mf, cf in comfort_checks:
        if mentee.get(mf):
            rating = mentor.get(cf, 3)
            if rating >= 4:
                specific_bonus += 0.75
    sub_scores["comfort_depth"] = min(5.0, round(base_comfort + specific_bonus, 1))

    # 5. Faith / Spiritual Alignment (Max 5.0)
    mentor_spirit = mentor.get("spiritual_conversation_importance", "")
    mentee_spirit = mentee.get("spiritual_alignment", "")
    if mentee_spirit == "Christian mentor preferred":
        faith_score = 5.0 if mentor_spirit == "Essential" else (4.3 if mentor_spirit == "Comfortable if mentee initiates" else 2.0)
    elif mentee_spirit == "Open to spiritual mentor":
        faith_score = 4.8 if mentor_spirit != "Prefer not" else 3.8
    else:  # "Prefer a non-spiritual focus"
        faith_score = 5.0 if mentor_spirit == "Prefer not" else (3.6 if mentor_spirit == "Comfortable if mentee initiates" else 1.0)
    sub_scores["faith_alignment"] = round(faith_score, 1)

    # 6. Interests & Goals Alignment (Max 5.0)
    mentee_text = f"{mentee.get('goals_text', '')} {mentee.get('hobbies_text', '')}".lower()
    mentor_text = f"{mentor.get('skills_experience_text', '')} {mentor.get('hobbies_text', '')} {' '.join(mentor.get('skills_tags', []))} {' '.join(mentor.get('interest_tags', []))}".lower()

    mentee_words = set(w.strip(",.!?\"'()") for w in mentee_text.split() if len(w) > 3)
    mentor_words = set(w.strip(",.!?\"'()") for w in mentor_text.split() if len(w) > 3)
    common_words = mentee_words.intersection(mentor_words)
    overlap_count = len(common_words)

    if overlap_count >= 4:
        interest_score = 5.0
    elif overlap_count == 3:
        interest_score = 4.4
    elif overlap_count == 2:
        interest_score = 3.7
    elif overlap_count == 1:
        interest_score = 2.9
    else:
        interest_score = 2.0
    sub_scores["interests_goals"] = interest_score

    # 7. Mentee Preferences (Max 30.0 - Dominant Weight)
    # Dynamically evaluate alignment with mentee career goals and preferences
    pref_score = 20.0

    # Trade / career specific synergy
    if any(k in mentee_text for k in ["trade", "automotive", "mechanic", "electric", "carpenter", "tools", "repair"]):
        if any(k in mentor_text for k in ["trade", "automotive", "mechanic", "repair", "tools", "electric", "carpenter", "construction"]):
            pref_score += 4.5
        elif any(k in mentor.get("skills_tags", []) for k in ["automotive_transport", "trade_vocational"]):
            pref_score += 3.5

    # Higher ed / college synergy
    if any(k in mentee_text for k in ["college", "degree", "school", "university", "classes"]):
        if any(k in mentor_text for k in ["college", "university", "degree", "academic", "higher_education_college"]):
            pref_score += 4.0

    # Financial / budgeting synergy
    if any(k in mentee_text for k in ["budget", "finance", "money", "savings"]):
        if any(k in mentor_text for k in ["budgeting_finance", "budget", "finance", "financial", "accounting"]):
            pref_score += 3.0

    # Mentor bio richness bonus
    if mentor.get("mentee_facing_bio") and len(mentor.get("mentee_facing_bio")) > 50:
        pref_score += 1.5

    sub_scores["mentee_preferences"] = min(30.0, round(pref_score, 1))

    # 8. Mentor Preferences (Max 5.0 - Low Weight Tie-Breaker)
    m_pref = 4.0
    if mentor.get("pref_mentee_gender") == "No preference":
        m_pref += 0.5
    elif mentor.get("pref_mentee_gender") == mentee.get("gender_identity_text"):
        m_pref += 0.8
    else:
        m_pref -= 0.5
    sub_scores["mentor_preferences"] = min(5.0, max(2.5, round(m_pref, 1)))

    total_score = sum(sub_scores.values())


    return {
        "mentor_id": mentor["mentor_id"],
        "mentor_name": f"{mentor['first_name']} {mentor['last_initial']}.",
        "total_score": round(total_score, 1),
        "distance_miles": round(dist, 1),
        "sub_scores": sub_scores,
        "shared_availability": list(common_blocks),
        "virtual_first": bool(dist > 20.0 and mentee.get("open_to_virtual") and mentor.get("open_to_virtual")),
        "consent_ok": mentor.get("profile_share_consent") in ["all", "selected"],
    }

def build_mentee_card(mentee: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds mentee card adhering strictly to Section 6 Profile Sharing Consent:
    - Never exposes last name, DOB, street address, or contact info.
    - Sensitive identifications appear ONLY if share_identifications=True.
    - If consent is 'none', only general summary goals are exposed.
    - If 'not_asked' (legacy), only safe defaults are exposed.
    """
    consent = mentee.get("mentor_share_consent", "all")
    shared_fields = mentee.get("mentor_share_fields") or []
    share_ids = mentee.get("share_identifications", False)

    card = {
        "first_name": mentee.get("first_name", "Mentee"),
        "consent_level": consent,
        "intro_quote": mentee.get("mentee_intro_text"),
    }

    if consent == "none":
        card["summary_of_goals"] = "Mentee is seeking general encouragement and career direction."
        card["restricted_notice"] = "Mentee elected not to share personal profile details in advance."
        return card

    if consent in ["all", "not_asked"]:
        card["age"] = mentee.get("age")
        card["general_area"] = mentee.get("city")
        card["goals"] = mentee.get("goals_text")
        card["meeting_frequency"] = mentee.get("meeting_frequency")
        card["schedule_blocks"] = mentee.get("schedule_blocks")
        card["transportation"] = mentee.get("transportation")
    elif consent == "selected":
        if "age" in shared_fields: card["age"] = mentee.get("age")
        if "city" in shared_fields: card["general_area"] = mentee.get("city")
        if "goals" in shared_fields: card["goals"] = mentee.get("goals_text")
        if "schedule_frequency" in shared_fields:
            card["meeting_frequency"] = mentee.get("meeting_frequency")
            card["schedule_blocks"] = mentee.get("schedule_blocks")

    # Sensitive identifications are strictly opt-in
    if share_ids:
        ids = []
        if mentee.get("identifies_lgbtq"): ids.append("LGBTQ+")
        if mentee.get("substance_recovery"): ids.append("Substance Recovery")
        if mentee.get("immigration_refugee"): ids.append("Immigrant/Refugee")
        if mentee.get("is_parenting"): ids.append("Parenting")
        if mentee.get("legal_history"): ids.append("Justice Involved")
        if mentee.get("developmental"): ids.append("Developmental Neurodiversity")
        card["consented_identifications"] = ids

    return card

def build_mentor_card(mentor: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds mentor card for mentee offer.
    ONLY includes Section 7 consented fields + bio.
    NEVER includes comfort ratings, mentor preferences, background check, or last names.
    """
    return {
        "mentor_id": mentor["mentor_id"],
        "first_name": mentor["first_name"],
        "last_initial": mentor["last_initial"],
        "city": mentor.get("city"),
        "bio": mentor.get("mentee_facing_bio", f"A caring mentor interested in {mentor.get('hobbies_text', 'mentorship')}."),
        "skills_tags": mentor.get("skills_tags", []),
        "interest_tags": mentor.get("interest_tags", []),
        "meeting_frequency": mentor.get("meeting_frequency"),
        "schedule_blocks": mentor.get("schedule_blocks", []),
    }
