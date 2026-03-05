CREATE TABLE IF NOT EXISTS public.user_profiles (
    user_id BIGINT PRIMARY KEY,
    sex TEXT,
    age_years INTEGER,
    height_cm NUMERIC,
    body_weight_lbs NUMERIC,
    estimated_body_fat_pct NUMERIC,
    activity_multiplier NUMERIC DEFAULT 1.55,
    primary_goal TEXT DEFAULT 'maintain',
    experience_level TEXT DEFAULT 'intermediate',
    training_days_per_week INTEGER,
    nutrition_mode TEXT DEFAULT 'tracked',
    target_wake_time TEXT,
    target_bedtime TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT user_profiles_goal_check CHECK (primary_goal = ANY (ARRAY['fat_loss'::text, 'maintain'::text, 'muscle_gain'::text, 'recomp'::text])),
    CONSTRAINT user_profiles_experience_check CHECK (experience_level = ANY (ARRAY['beginner'::text, 'intermediate'::text, 'advanced'::text])),
    CONSTRAINT user_profiles_nutrition_mode_check CHECK (nutrition_mode = ANY (ARRAY['tracked'::text, 'ad_libitum'::text]))
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_goal ON public.user_profiles(primary_goal);
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
