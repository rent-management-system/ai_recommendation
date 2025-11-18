-- Clear existing data from tables managed by this service
DELETE FROM public."RecommendationLogs";
DELETE FROM public."TenantPreferences";

-- Inserting users with specific UUIDs and full names from the user's database
INSERT INTO public.users (id, email, password, full_name, role, phone_number)
VALUES
('007a9359-e9ed-475f-ac13-401ca149b67d', 'test@test.com', '$2b$12$OFCp0Z83s2Gfxh306KAMQ.9MCfPrNPZ.WEaXrcAYKYxsOkjh1JZCC', 'Test User', 'TENANT', '+251911234567'),
('05a027b2-0aa4-4555-ba89-d9b7b9a1434b', 'testo@gmail.com', '$2b$12$3g6co1CF8IZFvW9Ly18fTek3VuXx1Z4oUT8ujhB.N8FB7zwbBXnui', 'TEST OWNER', 'OWNER', '\+251922345678')
ON CONFLICT (id) DO NOTHING; -- Add ON CONFLICT clause

-- Inserting properties owned by the owner user
INSERT INTO public.properties (user_id, title, description, location, price, house_type, amenities, status, lat, lon, payment_status)
VALUES
('05a027b2-0aa4-4555-ba89-d9b7b9a1434b', 'Apartment in Bole', 'Modern 2-bedroom apartment', 'Bole, Addis Ababa', 1500.00, 'apartment', '["wifi", "parking"]', 'APPROVED', 9.0, 38.7, 'PAID'),
('05a027b2-0aa4-4555-ba89-d9b7b9a1434b', 'House in Adama', 'Spacious family house', 'Adama', 2000.00, 'house', '["wifi", "water"]', 'APPROVED', 8.54, 39.27, 'PAID'),
('05a027b2-0aa4-4555-ba89-d9b7b9a1434b', 'Condo in Piazza', 'Luxury condo near city center', 'Piazza, Addis Ababa', 1800.00, 'condo', '["wifi", "parking", "security"]', 'APPROVED', 9.03, 38.75, 'PAID')
ON CONFLICT (id) DO NOTHING; -- Add ON CONFLICT clause

-- Inserting a tenant preference for the tenant user
INSERT INTO public."TenantPreferences" (user_id, job_school_location, salary, house_type, family_size, preferred_amenities)
VALUES
('007a9359-e9ed-475f-ac13-401ca149b67d', 'Bole, Addis Ababa', 5000.00, 'apartment', 2, '{"wifi", "parking"}');

