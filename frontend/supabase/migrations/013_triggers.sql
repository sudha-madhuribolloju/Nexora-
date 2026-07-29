-- 013_triggers.sql
-- Attach triggers for signups, timestamps, and audit logs

-------------------------------------------------------------------------------
-- 1. New User Registration Trigger
-------------------------------------------------------------------------------

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-------------------------------------------------------------------------------
-- 2. Automatic Timestamp (updated_at) Triggers
-------------------------------------------------------------------------------

DO $$
DECLARE
    t_name RECORD;
BEGIN
    FOR t_name IN 
        SELECT table_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND column_name = 'updated_at' 
          AND table_name NOT IN ('student_parents') -- Composite primary key / manual updates
    LOOP
        EXECUTE format('
            CREATE TRIGGER trg_update_updated_at_%I
            BEFORE UPDATE ON public.%I
            FOR EACH ROW
            EXECUTE FUNCTION public.update_updated_at_column();
        ', t_name.table_name, t_name.table_name);
    END LOOP;
END $$;

-------------------------------------------------------------------------------
-- 3. Sensitive Audit Logging Triggers
-------------------------------------------------------------------------------

-- 3.1 Audit Trigger Function
CREATE OR REPLACE FUNCTION public.process_audit_trigger()
RETURNS TRIGGER AS $$
DECLARE
    v_old_data JSONB := NULL;
    v_new_data JSONB := NULL;
    v_action TEXT := TG_OP;
    v_record_id UUID;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_old_data := to_jsonb(OLD);
        v_record_id := OLD.id;
    ELSIF TG_OP = 'UPDATE' THEN
        v_old_data := to_jsonb(OLD);
        v_new_data := to_jsonb(NEW);
        v_record_id := NEW.id;
    ELSIF TG_OP = 'INSERT' THEN
        v_new_data := to_jsonb(NEW);
        v_record_id := NEW.id;
    END IF;

    -- Log the audit record
    PERFORM public.create_audit_log(
        auth.uid(),
        v_action,
        TG_TABLE_NAME::text,
        v_record_id,
        v_old_data,
        v_new_data,
        CASE 
            WHEN TG_TABLE_NAME = 'user_roles' THEN 'security'::log_severity
            WHEN TG_TABLE_NAME = 'payments' THEN 'critical'::log_severity
            ELSE 'info'::log_severity
        END
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 3.2 Attach Audit Triggers to Sensitive Tables
CREATE TRIGGER audit_user_roles
    AFTER INSERT OR UPDATE OR DELETE ON public.user_roles
    FOR EACH ROW EXECUTE FUNCTION public.process_audit_trigger();

CREATE TRIGGER audit_payments
    AFTER INSERT OR UPDATE OR DELETE ON public.payments
    FOR EACH ROW EXECUTE FUNCTION public.process_audit_trigger();

CREATE TRIGGER audit_subscriptions
    AFTER INSERT OR UPDATE OR DELETE ON public.subscriptions
    FOR EACH ROW EXECUTE FUNCTION public.process_audit_trigger();

CREATE TRIGGER audit_enrollments
    AFTER INSERT OR UPDATE OR DELETE ON public.enrollments
    FOR EACH ROW EXECUTE FUNCTION public.process_audit_trigger();
