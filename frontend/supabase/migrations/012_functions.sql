-- 012_functions.sql
-- Define database functions for triggers, audits, and business logic

-- 1. Timestamp updater trigger function
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Trigger function to handle new user registration from Supabase Auth
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    v_role_id UUID;
    v_school_id UUID;
    v_role_name TEXT;
BEGIN
    -- Extract role and school from raw_user_meta_data if present
    v_role_name := COALESCE(NEW.raw_user_meta_data->>'role', 'student');
    v_school_id := (NEW.raw_user_meta_data->>'school_id')::UUID;

    -- Fetch the role ID
    SELECT id INTO v_role_id FROM public.roles WHERE name = v_role_name;
    IF v_role_id IS NULL THEN
        SELECT id INTO v_role_id FROM public.roles WHERE name = 'student';
    END IF;

    -- Insert into public.profiles
    INSERT INTO public.profiles (id, email, first_name, last_name, status)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'first_name', ''),
        COALESCE(NEW.raw_user_meta_data->>'last_name', ''),
        'active'
    );

    -- Assign role
    INSERT INTO public.user_roles (profile_id, role_id, school_id)
    VALUES (NEW.id, v_role_id, v_school_id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 3. Soft Delete helper function
CREATE OR REPLACE FUNCTION public.soft_delete_record(
    p_table_name TEXT,
    p_record_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    v_query TEXT;
BEGIN
    IF p_table_name = 'profiles' THEN
        UPDATE public.profiles SET status = 'suspended' WHERE id = p_record_id;
        RETURN TRUE;
    ELSE
        v_query := format('DELETE FROM public.%I WHERE id = %L', p_table_name, p_record_id);
        EXECUTE v_query;
        RETURN TRUE;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. Audit Logging helper function
CREATE OR REPLACE FUNCTION public.create_audit_log(
    p_profile_id UUID,
    p_action TEXT,
    p_table_name TEXT,
    p_record_id UUID,
    p_old_data JSONB,
    p_new_data JSONB,
    p_severity log_severity
)
RETURNS UUID AS $$
DECLARE
    v_log_id UUID;
BEGIN
    INSERT INTO public.audit_logs (profile_id, action, table_name, record_id, old_data, new_data, severity)
    VALUES (p_profile_id, p_action, p_table_name, p_record_id, p_old_data, p_new_data, p_severity)
    RETURNING id INTO v_log_id;
    
    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 5. Notification Generation helper function
CREATE OR REPLACE FUNCTION public.create_notification(
    p_profile_id UUID,
    p_title TEXT,
    p_message TEXT,
    p_type TEXT
)
RETURNS UUID AS $$
DECLARE
    v_notification_id UUID;
BEGIN
    INSERT INTO public.notifications (profile_id, title, message, type)
    VALUES (p_profile_id, p_title, p_message, p_type)
    RETURNING id INTO v_notification_id;
    
    RETURN v_notification_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
