-- 004_profiles_and_rbac.sql
-- Create profiles and RBAC tables, and seed default roles and permissions

CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    avatar_url TEXT,
    status user_status NOT NULL DEFAULT 'active',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.role_permissions (
    role_id UUID REFERENCES public.roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES public.permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS public.user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    role_id UUID REFERENCES public.roles(id) ON DELETE CASCADE NOT NULL,
    school_id UUID REFERENCES public.schools(id) ON DELETE CASCADE, -- Can be NULL for super admins
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (profile_id, role_id, school_id)
);

-- Seed default roles
INSERT INTO public.roles (name, description) VALUES
('super_admin', 'Global system administrator with unrestricted access'),
('school_admin', 'Administrative head of a specific school'),
('teacher', 'Academic instructor managing courses, sections, and grades'),
('student', 'Enrolled learner participating in courses and assignments'),
('parent', 'Parent or legal guardian tracking student progress')
ON CONFLICT (name) DO NOTHING;

-- Seed basic permissions
INSERT INTO public.permissions (name, description) VALUES
('school:create', 'Create new schools'),
('school:edit', 'Edit school details'),
('school:delete', 'Delete schools'),
('school:view_analytics', 'View school-wide analytics'),
('user:create', 'Create new user profiles'),
('user:edit', 'Modify user profiles'),
('user:delete', 'Suspend or delete user profiles'),
('course:create', 'Create courses and subjects'),
('course:edit', 'Edit courses and subjects'),
('course:delete', 'Delete courses and subjects'),
('section:create', 'Create sections and assign teachers'),
('section:edit', 'Modify section parameters'),
('attendance:mark', 'Mark student attendance'),
('attendance:view', 'View attendance records'),
('grade:write', 'Grade assignments and quizzes'),
('grade:view', 'View grades'),
('assignment:create', 'Create and publish assignments and homework'),
('quiz:create', 'Create quizzes and questions'),
('quiz:attempt', 'Attempt quizzes'),
('document:upload', 'Upload educational materials or administrative documents'),
('ai:chat', 'Interact with AI classroom assistants'),
('ai:generate', 'Use AI to generate quizzes or summaries')
ON CONFLICT (name) DO NOTHING;

-- Map permissions to roles
DO $$
DECLARE
    role_sa_id UUID := (SELECT id FROM public.roles WHERE name = 'super_admin');
    role_sadmin_id UUID := (SELECT id FROM public.roles WHERE name = 'school_admin');
    role_teacher_id UUID := (SELECT id FROM public.roles WHERE name = 'teacher');
    role_student_id UUID := (SELECT id FROM public.roles WHERE name = 'student');
    role_parent_id UUID := (SELECT id FROM public.roles WHERE name = 'parent');
    perm_id UUID;
BEGIN
    -- Super Admin gets all permissions
    FOR perm_id IN SELECT id FROM public.permissions LOOP
        INSERT INTO public.role_permissions (role_id, permission_id) VALUES (role_sa_id, perm_id) ON CONFLICT DO NOTHING;
    END LOOP;

    -- School Admin permissions
    INSERT INTO public.role_permissions (role_id, permission_id)
    SELECT role_sadmin_id, id FROM public.permissions 
    WHERE name NOT IN ('school:create', 'school:delete')
    ON CONFLICT DO NOTHING;

    -- Teacher permissions
    INSERT INTO public.role_permissions (role_id, permission_id)
    SELECT role_teacher_id, id FROM public.permissions 
    WHERE name IN ('attendance:mark', 'attendance:view', 'grade:write', 'grade:view', 'assignment:create', 'quiz:create', 'document:upload', 'ai:chat', 'ai:generate')
    ON CONFLICT DO NOTHING;

    -- Student permissions
    INSERT INTO public.role_permissions (role_id, permission_id)
    SELECT role_student_id, id FROM public.permissions 
    WHERE name IN ('attendance:view', 'grade:view', 'quiz:attempt', 'document:upload', 'ai:chat')
    ON CONFLICT DO NOTHING;

    -- Parent permissions
    INSERT INTO public.role_permissions (role_id, permission_id)
    SELECT role_parent_id, id FROM public.permissions 
    WHERE name IN ('attendance:view', 'grade:view')
    ON CONFLICT DO NOTHING;
END $$;

-- Add comments for documentation
COMMENT ON TABLE public.profiles IS 'User profiles extending auth.users';
COMMENT ON TABLE public.roles IS 'User roles for access control';
COMMENT ON TABLE public.permissions IS 'Individual granular action permissions';
COMMENT ON TABLE public.role_permissions IS 'Junction table mapping permissions to roles';
COMMENT ON TABLE public.user_roles IS 'Junction table assigning roles to profiles within a school tenant';
