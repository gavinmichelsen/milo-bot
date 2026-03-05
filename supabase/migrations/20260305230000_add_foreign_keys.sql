-- Add foreign key constraints to snapshot and state tables
-- to prevent orphaned data when users are removed.

ALTER TABLE public.whoop_snapshots
    ADD CONSTRAINT fk_whoop_snapshots_user
    FOREIGN KEY (user_id) REFERENCES public.users(telegram_id) ON DELETE CASCADE;

ALTER TABLE public.body_metrics
    ADD CONSTRAINT fk_body_metrics_user
    FOREIGN KEY (user_id) REFERENCES public.users(telegram_id) ON DELETE CASCADE;

ALTER TABLE public.nutrition_states
    ADD CONSTRAINT fk_nutrition_states_user
    FOREIGN KEY (user_id) REFERENCES public.users(telegram_id) ON DELETE CASCADE;

ALTER TABLE public.recovery_daily_status
    ADD CONSTRAINT fk_recovery_daily_status_user
    FOREIGN KEY (user_id) REFERENCES public.users(telegram_id) ON DELETE CASCADE;

ALTER TABLE public.user_profiles
    ADD CONSTRAINT fk_user_profiles_user
    FOREIGN KEY (user_id) REFERENCES public.users(telegram_id) ON DELETE CASCADE;
