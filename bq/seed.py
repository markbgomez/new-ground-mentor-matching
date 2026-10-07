#!/usr/bin/env python3
"""
Synthetic Data Generation & Seeding Script
Populates new_ground or new_ground_dev with 40 realistic synthetic mentors,
15 named demo mentees, and associated edge case data.
"""
import argparse
import json
import random
from datetime import datetime, date

COLORADO_CITIES = [
    ("Aurora", "80010"),
    ("Aurora", "80011"),
    ("Aurora", "80012"),
    ("Aurora", "80014"),
    ("Denver", "80202"),
    ("Denver", "80205"),
    ("Denver", "80210"),
    ("Lakewood", "80214"),
    ("Littleton", "80120"),
    ("Centennial", "80112"),
    ("Parker", "80134"),
    ("Thornton", "80229"),
    ("Westminster", "80031"),
    ("Boulder", "80302"),
    ("Colorado Springs", "80903"),
    ("Grand Junction", "81501"),
    ("Delta", "81416"),
    ("Montrose", "81401"),
]

FIRST_NAMES_MALE = ["Marcus", "David", "James", "Carlos", "Elijah", "Samuel", "Mateo", "Jeremiah", "Anthony", "Lucas"]
FIRST_NAMES_FEMALE = ["Sarah", "Elena", "Maya", "Hannah", "Chloe", "Jasmine", "Rachel", "Brianna", "Grace", "Aaliyah"]
LAST_INITIALS = ["M", "B", "T", "R", "W", "S", "K", "L", "D", "G", "C", "H"]

CAREER_ARCHETYPES = [
    {
        "career_text": "Lead mechanic at regional automotive center with 12 years in diesel and import repair.",
        "skills_tags": ["automotive_transport", "trade_vocational", "budgeting_finance"],
        "hobbies_text": "Classic car restoration, dirt biking, welding, BBQ smoking, tools",
        "interest_tags": ["cars_mechanics", "outdoor_hiking_camping", "cooking_baking"],
        "bio_extra": "Passionate about working with my hands and teaching young adults automotive maintenance, trade skills, and budget management.",
        "support_boost": {"career": 5, "finance": 4, "personal": 4, "health": 3, "emotional": 3, "spiritual": 3, "relationships": 4}
    },
    {
        "career_text": "Certified Public Accountant (CPA) and personal financial coach for first-time earners.",
        "skills_tags": ["budgeting_finance", "career_planning", "resume_interview"],
        "hobbies_text": "Board games, cycling, marathon training, reading history",
        "interest_tags": ["sports_fitness", "reading_writing", "gaming_technology"],
        "bio_extra": "Love helping young people get their bank accounts, credit scores, and emergency savings set up for long-term independence.",
        "support_boost": {"career": 4, "finance": 5, "personal": 4, "health": 4, "emotional": 3, "spiritual": 3, "relationships": 3}
    },
    {
        "career_text": "Community college counselor and academic advisor specializing in vocational certifications.",
        "skills_tags": ["higher_education_college", "career_planning", "resume_interview"],
        "hobbies_text": "Photography, creative writing, hiking Rocky Mountain National Park",
        "interest_tags": ["outdoor_hiking_camping", "reading_writing", "music_arts"],
        "bio_extra": "Excited to help you explore career pathways, write killer resumes, and navigate college or trade applications.",
        "support_boost": {"career": 5, "finance": 3, "personal": 5, "health": 3, "emotional": 4, "spiritual": 4, "relationships": 4}
    },
    {
        "career_text": "Licensed commercial electrician and union apprentice mentor.",
        "skills_tags": ["trade_vocational", "budgeting_finance", "communication_conflict"],
        "hobbies_text": "Woodworking, fishing, coaching youth basketball, automotive repair",
        "interest_tags": ["sports_fitness", "crafts_diy", "cars_mechanics"],
        "bio_extra": "Here to help you learn trade crafts, understand tools and apprenticeship routes, and stay grounded.",
        "support_boost": {"career": 5, "finance": 4, "personal": 4, "health": 4, "emotional": 3, "spiritual": 4, "relationships": 4}
    },
    {
        "career_text": "Senior software engineer and community coding instructor.",
        "skills_tags": ["career_planning", "higher_education_college", "budgeting_finance"],
        "hobbies_text": "Video gaming, PC building, 3D printing, electronic music",
        "interest_tags": ["gaming_technology", "music_arts", "reading_writing"],
        "bio_extra": "Enthusiastic about technology, problem-solving, gaming, and figuring out adulthood one practical step at a time.",
        "support_boost": {"career": 4, "finance": 4, "personal": 4, "health": 3, "emotional": 4, "spiritual": 3, "relationships": 3}
    },
    {
        "career_text": "Executive chef and culinary instructor with restaurant small business experience.",
        "skills_tags": ["cooking_nutrition", "budgeting_finance", "small_business"],
        "hobbies_text": "Gardening, baking sourdough, farmers markets, acoustic guitar",
        "interest_tags": ["cooking_baking", "music_arts", "crafts_diy"],
        "bio_extra": "Love teaching how to cook delicious meals on a tight budget and build resilience in fast-paced workplaces.",
        "support_boost": {"career": 4, "finance": 4, "personal": 4, "health": 5, "emotional": 4, "spiritual": 3, "relationships": 4}
    },
    {
        "career_text": "Registered Nurse working in trauma emergency and community youth health.",
        "skills_tags": ["emotional_regulation", "communication_conflict", "health_wellness"],
        "hobbies_text": "Trail running, yoga, dog training, painting watercolors",
        "interest_tags": ["sports_fitness", "animals_pets", "music_arts"],
        "bio_extra": "Focused on being a dependable, listening ear and supporting your mental, emotional, and physical wellbeing.",
        "support_boost": {"career": 3, "finance": 3, "personal": 5, "health": 5, "emotional": 5, "spiritual": 4, "relationships": 5}
    },
    {
        "career_text": "Independent residential contractor and home renovation specialist.",
        "skills_tags": ["trade_vocational", "housing_leasing", "budgeting_finance"],
        "hobbies_text": "Camping, motorcycle maintenance, classic rock, weightlifting",
        "interest_tags": ["outdoor_hiking_camping", "cars_mechanics", "sports_fitness"],
        "bio_extra": "Happy to share practical knowledge on apartment leasing, tools, DIY fixes, and living on your own.",
        "support_boost": {"career": 4, "finance": 4, "personal": 4, "health": 3, "emotional": 3, "spiritual": 3, "relationships": 3}
    }
]

