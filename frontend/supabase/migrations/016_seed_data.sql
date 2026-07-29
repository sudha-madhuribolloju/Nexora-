-- 016_seed_data.sql
-- Seed database with realistic, production-ready sample data
-- All UUIDs are valid RFC4122 hexadecimal-only strings.

BEGIN;

-------------------------------------------------------------------------------
-- 1. Seed Subscription Plans
-------------------------------------------------------------------------------
INSERT INTO public.subscription_plans (id, name, description, price, currency, interval, features, is_active)
VALUES 
  ('a1111111-1111-1111-1111-111111111111', 'Free Tier', 'Basic classroom features for small schools', 0.00, 'USD', 'month', '["students_limit:50", "courses_limit:5", "ai_tokens_limit:10000"]'::jsonb, true),
  ('a2222222-2222-2222-2222-222222222222', 'Pro School', 'Advanced features for growing educational institutions', 199.00, 'USD', 'month', '["students_limit:500", "courses_limit:50", "ai_tokens_limit:1000000", "custom_branding:true"]'::jsonb, true),
  ('a3333333-3333-3333-3333-333333333333', 'Enterprise', 'Unlimited scale and dedicated AI agents for large schools', 499.00, 'USD', 'month', '["students_limit:unlimited", "courses_limit:unlimited", "ai_tokens_limit:unlimited", "dedicated_support:true"]'::jsonb, true)
ON CONFLICT (id) DO NOTHING;

-------------------------------------------------------------------------------
-- 2. Seed School Tenant
-------------------------------------------------------------------------------
INSERT INTO public.schools (id, name, slug, logo_url, address, phone, email, settings)
VALUES (
    '11111111-1111-1111-1111-111111111111', 
    'Nexora Academy', 
    'nexora-academy', 
    'https://assets.nexora.edu/logo.png', 
    '100 Innovation Way, Boston, MA 02110', 
    '+1 (617) 555-0199', 
    'info@nexora.edu', 
    '{"theme": "dark", "allowed_email_domains": ["nexora.edu"]}'::jsonb
) ON CONFLICT (id) DO NOTHING;

-- Seed Settings for the School
INSERT INTO public.settings (school_id, config)
VALUES ('11111111-1111-1111-1111-111111111111', '{"timezone": "America/New_York", "grading_system": "GPA"}'::jsonb)
ON CONFLICT (school_id) DO NOTHING;

-- Seed Subscription for the School
INSERT INTO public.subscriptions (id, school_id, plan_id, status, current_period_start, current_period_end)
VALUES (
    'b1111111-1111-1111-1111-111111111111', 
    '11111111-1111-1111-1111-111111111111', 
    'a3333333-3333-3333-3333-333333333333', -- Enterprise
    'active', 
    now(), 
    now() + INTERVAL '1 month'
) ON CONFLICT (id) DO NOTHING;

