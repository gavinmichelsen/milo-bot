CREATE TABLE IF NOT EXISTS public.recovery_daily_status (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id BIGINT NOT NULL,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    composite_score NUMERIC,
    composite_tier TEXT NOT NULL,
    hrv_status TEXT,
    rhr_status TEXT,
    sleep_duration_status TEXT,
    sleep_efficiency_status TEXT,
    baseline_ready BOOLEAN NOT NULL DEFAULT false,
    should_send BOOLEAN NOT NULL DEFAULT false,
    training_action TEXT,
    message_text TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT recovery_daily_status_tier_check CHECK (composite_tier = ANY (ARRAY['green'::text, 'yellow'::text, 'red'::text, 'insufficient_data'::text]))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_recovery_daily_status_user_snapshot_date ON public.recovery_daily_status(user_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_recovery_daily_status_user_created_at ON public.recovery_daily_status(user_id, created_at DESC);
ALTER TABLE public.recovery_daily_status ENABLE ROW LEVEL SECURITY;
