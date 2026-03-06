-- Add CHECK constraints for enum and range fields on user_profiles.
-- Uses DO blocks to safely skip constraints that already exist.

DO $$ BEGIN
    ALTER TABLE public.user_profiles ADD CONSTRAINT user_profiles_sex_check
        CHECK (sex = ANY (ARRAY['male'::text, 'female'::text]));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE public.user_profiles ADD CONSTRAINT user_profiles_equipment_check
        CHECK (equipment_access = ANY (ARRAY['full_gym'::text, 'home_gym'::text, 'minimal'::text]));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE public.user_profiles ADD CONSTRAINT user_profiles_emphasis_check
        CHECK (emphasis_preference = ANY (ARRAY['balanced'::text, 'upper'::text, 'lower'::text, 'arms'::text]));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE public.user_profiles ADD CONSTRAINT user_profiles_communication_check
        CHECK (communication_preference = ANY (ARRAY['daily'::text, 'training_days_only'::text, 'weekly'::text]));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE public.user_profiles ADD CONSTRAINT user_profiles_injury_status_check
        CHECK (injury_status = ANY (ARRAY['none'::text, 'has_injury'::text, 'diagnosed_or_rehabbed'::text, 'movement_specific'::text]));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE public.user_profiles ADD CONSTRAINT user_profiles_age_check
        CHECK (age_years >= 13 AND age_years <= 100);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE public.user_profiles ADD CONSTRAINT user_profiles_height_check
        CHECK (height_cm >= 100 AND height_cm <= 250);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE public.user_profiles ADD CONSTRAINT user_profiles_weight_check
        CHECK (body_weight_lbs >= 50 AND body_weight_lbs <= 700);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE public.user_profiles ADD CONSTRAINT user_profiles_training_days_check
        CHECK (training_days_per_week >= 1 AND training_days_per_week <= 7);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
