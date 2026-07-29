-- 011_storage_setup.sql
-- Setup Supabase Storage buckets and policies

-- Create buckets if they do not exist
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES 
  ('avatars', 'avatars', true, 5242880, ARRAY['image/jpeg', 'image/png', 'image/gif', 'image/webp']),
  ('documents', 'documents', false, 52428800, ARRAY['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']),
  ('lecture-notes', 'lecture-notes', false, 52428800, ARRAY['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']),
  ('assignments', 'assignments', false, 52428800, ARRAY['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']),
  ('homework', 'homework', false, 52428800, ARRAY['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'image/jpeg', 'image/png']),
  ('videos', 'videos', false, 524288000, ARRAY['video/mp4', 'video/mpeg', 'video/webm']),
  ('certificates', 'certificates', false, 10485760, ARRAY['application/pdf', 'image/jpeg', 'image/png']),
  ('reports', 'reports', false, 20971520, ARRAY['application/pdf', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'])
ON CONFLICT (id) DO NOTHING;

-- Enable RLS on storage.objects


-- 1. Avatars Bucket Policies
CREATE POLICY "Public Read Avatars" ON storage.objects
    FOR SELECT TO public USING (bucket_id = 'avatars');

CREATE POLICY "Authenticated Upload Avatars" ON storage.objects
    FOR INSERT TO authenticated WITH CHECK (bucket_id = 'avatars' AND (auth.uid() = owner OR owner IS NULL));

CREATE POLICY "Owner Update/Delete Avatars" ON storage.objects
    FOR ALL TO authenticated USING (bucket_id = 'avatars' AND auth.uid() = owner);

-- 2. Documents Bucket Policies
CREATE POLICY "School Members Read Documents" ON storage.objects
    FOR SELECT TO authenticated USING (
        bucket_id = 'documents' AND (
            EXISTS (
                SELECT 1 FROM public.profiles p
                JOIN public.user_roles ur ON p.id = ur.profile_id
                WHERE p.id = auth.uid() AND (ur.role_id = (SELECT id FROM public.roles WHERE name = 'super_admin') OR ur.school_id IS NOT NULL)
            )
        )
    );

CREATE POLICY "Staff Upload Documents" ON storage.objects
    FOR INSERT TO authenticated WITH CHECK (
        bucket_id = 'documents' AND (
            EXISTS (
                SELECT 1 FROM public.user_roles ur
                WHERE ur.profile_id = auth.uid() AND ur.role_id IN (
                    SELECT id FROM public.roles WHERE name IN ('super_admin', 'school_admin', 'teacher')
                )
            )
        )
    );

-- 3. Lecture Notes Bucket Policies
CREATE POLICY "School Members Read Lecture Notes" ON storage.objects
    FOR SELECT TO authenticated USING (bucket_id = 'lecture-notes');

CREATE POLICY "Teachers Upload Lecture Notes" ON storage.objects
    FOR INSERT TO authenticated WITH CHECK (
        bucket_id = 'lecture-notes' AND (
            EXISTS (
                SELECT 1 FROM public.user_roles ur
                WHERE ur.profile_id = auth.uid() AND ur.role_id IN (
                    SELECT id FROM public.roles WHERE name IN ('super_admin', 'school_admin', 'teacher')
                )
            )
        )
    );

-- 4. Assignments & Homework Bucket Policies
CREATE POLICY "Read Assignments/Homework" ON storage.objects
    FOR SELECT TO authenticated USING (bucket_id IN ('assignments', 'homework'));

CREATE POLICY "Teachers Upload Assignments" ON storage.objects
    FOR INSERT TO authenticated WITH CHECK (
        bucket_id = 'assignments' AND (
            EXISTS (
                SELECT 1 FROM public.user_roles ur
                WHERE ur.profile_id = auth.uid() AND ur.role_id IN (
                    SELECT id FROM public.roles WHERE name IN ('super_admin', 'school_admin', 'teacher')
                )
            )
        )
    );

CREATE POLICY "Students Upload Homework" ON storage.objects
    FOR INSERT TO authenticated WITH CHECK (
        bucket_id = 'homework' AND (
            EXISTS (
                SELECT 1 FROM public.user_roles ur
                WHERE ur.profile_id = auth.uid() AND ur.role_id IN (
                    SELECT id FROM public.roles WHERE name IN ('student')
                )
            )
        )
    );
