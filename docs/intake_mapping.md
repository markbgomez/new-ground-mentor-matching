# Intake Mapping Specification

Mapping between Mentor Intake Questionnaire, Mentee Intake Questionnaire, and deterministic matching rules.

| Mentee Intake Question | Mentor Intake Question | Matching Rule & Weight |
| :--- | :--- | :--- |
| **Section 1: General Goals** | Skills & Career Experience | Matched via semantic alignment & keyword overlap (Weight: 15) |
| **Section 2: Support Areas** | Support Confidence (1-5) | Direct 1-to-1 rating comparison across 7 core flourishing domains (Weight: 15) |
| **Section 3: Availability** | Availability Blocks | Overlapping schedule blocks (Weekday Evenings, Weekend Mornings, etc.) (Weight: 15) |
| **Section 4: Location & Transit** | Max Travel Bucket & City | Distance computed via zip centroid coordinates. Transit-dependent mentees require mentor to cover travel (Weight: 20) |
| **Section 5: Background Identifiers** | Comfort Ratings (1-5) | **COMFORT GATE**: Mentor rating <= 2 triggers hard exclusion. Rating 3 is caution. Rating 4-5 earns bonus points (Weight: 5) |
| **Section 5: Spiritual Preference** | Spiritual Importance | **SPIRITUAL GATE**: Mentor "Essential" + Mentee "Non-spiritual focus" triggers hard exclusion (Weight: 5) |
| **Section 6: Profile Sharing Consent** | Section 7: Profile Sharing Consent | Determines data exposure in mentor invitations and mentee offers. Only consented fields are rendered. |
