CREATE OR REPLACE FUNCTION public.get_user_school_id(user_id UUID)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_school_id UUID;
BEGIN
    SELECT school_id
    INTO v_school_id
    FROM public.user_roles
    WHERE profile_id = user_id
      AND school_id IS NOT NULL
    LIMIT 1;

    RETURN v_school_id;
END;
$$;