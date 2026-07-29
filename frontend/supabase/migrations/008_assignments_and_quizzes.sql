-- 008_assignments_and_quizzes.sql
-- Create assignments, homework, submissions, quizzes, and quiz attempts tables

CREATE TABLE IF NOT EXISTS public.assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id UUID REFERENCES public.sections(id) ON DELETE CASCADE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    due_date TIMESTAMPTZ NOT NULL,
    max_points INTEGER NOT NULL CHECK (max_points > 0),
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.homework (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id UUID REFERENCES public.sections(id) ON DELETE CASCADE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    due_date TIMESTAMPTZ NOT NULL,
    max_points INTEGER NOT NULL CHECK (max_points > 0),
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.homework_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES public.students(id) ON DELETE CASCADE NOT NULL,
    assignment_id UUID REFERENCES public.assignments(id) ON DELETE CASCADE,
    homework_id UUID REFERENCES public.homework(id) ON DELETE CASCADE,
    content_path TEXT NOT NULL, -- Storage path to PDF or file
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status submission_status NOT NULL DEFAULT 'submitted',
    grade NUMERIC(5, 2) CHECK (grade >= 0.00),
    feedback TEXT,
    graded_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_grade_limit CHECK (grade IS NULL OR grade <= 100.00),
    CONSTRAINT chk_mutually_exclusive CHECK (
        (assignment_id IS NOT NULL AND homework_id IS NULL) OR
        (assignment_id IS NULL AND homework_id IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS public.quizzes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id UUID REFERENCES public.sections(id) ON DELETE CASCADE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    time_limit INTEGER CHECK (time_limit > 0), -- in minutes
    passing_score INTEGER CHECK (passing_score >= 0),
    max_score INTEGER NOT NULL CHECK (max_score > 0),
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_passing_max CHECK (passing_score IS NULL OR passing_score <= max_score)
);

CREATE TABLE IF NOT EXISTS public.quiz_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID REFERENCES public.quizzes(id) ON DELETE CASCADE NOT NULL,
    type question_type NOT NULL DEFAULT 'multiple_choice',
    question_text TEXT NOT NULL,
    options JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of choices
    correct_answer TEXT NOT NULL,
    points INTEGER NOT NULL DEFAULT 1 CHECK (points >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID REFERENCES public.quizzes(id) ON DELETE CASCADE NOT NULL,
    student_id UUID REFERENCES public.students(id) ON DELETE CASCADE NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    answers JSONB NOT NULL DEFAULT '{}'::jsonb, -- question_id -> answer
    score NUMERIC(5, 2) CHECK (score >= 0.00),
    is_passed BOOLEAN,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Add comments for documentation
COMMENT ON TABLE public.assignments IS 'Formal assignments created by teachers';
COMMENT ON TABLE public.homework IS 'Daily homework assignments created by teachers';
COMMENT ON TABLE public.homework_submissions IS 'Student homework and assignment submissions';
COMMENT ON TABLE public.quizzes IS 'Academic quizzes assigned to sections';
COMMENT ON TABLE public.quiz_questions IS 'Individual questions belonging to a quiz';
COMMENT ON TABLE public.quiz_attempts IS 'Student quiz attempts and scores';
