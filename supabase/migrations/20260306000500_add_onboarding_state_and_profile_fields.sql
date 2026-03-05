ALTER TABLE public.user_profiles
    ADD COLUMN IF NOT EXISTS training_age_months INTEGER,
    ADD COLUMN IF NOT EXISTS injury_notes TEXT,
    ADD COLUMN IF NOT EXISTS injury_details TEXT,
    ADD COLUMN IF NOT EXISTS injury_status TEXT,
    ADD COLUMN IF NOT EXISTS equipment_access TEXT,
    ADD COLUMN IF NOT EXISTS emphasis_preference TEXT DEFAULT 'balanced',
    ADD COLUMN IF NOT EXISTS communication_preference TEXT,
    ADD COLUMN IF NOT EXISTS age_under_18 BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS medical_disclaimer_acknowledged BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS medical_clearance_confirmed BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS uses_whoop BOOLEAN,
    ADD COLUMN IF NOT EXISTS uses_withings BOOLEAN,
    ADD COLUMN IF NOT EXISTS onboarding_status TEXT DEFAULT 'not_started',
    ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS public.onboarding_states (
    user_id BIGINT PRIMARY KEY,
    status TEXT DEFAULT 'not_started',
    current_step TEXT,
    profile_data JSONB DEFAULT '{}'::jsonb,
    last_question TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    CONSTRAINT fk_onboarding_states_user
        FOREIGN KEY (user_id) REFERENCES public.users(telegram_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_onboarding_states_status ON public.onboarding_states(status);
ALTER TABLE public.onboarding_states ENABLE ROW LEVEL SECURITY;
