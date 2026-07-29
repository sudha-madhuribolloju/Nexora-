-- 015_indexes.sql
-- Create database indexes for performance optimization

-------------------------------------------------------------------------------
-- 1. B-Tree Indexes on Foreign Keys (Optimizes Joins and Cascade Deletes)
-------------------------------------------------------------------------------

-- School ID Indexes
CREATE INDEX IF NOT EXISTS idx_departments_school_id ON public.departments(school_id);
CREATE INDEX IF NOT EXISTS idx_academic_years_school_id ON public.academic_years(school_id);
CREATE INDEX IF NOT EXISTS idx_courses_school_id ON public.courses(school_id);
CREATE INDEX IF NOT EXISTS idx_classrooms_school_id ON public.classrooms(school_id);
CREATE INDEX IF NOT EXISTS idx_students_school_id ON public.students(school_id);
CREATE INDEX IF NOT EXISTS idx_parents_school_id ON public.parents(school_id);
CREATE INDEX IF NOT EXISTS idx_teachers_school_id ON public.teachers(school_id);
CREATE INDEX IF NOT EXISTS idx_ai_agents_school_id ON public.ai_agents(school_id);
CREATE INDEX IF NOT EXISTS idx_documents_school_id ON public.documents(school_id);
CREATE INDEX IF NOT EXISTS idx_announcements_school_id ON public.announcements(school_id);
CREATE INDEX IF NOT EXISTS idx_reports_school_id ON public.reports(school_id);
CREATE INDEX IF NOT EXISTS idx_analytics_school_id ON public.analytics(school_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_school_id ON public.api_keys(school_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_school_id ON public.subscriptions(school_id);

-- User Profiles / Roles Indexes
CREATE INDEX IF NOT EXISTS idx_user_roles_profile_id ON public.user_roles(profile_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON public.user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_school_id ON public.user_roles(school_id);

-- Teacher and Student Indexes
CREATE INDEX IF NOT EXISTS idx_teachers_profile_id ON public.teachers(profile_id);
CREATE INDEX IF NOT EXISTS idx_students_profile_id ON public.students(profile_id);
CREATE INDEX IF NOT EXISTS idx_parents_profile_id ON public.parents(profile_id);
CREATE INDEX IF NOT EXISTS idx_sections_teacher_id ON public.sections(teacher_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_student_id ON public.enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_section_id ON public.enrollments(section_id);

-- Course & Subject Indexes
CREATE INDEX IF NOT EXISTS idx_subjects_course_id ON public.subjects(course_id);
CREATE INDEX IF NOT EXISTS idx_sections_course_id ON public.sections(course_id);
CREATE INDEX IF NOT EXISTS idx_sessions_section_id ON public.sessions(section_id);
CREATE INDEX IF NOT EXISTS idx_sessions_subject_id ON public.sessions(subject_id);

-- Attendance and Coursework Indexes
CREATE INDEX IF NOT EXISTS idx_attendance_session_id ON public.attendance(session_id);
CREATE INDEX IF NOT EXISTS idx_attendance_student_id ON public.attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_assignments_section_id ON public.assignments(section_id);
CREATE INDEX IF NOT EXISTS idx_homework_section_id ON public.homework(section_id);
CREATE INDEX IF NOT EXISTS idx_homework_submissions_student_id ON public.homework_submissions(student_id);
CREATE INDEX IF NOT EXISTS idx_homework_submissions_assignment_id ON public.homework_submissions(assignment_id);
CREATE INDEX IF NOT EXISTS idx_homework_submissions_homework_id ON public.homework_submissions(homework_id);

-- Quizzes Indexes
CREATE INDEX IF NOT EXISTS idx_quizzes_section_id ON public.quizzes(section_id);
CREATE INDEX IF NOT EXISTS idx_quiz_questions_quiz_id ON public.quiz_questions(quiz_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_quiz_id ON public.quiz_attempts(quiz_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_student_id ON public.quiz_attempts(student_id);

-- AI Chat & Documents Indexes
CREATE INDEX IF NOT EXISTS idx_chat_conversations_profile_id ON public.chat_conversations(profile_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation_id ON public.chat_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_document_id ON public.embeddings(document_id);

-- Billing & SaaS Indexes
CREATE INDEX IF NOT EXISTS idx_payments_subscription_id ON public.payments(subscription_id);
CREATE INDEX IF NOT EXISTS idx_invoices_payment_id ON public.invoices(payment_id);

-------------------------------------------------------------------------------
-- 2. GIN Trigram Indexes for Fast Fuzzy Text Searching
-------------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_profiles_names_trgm ON public.profiles USING gin ((first_name || ' ' || last_name) gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_courses_name_code_trgm ON public.courses USING gin (name gin_trgm_ops, code gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_documents_title_trgm ON public.documents USING gin (title gin_trgm_ops);

-------------------------------------------------------------------------------
-- 3. HNSW Vector Index (Optimizes Cosine Similarity for pgvector)
-------------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_embeddings_vector_hnsw 
ON public.embeddings USING hnsw (embedding vector_cosine_ops);
