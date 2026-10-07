-- BigQuery Schema for New Ground Match Agent
-- Dataset: new_ground (US) and new_ground_dev (US)

-- 1. Mentors table (Intake Sections 1-7)
CREATE TABLE IF NOT EXISTS `{dataset}.mentors` (
    mentor_id STRING NOT NULL,
    synthetic BOOL DEFAULT TRUE,
    first_name STRING NOT NULL,
    last_initial STRING NOT NULL,
    gender STRING,
    gender_other_text STRING,
    race_ethnicity_text STRING,
    age_group STRING,
    skills_experience_text STRING,
    skills_tags ARRAY<STRING>,
    faith_background_text STRING,
    spiritual_conversation_importance STRING, -- "Essential", "Comfortable if mentee initiates", "Prefer not"
    pref_mentee_gender STRING,
    pref_mentee_race_ethnicity STRING,
    pref_mentee_faith_interest STRING,
    city STRING,
    zip STRING,
    geo GEOGRAPHY,
    max_travel_bucket STRING, -- "under_10", "10_to_20", "20_plus"
    open_to_virtual BOOL,
    pref_mentee_has_transport BOOL,
    comfort_lgbtq INT64, -- 1-5
    comfort_substance INT64, -- 1-5
    comfort_immigration INT64, -- 1-5
    comfort_parenting INT64, -- 1-5
    comfort_legal INT64, -- 1-5
    comfort_developmental INT64, -- 1-5
    schedule_raw STRING,
    schedule_blocks ARRAY<STRING>,
    meeting_frequency STRING,
    personality_text STRING,
    hobbies_text STRING,
    career_text STRING,
    activities_text STRING,
    interest_tags ARRAY<STRING>,
    support_personal_growth INT64, -- 1-5
    support_career_education INT64, -- 1-5
    support_spiritual_growth INT64, -- 1-5
    support_financial_life_skills INT64, -- 1-5
    support_emotional_wellbeing INT64, -- 1-5
    support_relationships_family INT64, -- 1-5
    support_health_wellness INT64, -- 1-5
    profile_share_consent STRING, -- "all", "selected", "none"
    profile_share_fields ARRAY<STRING>,
    mentee_facing_bio STRING,
    consent_name STRING,
    consent_date DATE,
    consent_withdrawn_at TIMESTAMP,
    max_mentees INT64 DEFAULT 1,
    current_mentee_count INT64 DEFAULT 0,
    status STRING DEFAULT 'active', -- 'active', 'paused', 'inactive'
    background_check_cleared BOOL DEFAULT TRUE,
    training_completed BOOL DEFAULT TRUE,
    notes STRING,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- 2. Restricted mentor contact (NEVER sent to Gemini)
CREATE TABLE IF NOT EXISTS `{dataset}.mentor_contact` (
    mentor_id STRING NOT NULL,
    full_name STRING NOT NULL,
    email STRING NOT NULL,
    phone STRING
);

-- 3. Restricted mentee contact (NEVER sent to Gemini or shown to mentors)
CREATE TABLE IF NOT EXISTS `{dataset}.mentee_contact` (
    mentee_id STRING NOT NULL,
    full_name STRING NOT NULL,
    date_of_birth DATE,
    email STRING NOT NULL,
    phone STRING,
    street_address STRING
);

-- 4. Mentees table
CREATE TABLE IF NOT EXISTS `{dataset}.mentees` (
    mentee_id STRING NOT NULL,
    synthetic BOOL DEFAULT TRUE,
    first_name STRING NOT NULL,
    last_initial STRING NOT NULL,
    age INT64,
    gender_identity_text STRING,
    city STRING,
    zip STRING,
    geo GEOGRAPHY,
    identifies_lgbtq BOOL,
    substance_recovery BOOL,
    immigration_refugee BOOL,
    is_parenting BOOL,
    legal_history BOOL,
    developmental BOOL,
    mentor_preferences_text STRING,
    goals_text STRING,
    spiritual_alignment STRING, -- "Christian mentor preferred", "Open to spiritual mentor", "Prefer a non-spiritual focus"
    transportation STRING, -- "has_car", "public_transit", "rides_needed"
    communication_pref STRING, -- "text", "phone", "email"
    meeting_frequency STRING, -- "weekly", "biweekly", "monthly"
    schedule_raw STRING,
    schedule_blocks ARRAY<STRING>,
    need_personal_growth INT64,
    need_career_education INT64,
    need_spiritual_growth INT64,
    need_financial_life_skills INT64,
    need_emotional_wellbeing INT64,
    need_relationships_family INT64,
    need_health_wellness INT64,
    support_notes JSON,
    open_to_virtual BOOL,
    hobbies_text STRING,
    career_interests_text STRING,
    activities_text STRING,
    -- Section 6 Profile Sharing Consent
    mentor_share_consent STRING DEFAULT 'all', -- 'all', 'selected', 'none', 'not_asked'
    mentor_share_fields ARRAY<STRING>,
    share_identifications BOOL DEFAULT FALSE, -- Separate opt-in; NOT included by "all"
    mentee_intro_text STRING,
    mentee_consent_name STRING,
    mentee_consent_date DATE,
    mentee_consent_withdrawn_at TIMESTAMP,
    notes_text STRING,
    status STRING DEFAULT 'intake', -- intake, proposed, needs_review, mentor_review, ready_to_offer, offer_sent, mentee_selected, matched, declined_all, expired
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- 5. Mentee Preferences normalized
CREATE TABLE IF NOT EXISTS `{dataset}.mentee_preferences` (
    pref_id STRING NOT NULL,
    mentee_id STRING NOT NULL,
    attribute STRING NOT NULL,
    operator STRING NOT NULL, -- "equals", "contains", "in", "gte", "lte"
    value STRING NOT NULL,
    strength STRING NOT NULL, -- "must_have", "strong", "nice_to_have"
    source STRING DEFAULT 'extracted', -- 'extracted', 'coordinator_added'
    confirmed_by_coordinator BOOL DEFAULT FALSE
);

-- 6. Match Proposals
CREATE TABLE IF NOT EXISTS `{dataset}.match_proposals` (
    proposal_id STRING NOT NULL,
    mentee_id STRING NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    status STRING DEFAULT 'pending_review', -- pending_review, needs_human_review, superseded
    escalation_reason STRING,
    ranked_matches JSON, -- Top 5 with scores, breakdown, explanation, concerns, virtual_first, consent_ok
    excluded JSON, -- Excluded mentors and reasons
    agent_session_id STRING,
    prompt_versions JSON
);

-- 7. Selections (Coordinator chooses 3)
CREATE TABLE IF NOT EXISTS `{dataset}.selections` (
    selection_id STRING NOT NULL,
    proposal_id STRING NOT NULL,
    mentee_id STRING NOT NULL,
    mentor_ids ARRAY<STRING>, -- exactly 3
    override_reason STRING,
    selected_by STRING NOT NULL,
    selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- 8. Mentor Invitations
CREATE TABLE IF NOT EXISTS `{dataset}.mentor_invitations` (
    invitation_id STRING NOT NULL,
    selection_id STRING NOT NULL,
    mentee_id STRING NOT NULL,
    mentor_id STRING NOT NULL,
    rank_in_proposal INT64,
    is_backfill BOOL DEFAULT FALSE,
    message_draft STRING,
    message_final STRING,
    verifier_passed BOOL DEFAULT FALSE,
    approved_by STRING,
    approved_at TIMESTAMP,
    sent_at TIMESTAMP,
    gmail_message_id STRING,
    token_hash STRING,
    expires_at TIMESTAMP,
    reminder_count INT64 DEFAULT 0,
    status STRING DEFAULT 'draft' -- draft, sent, accepted, declined, expired, cancelled
);

-- 9. Mentor Responses (Written only by the portal; single use)
CREATE TABLE IF NOT EXISTS `{dataset}.mentor_responses` (
    invitation_id STRING NOT NULL,
    response STRING NOT NULL, -- 'accept', 'decline'
    decline_reason_private STRING,
    responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- 10. Offers to Mentee
CREATE TABLE IF NOT EXISTS `{dataset}.offers` (
    offer_id STRING NOT NULL,
    mentee_id STRING NOT NULL,
    selection_id STRING NOT NULL,
    mentor_ids ARRAY<STRING>, -- accepted only
    message_draft STRING,
    message_final STRING,
    verifier_passed BOOL DEFAULT FALSE,
    approved_by STRING,
    approved_at TIMESTAMP,
    sent_at TIMESTAMP,
    gmail_message_id STRING,
    token_hash STRING,
    expires_at TIMESTAMP,
    reminder_count INT64 DEFAULT 0,
    status STRING DEFAULT 'draft' -- draft, sent, responded, expired, cancelled
);

-- 11. Offer Responses (Portal only; single use)
CREATE TABLE IF NOT EXISTS `{dataset}.offer_responses` (
    offer_id STRING NOT NULL,
    response STRING NOT NULL, -- 'chose_mentor', 'none_fit'
    chosen_mentor_id STRING,
    none_fit_reason STRING,
    responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- 12. Mentor Holds
CREATE TABLE IF NOT EXISTS `{dataset}.mentor_holds` (
    mentor_id STRING NOT NULL,
    invitation_id STRING NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    released_at TIMESTAMP,
    release_reason STRING -- declined, expired, not_selected, matched, cancelled
);

-- 13. Matches
CREATE TABLE IF NOT EXISTS `{dataset}.matches` (
    match_id STRING NOT NULL,
    mentee_id STRING NOT NULL,
    mentor_id STRING NOT NULL,
    offer_id STRING NOT NULL,
    confirmed_by STRING NOT NULL,
    confirmed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- 14. Agent Sessions and Steps
CREATE TABLE IF NOT EXISTS `{dataset}.agent_sessions` (
    session_id STRING NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    mentee_id STRING,
    status STRING
);

CREATE TABLE IF NOT EXISTS `{dataset}.agent_steps` (
    session_id STRING NOT NULL,
    step_no INT64 NOT NULL,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    agent_name STRING NOT NULL, -- orchestrator, verifier, normalizer, invite_writer, offer_writer, follow_up
    step_type STRING NOT NULL,
    tool_name STRING,
    input JSON,
    output JSON,
    model_id STRING,
    prompt_version STRING,
    tokens_in INT64,
    tokens_out INT64,
    latency_ms INT64,
    bq_bytes_processed INT64,
    error STRING
);

-- 15. Coordinator Actions
CREATE TABLE IF NOT EXISTS `{dataset}.coordinator_actions` (
    action_id STRING NOT NULL,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    actor STRING NOT NULL,
    action STRING NOT NULL, -- select_3, approve_send_invites, approve_backfill, approve_reminder, prepare_offer, approve_send_offer, confirm_match, approve_closure_notes, reject, rerun, override
    entity_id STRING NOT NULL,
    details JSON
);

-- 16. Outbox
CREATE TABLE IF NOT EXISTS `{dataset}.outbox` (
    message_id STRING NOT NULL,
    kind STRING NOT NULL, -- mentor_invite, mentor_reminder, mentee_offer, mentee_reminder, mentor_confirmation, mentor_not_selected
    intended_role STRING NOT NULL,
    intended_first_name STRING NOT NULL,
    delivered_to STRING NOT NULL,
    subject STRING NOT NULL,
    body STRING NOT NULL,
    approved_by STRING NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    delivery_mode STRING NOT NULL,
    gmail_message_id STRING
);

-- 17. Evaluation Runs
CREATE TABLE IF NOT EXISTS `{dataset}.eval_runs` (
    eval_run_id STRING NOT NULL,
    case_id STRING NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    passed BOOL NOT NULL,
    escalation_match BOOL,
    leakage_detected BOOL,
    emails_sent INT64,
    latency_ms INT64,
    tokens_used INT64,
    cost_usd FLOAT64,
    notes STRING
);

-- Views
-- Public View: v_mentor_invite_public (used by response portal)
CREATE OR REPLACE VIEW `{dataset}.v_mentor_invite_public` AS
SELECT
    i.invitation_id,
    i.token_hash,
    i.expires_at,
    i.status AS invitation_status,
    m.mentee_id,
    m.first_name AS mentee_first_name,
    CASE WHEN 'age' IN UNNEST(COALESCE(m.mentor_share_fields, [])) OR m.mentor_share_consent = 'not_asked' THEN m.age ELSE NULL END AS mentee_age,
    CASE WHEN 'city' IN UNNEST(COALESCE(m.mentor_share_fields, [])) OR m.mentor_share_consent = 'not_asked' THEN m.city ELSE NULL END AS mentee_city,
    CASE WHEN 'goals' IN UNNEST(COALESCE(m.mentor_share_fields, [])) OR m.mentor_share_consent = 'not_asked' THEN m.goals_text ELSE NULL END AS mentee_goals,
    m.mentee_intro_text,
    m.mentor_share_consent,
    m.schedule_blocks AS mentee_schedule_blocks,
    m.meeting_frequency AS mentee_meeting_frequency
FROM `{dataset}.mentor_invitations` i
JOIN `{dataset}.mentees` m ON i.mentee_id = m.mentee_id;

-- Public View: v_offer_public (used by response portal)
CREATE OR REPLACE VIEW `{dataset}.v_offer_public` AS
SELECT
    o.offer_id,
    o.token_hash,
    o.expires_at,
    o.status AS offer_status,
    o.mentee_id,
    o.mentor_ids AS accepted_mentor_ids
FROM `{dataset}.offers` o;
