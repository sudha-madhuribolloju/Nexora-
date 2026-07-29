-- 005_users_directories.sql
-- Create teachers, students, parents, and student_parents directories

CREATE TABLE IF NOT EXISTS public.teachers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL UNIQUE,
    school_id UUID REFERENCES public.schools(id) ON DELETE CASCADE NOT NULL,
    department_id UUID REFERENCES public.departments(id) ON DELETE SET NULL,
    qualification TEXT,
    bio TEXT,
    joined_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL UNIQUE,
    school_id UUID REFERENCES public.schools(id) ON DELETE CASCADE NOT NULL,
    roll_number TEXT NOT NULL,
    date_of_birth DATE,
    gender TEXT,
    emergency_contact JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (school_id, roll_number)
);

CREATE TABLE IF NOT EXISTS public.parents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL UNIQUE,
    school_id UUID REFERENCES public.schools(id) ON DELETE CASCADE NOT NULL,
    occupation TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.student_parents (
    student_id UUID REFERENCES public.students(id) ON DELETE CASCADE NOT NULL,
    parent_id UUID REFERENCES public.parents(id) ON DELETE CASCADE NOT NULL,
    relationship relationship_type NOT NULL DEFAULT 'other',
    is_primary_contact BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (student_id, parent_id)
);

-- Add comments for documentation
COMMENT ON TABLE public.teachers IS 'Professional profiles for teachers linked to departments';
COMMENT ON TABLE public.students IS 'Student records containing roll numbers and emergency details';
COMMENT ON TABLE public.parents IS 'Parent and guardian contact directories';
COMMENT ON TABLE public.student_parents IS 'Junction table mapping students to their parents/guardians';