-------------------------------------------------------------------------------
-- 3. Seed Departments & Academic Years
-------------------------------------------------------------------------------
INSERT INTO public.departments (id, school_id, name, description)
VALUES 
  ('d1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'Science', 'Department of Natural and Physical Sciences'),
  ('d2222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111', 'Mathematics', 'Department of Pure and Applied Mathematics')
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.academic_years (id, school_id, name, start_date, end_date, is_active)
VALUES (
    'c1111111-1111-1111-1111-111111111111', 
    '11111111-1111-1111-1111-111111111111', 
    '2025-2026', 
    '2025-09-01', 
    '2026-06-15', 
    true
) ON CONFLICT (id) DO NOTHING;

-------------------------------------------------------------------------------
-- 4. Seed Auth Users (Triggers Profile & User Role Creation)
-------------------------------------------------------------------------------

-- 4.1 Super Admin
INSERT INTO auth.users (id, email, encrypted_password, email_confirmed_at, raw_app_meta_data, raw_user_meta_data, aud, role)
VALUES (
    '00000000-0000-0000-0000-000000000001', 
    'superadmin@nexora.edu', 
    '$2a$10$7EqJtDQegSLWhA4W9N.TxeZ.R8z/7j.LhC.mYkZqE1J3L9X0v.mDG', -- crypt('Password123')
    now(), 
    '{"provider":"email","providers":["email"]}'::jsonb, 
    '{"first_name":"Alex","last_name":"Mercer","role":"super_admin"}'::jsonb, 
    'authenticated', 
    'authenticated'
) ON CONFLICT (id) DO NOTHING;

-- 4.2 School Admin
INSERT INTO auth.users (id, email, encrypted_password, email_confirmed_at, raw_app_meta_data, raw_user_meta_data, aud, role)
VALUES (
    '00000000-0000-0000-0000-000000000002', 
    'admin@nexora.edu', 
    '$2a$10$7EqJtDQegSLWhA4W9N.TxeZ.R8z/7j.LhC.mYkZqE1J3L9X0v.mDG', 
    now(), 
    '{"provider":"email","providers":["email"]}'::jsonb, 
    '{"first_name":"Sarah","last_name":"Conner","role":"school_admin","school_id":"11111111-1111-1111-1111-111111111111"}'::jsonb, 
    'authenticated', 
    'authenticated'
) ON CONFLICT (id) DO NOTHING;

-- 4.3 Teacher
INSERT INTO auth.users (id, email, encrypted_password, email_confirmed_at, raw_app_meta_data, raw_user_meta_data, aud, role)
VALUES (
    '00000000-0000-0000-0000-000000000003', 
    'teacher@nexora.edu', 
    '$2a$10$7EqJtDQegSLWhA4W9N.TxeZ.R8z/7j.LhC.mYkZqE1J3L9X0v.mDG', 
    now(), 
    '{"provider":"email","providers":["email"]}'::jsonb, 
    '{"first_name":"John","last_name":"Keating","role":"teacher","school_id":"11111111-1111-1111-1111-111111111111"}'::jsonb, 
    'authenticated', 
    'authenticated'
) ON CONFLICT (id) DO NOTHING;

-- 4.4 Student
INSERT INTO auth.users (id, email, encrypted_password, email_confirmed_at, raw_app_meta_data, raw_user_meta_data, aud, role)
VALUES (
    '00000000-0000-0000-0000-000000000004', 
    'student@nexora.edu', 
    '$2a$10$7EqJtDQegSLWhA4W9N.TxeZ.R8z/7j.LhC.mYkZqE1J3L9X0v.mDG', 
    now(), 
    '{"provider":"email","providers":["email"]}'::jsonb, 
    '{"first_name":"Jane","last_name":"Doe","role":"student","school_id":"11111111-1111-1111-1111-111111111111"}'::jsonb, 
    'authenticated', 
    'authenticated'
) ON CONFLICT (id) DO NOTHING;

-- 4.5 Parent
INSERT INTO auth.users (id, email, encrypted_password, email_confirmed_at, raw_app_meta_data, raw_user_meta_data, aud, role)
VALUES (
    '00000000-0000-0000-0000-000000000005', 
    'parent@nexora.edu', 
    '$2a$10$7EqJtDQegSLWhA4W9N.TxeZ.R8z/7j.LhC.mYkZqE1J3L9X0v.mDG', 
    now(), 
    '{"provider":"email","providers":["email"]}'::jsonb, 
    '{"first_name":"Robert","last_name":"Doe","role":"parent","school_id":"11111111-1111-1111-1111-111111111111"}'::jsonb, 
    'authenticated', 
    'authenticated'
) ON CONFLICT (id) DO NOTHING;

-------------------------------------------------------------------------------
-- 5. Seed Core Entity Records (Teachers, Students, Parents)
-------------------------------------------------------------------------------
INSERT INTO public.teachers (id, profile_id, school_id, department_id, qualification, bio)
VALUES (
    'e1111111-1111-1111-1111-111111111111', 
    '00000000-0000-0000-0000-000000000003', 
    '11111111-1111-1111-1111-111111111111', 
    'd1111111-1111-1111-1111-111111111111', -- Science
    'Ph.D. in Astrophysics', 
    'Passionate about teaching physics and exploring the cosmos.'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO public.students (id, profile_id, school_id, roll_number, date_of_birth, gender)
VALUES (
    'f1111111-1111-1111-1111-111111111111', 
    '00000000-0000-0000-0000-000000000004', 
    '11111111-1111-1111-1111-111111111111', 
    'NEX-2025-0042', 
    '2010-05-14', 
    'Female'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO public.parents (id, profile_id, school_id, occupation)
VALUES (
    'ba111111-1111-1111-1111-111111111111', 
    '00000000-0000-0000-0000-000000000005', 
    '11111111-1111-1111-1111-111111111111', 
    'Software Architect'
) ON CONFLICT (id) DO NOTHING;

-- Map student to parent
INSERT INTO public.student_parents (student_id, parent_id, relationship, is_primary_contact)
VALUES (
    'f1111111-1111-1111-1111-111111111111', 
    'ba111111-1111-1111-1111-111111111111', 
    'father', 
    true
) ON CONFLICT (student_id, parent_id) DO NOTHING;

-------------------------------------------------------------------------------
-- 6. Seed Academics (Courses, Subjects, Classrooms, Sections)
-------------------------------------------------------------------------------
INSERT INTO public.courses (id, school_id, academic_year_id, name, code, description)
VALUES (
    'bc111111-1111-1111-1111-111111111111', 
    '11111111-1111-1111-1111-111111111111', 
    'c1111111-1111-1111-1111-111111111111', 
    'Grade 10 Physics', 
    'PHYS-10', 
    'Introduction to Classical Mechanics and Thermodynamics'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO public.subjects (id, course_id, name, description)
VALUES (
    'bd111111-1111-1111-1111-111111111111', 
    'bc111111-1111-1111-1111-111111111111', 
    'Thermodynamics', 
    'Study of heat, work, temperature, and statistical mechanics'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO public.classrooms (id, school_id, name, capacity, type)
VALUES (
    'be111111-1111-1111-1111-111111111111', 
    '11111111-1111-1111-1111-111111111111', 
    'Room 302', 
    30, 
    'physical'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO public.sections (id, course_id, classroom_id, teacher_id, name)
VALUES (
    'bf111111-1111-1111-1111-111111111111', 
    'bc111111-1111-1111-1111-111111111111', 
    'be111111-1111-1111-1111-111111111111', 
    'e1111111-1111-1111-1111-111111111111', -- Teacher John Keating
    'Section A'
) ON CONFLICT (id) DO NOTHING;

-- Enroll the student
INSERT INTO public.enrollments (student_id, section_id, status)
VALUES (
    'f1111111-1111-1111-1111-111111111111', 
    'bf111111-1111-1111-1111-111111111111', 
    'active'
) ON CONFLICT (student_id, section_id) DO NOTHING;

-------------------------------------------------------------------------------
-- 7. Seed Sessions, Lecture Notes, Assignments, Quizzes & AI Agent
-------------------------------------------------------------------------------
INSERT INTO public.sessions (id, section_id, subject_id, title, description, session_date, start_time, end_time)
VALUES (
    'ca111111-1111-1111-1111-111111111111', 
    'bf111111-1111-1111-1111-111111111111', 
    'bd111111-1111-1111-1111-111111111111', -- Thermodynamics
    'First Law of Thermodynamics', 
    'Introduction to internal energy, heat, and work done.', 
    '2026-06-30', 
    '09:00:00', 
    '10:30:00'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO public.attendance (session_id, student_id, status, remarks, marked_by)
VALUES (
    'ca111111-1111-1111-1111-111111111111', 
    'f1111111-1111-1111-1111-111111111111', 
    'present', 
    'On time and highly active.', 
    '00000000-0000-0000-0000-000000000003'
) ON CONFLICT (session_id, student_id) DO NOTHING;

INSERT INTO public.lecture_notes (id, session_id, title, content, created_by)
VALUES (
    'cb111111-1111-1111-1111-111111111111', 
    'ca111111-1111-1111-1111-111111111111', 
    'First Law of Thermodynamics Notes', 
    'The First Law of Thermodynamics states that energy cannot be created or destroyed, only transformed. Mathematically: dU = dQ - dW...', 
    '00000000-0000-0000-0000-000000000003'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO public.assignments (id, section_id, title, description, due_date, max_points, created_by)
VALUES (
    'cc111111-1111-1111-1111-111111111111', 
    'bf111111-1111-1111-1111-111111111111', 
    'Thermodynamics Problem Set 1', 
    'Solve the 5 problems on work done during isobaric and isothermal processes.', 
    '2026-07-05 23:59:59+00', 
    100, 
    '00000000-0000-0000-0000-000000000003'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO public.quizzes (id, section_id, title, description, time_limit, passing_score, max_score, created_by)
VALUES (
    'cd111111-1111-1111-1111-111111111111', 
    'bf111111-1111-1111-1111-111111111111', 
    'Thermodynamics Pop Quiz', 
    'Quick check on the First Law of Thermodynamics.', 
    15, 
    6, 
    10, 
    '00000000-0000-0000-0000-000000000003'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO public.quiz_questions (id, quiz_id, type, question_text, options, correct_answer, points)
VALUES (
    'ce111111-1111-1111-1111-111111111111', 
    'cd111111-1111-1111-1111-111111111111', 
    'multiple_choice', 
    'What is the formula for the First Law of Thermodynamics?', 
    '["dU = dQ - dW", "dU = dQ + dW", "dQ = dU - dW", "dW = dU + dQ"]'::jsonb, 
    'dU = dQ - dW', 
    5
) ON CONFLICT (id) DO NOTHING;

INSERT INTO public.ai_agents (id, school_id, name, system_prompt, model, is_active)
VALUES (
    'cf111111-1111-1111-1111-111111111111', 
    '11111111-1111-1111-1111-111111111111', 
    'Newton - Physics Tutor', 
    'You are Newton, an AI tutor specialized in Grade 10 Physics. Help students understand physics concepts step-by-step. Do not give the answers directly, guide them to the solution.', 
    'gpt-4o', 
    true
) ON CONFLICT (id) DO NOTHING;

COMMIT;