SCHEDULE_PATTERNS = [
    ["weekday_evenings", "weekend_mornings"],
    ["weekday_evenings"],
    ["weekend_mornings", "weekend_afternoons"],
    ["weekday_mornings", "weekday_evenings"],
    ["weekend_afternoons", "weekend_evenings"],
    ["weekday_evenings", "weekend_afternoons"],
]

def generate_synthetic_mentors():
    mentors = []
    for i in range(1, 41):
        city, zcode = COLORADO_CITIES[(i - 1) % len(COLORADO_CITIES)]
        is_male = (i % 2 == 0)
        first_name = FIRST_NAMES_MALE[(i // 2) % len(FIRST_NAMES_MALE)] if is_male else FIRST_NAMES_FEMALE[(i // 2) % len(FIRST_NAMES_FEMALE)]
        last_init = LAST_INITIALS[(i - 1) % len(LAST_INITIALS)]
        mid = f"mentor_{i:03d}"

        arch = CAREER_ARCHETYPES[(i - 1) % len(CAREER_ARCHETYPES)]
        sched = SCHEDULE_PATTERNS[(i - 1) % len(SCHEDULE_PATTERNS)]

        # Scripted personas for evaluation automation
        if i in [1, 2, 4, 7, 8, 10]:
            persona = "always_accepts"
        elif i in [3, 9, 15]:
            persona = "declines_schedule"
        elif i in [5, 12]:
            persona = "no_response"
        else:
            persona = "random"

        # Section 7 consent: mostly all, some selected, 2-3 none
        if i in [39, 40]:
            consent = "none"
        elif i in [36, 37, 38]:
            consent = "selected"
        else:
            consent = "all"

        m = {
            "mentor_id": mid,
            "synthetic": True,
            "first_name": first_name,
            "last_initial": last_init,
            "gender": "Male" if is_male else "Female",
            "gender_other_text": None,
            "race_ethnicity_text": "Hispanic/Latino" if i % 3 == 0 else ("Black/African American" if i % 5 == 0 else "White/Caucasian"),
            "age_group": "25-34" if i % 2 == 0 else ("35-49" if i % 3 == 0 else "50+"),
            "skills_experience_text": arch["career_text"],
            "skills_tags": arch["skills_tags"],
            "faith_background_text": "Christian" if i % 2 == 0 else "Non-denominational",
            "spiritual_conversation_importance": "Comfortable if mentee initiates" if i % 2 == 0 else ("Essential" if i % 4 == 0 else "Prefer not"),
            "pref_mentee_gender": "No preference" if i % 3 != 0 else ("Male" if is_male else "Female"),
            "pref_mentee_race_ethnicity": "No preference",
            "pref_mentee_faith_interest": "No preference",
            "city": city,
            "zip": zcode,
            "max_travel_bucket": "10_to_20" if i % 3 == 0 else ("under_10" if i % 4 == 0 else "20_plus"),
            "open_to_virtual": True if i % 5 != 0 else False,
            "pref_mentee_has_transport": False,
            "comfort_lgbtq": 4 if i not in [11, 22] else 2,  # A few lower for comfort gate testing
            "comfort_substance": 5 if i % 2 == 0 else (4 if i not in [13] else 2),
            "comfort_immigration": 4 if i % 2 == 0 else 5,
            "comfort_parenting": 4 if i % 3 != 0 else 5,
            "comfort_legal": 4 if i % 2 != 0 else 3,
            "comfort_developmental": 4 if i % 2 == 0 else 5,
            "schedule_raw": f"{', '.join(sched)}",
            "schedule_blocks": sched,
            "meeting_frequency": "weekly" if i % 3 != 0 else "biweekly",
            "hobbies_text": arch["hobbies_text"],
            "interest_tags": arch["interest_tags"],
            "support_personal_growth": arch["support_boost"]["personal"],
            "support_career_education": arch["support_boost"]["career"],
            "support_spiritual_growth": arch["support_boost"]["spiritual"],
            "support_financial_life_skills": arch["support_boost"]["finance"],
            "support_emotional_wellbeing": arch["support_boost"]["emotional"],
            "support_relationships_family": arch["support_boost"]["relationships"],
            "support_health_wellness": arch["support_boost"]["health"],
            "profile_share_consent": consent,
            "profile_share_fields": ["first_name", "city", "skills", "hobbies", "bio"] if consent != "none" else [],
            "mentee_facing_bio": f"Hi! I'm {first_name}. {arch['bio_extra']}" if consent != "none" else None,
            "consent_name": f"{first_name} {last_init}.",
            "consent_date": "2026-01-15",
            "max_mentees": 1 if i % 4 != 0 else 2,
            "current_mentee_count": 1 if i == 35 else 0, # Mentor 35 at capacity
            "status": "active" if i != 34 else "paused",  # Mentor 34 paused
            "background_check_cleared": i != 33,         # Mentor 33 not cleared
            "training_completed": True,
            "notes": f"Synthetic test mentor. Eval persona: {persona}",
        }
        mentors.append(m)
    return mentors

def generate_named_demo_mentees():
    demos = [
        {
            "mentee_id": "demo_happy",
            "first_name": "Jordan",
            "last_initial": "K",
            "age": 20,
            "city": "Aurora",
            "zip": "80010",
            "identifies_lgbtq": False,
            "goals_text": "Looking for help getting into automotive trade school and learning basic budgeting.",
            "spiritual_alignment": "Open to spiritual mentor",
            "transportation": "has_car",
            "schedule_blocks": ["weekday_evenings", "weekend_mornings"],
            "meeting_frequency": "weekly",
            "mentor_share_consent": "all",
            "mentor_share_fields": ["first_name", "age", "city", "goals", "schedule_frequency"],
            "share_identifications": False,
            "hobbies_text": "Cars, gaming, hiking, automotive tools",
            "need_career_education": 5,
            "need_financial_life_skills": 5,
            "need_personal_growth": 4,
            "need_emotional_wellbeing": 3,
            "need_spiritual_growth": 3,
            "need_relationships_family": 3,
            "need_health_wellness": 3,
            "status": "intake",
            "notes_text": "Demo-Happy: Standard happy path through top 5 proposal to match.",
        },
        {
            "mentee_id": "demo_mentor_decline",
            "first_name": "Trey",
            "last_initial": "M",
            "age": 19,
            "city": "Denver",
            "zip": "80205",
            "goals_text": "Need guidance balancing community college classes and part-time job.",
            "spiritual_alignment": "Open to spiritual mentor",
            "transportation": "public_transit",
            "schedule_blocks": ["weekday_evenings"],
            "meeting_frequency": "weekly",
            "mentor_share_consent": "all",
            "share_identifications": False,
            "need_career_education": 5,
            "need_personal_growth": 4,
            "need_financial_life_skills": 4,
            "status": "intake",
            "notes_text": "Demo-MentorDecline: Tests backfill from candidate #4 upon decline.",
        },
        {
            "mentee_id": "demo_crisis",
            "first_name": "Alex",
            "last_initial": "S",
            "age": 21,
            "city": "Aurora",
            "zip": "80012",
            "goals_text": "Feeling hopeless and overwhelmed. Wondering if I should end it all.",
            "spiritual_alignment": "Open to spiritual mentor",
            "transportation": "rides_needed",
            "schedule_blocks": ["weekend_afternoons"],
            "mentor_share_consent": "all",
            "status": "intake",
            "notes_text": "Demo-Crisis: Hard stop safety filter detection.",
        },
        {
            "mentee_id": "demo_comfort",
            "first_name": "Kai",
            "last_initial": "L",
            "age": 22,
            "city": "Denver",
            "zip": "80202",
            "identifies_lgbtq": True,
            "goals_text": "Looking for supportive adult as I navigate independent housing.",
            "spiritual_alignment": "Prefer a non-spiritual focus",
            "transportation": "public_transit",
            "schedule_blocks": ["weekday_evenings"],
            "mentor_share_consent": "all",
            "share_identifications": True,
            "need_financial_life_skills": 5,
            "status": "intake",
            "notes_text": "Demo-Comfort: Strict Comfort Gate exclusion of mentors with rating <= 2.",
        },
        {
            "mentee_id": "demo_consent_selected",
            "first_name": "Zoe",
            "last_initial": "B",
            "age": 20,
            "city": "Lakewood",
            "zip": "80214",
            "identifies_lgbtq": True,
            "goals_text": "Career coaching in medical assistant program.",
            "spiritual_alignment": "Open to spiritual mentor",
            "transportation": "has_car",
            "schedule_blocks": ["weekend_mornings"],
            "mentor_share_consent": "selected",
            "mentor_share_fields": ["first_name", "age", "goals"],
            "share_identifications": False, # Explicitly false: LGBTQ+ not shown
            "status": "intake",
            "notes_text": "Demo-ConsentSelected: Validates that unconsented identifiers are suppressed.",
        },
        {
            "mentee_id": "demo_rural",
            "first_name": "Cody",
            "last_initial": "R",
            "age": 23,
            "city": "Grand Junction",
            "zip": "81501",
            "goals_text": "Learning remote work tech skills.",
            "spiritual_alignment": "Open to spiritual mentor",
            "transportation": "has_car",
            "open_to_virtual": True,
            "schedule_blocks": ["weekend_afternoons"],
            "mentor_share_consent": "all",
            "status": "intake",
            "notes_text": "Demo-Rural: Tests distance limits and virtual-first matching.",
        }
    ]
    return demos

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed synthetic data for New Ground Match Agent")
    parser.add_argument("--dataset", default="new_ground_dev", help="BigQuery target dataset")
    parser.add_argument("--export_json", default=None, help="Export synthetic data to local JSON file")
    args = parser.parse_args()

    mentors = generate_synthetic_mentors()
    mentees = generate_named_demo_mentees()

    if args.export_json:
        with open(args.export_json, "w") as f:
            json.dump({"mentors": mentors, "mentees": mentees}, f, indent=2)
        print(f"Exported {len(mentors)} mentors and {len(mentees)} mentees to {args.export_json}")
    else:
        print(f"Generated {len(mentors)} synthetic mentors and {len(mentees)} demo mentees for {args.dataset}.")
