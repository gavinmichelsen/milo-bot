-- Disable RLS on server-only tables.
-- These tables are only accessed by the bot backend (service role key),
-- never by browser clients. RLS without policies blocks all access
-- when using the anon key.

ALTER TABLE public.onboarding_states DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrition_states DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrition_state_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.recovery_daily_status DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.whoop_snapshots DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.body_metrics DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.workouts DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history DISABLE ROW LEVEL SECURITY;
