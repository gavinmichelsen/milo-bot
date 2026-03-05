CREATE TABLE IF NOT EXISTS public.nutrition_states (
    user_id BIGINT PRIMARY KEY,
    phase TEXT NOT NULL,
    nutrition_mode TEXT NOT NULL DEFAULT 'tracked',
    current_calorie_target INTEGER,
    current_protein_target_g INTEGER,
    estimated_tdee INTEGER,
    adaptive_tdee INTEGER,
    working_tdee INTEGER,
    goal_rate_pct_per_week NUMERIC,
    started_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT nutrition_states_phase_check CHECK (phase = ANY (ARRAY['cut'::text, 'maintenance'::text, 'lean_bulk'::text])),
    CONSTRAINT nutrition_states_mode_check CHECK (nutrition_mode = ANY (ARRAY['tracked'::text, 'ad_libitum'::text]))
);

CREATE TABLE IF NOT EXISTS public.nutrition_state_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id BIGINT NOT NULL,
    phase TEXT NOT NULL,
    nutrition_mode TEXT NOT NULL DEFAULT 'tracked',
    calorie_target INTEGER,
    protein_target_g INTEGER,
    estimated_tdee INTEGER,
    adaptive_tdee INTEGER,
    working_tdee INTEGER,
    goal_rate_pct_per_week NUMERIC,
    reason_code TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT nutrition_state_history_phase_check CHECK (phase = ANY (ARRAY['cut'::text, 'maintenance'::text, 'lean_bulk'::text])),
    CONSTRAINT nutrition_state_history_mode_check CHECK (nutrition_mode = ANY (ARRAY['tracked'::text, 'ad_libitum'::text]))
);

CREATE INDEX IF NOT EXISTS idx_nutrition_state_history_user_created_at ON public.nutrition_state_history(user_id, created_at DESC);
ALTER TABLE public.nutrition_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrition_state_history ENABLE ROW LEVEL SECURITY;
