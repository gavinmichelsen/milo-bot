CREATE TABLE IF NOT EXISTS public.oauth_states (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    state TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ DEFAULT now() + INTERVAL '10 minutes'
);

CREATE INDEX IF NOT EXISTS idx_oauth_states_state ON public.oauth_states(state);
ALTER TABLE public.oauth_states DISABLE ROW LEVEL SECURITY;

CREATE TABLE IF NOT EXISTS public.whoop_tokens (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    telegram_id BIGINT NOT NULL UNIQUE,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    scopes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_whoop_tokens_telegram_id ON public.whoop_tokens(telegram_id);
ALTER TABLE public.whoop_tokens DISABLE ROW LEVEL SECURITY;
