INSERT INTO Users (email, password, role, phone)
VALUES
('tenant1@example.com', 'hashed_password', 'Tenant', '+251912345678'),
('owner1@example.com', 'hashed_password', 'Owner', '+251912345679');

INSERT INTO Properties (user_id, title, description, location, price, house_type, amenities, bedrooms, status, lat, lon, search_vector)
VALUES
(2, 'Apartment in Bole', 'Modern 2-bedroom apartment', 'Bole, Addis Ababa', 1500.00, 'apartment', '{"wifi", "parking"}', 2, 'APPROVED', 9.0, 38.7, to_tsvector('english', 'Apartment in Bole Modern 2-bedroom apartment')),
(2, 'House in Adama', 'Spacious family house', 'Adama', 2000.00, 'house', '{"wifi", "water"}', 3, 'APPROVED', 8.54, 39.27, to_tsvector('english', 'House in Adama Spacious family house')),
(2, 'Condo in Piazza', 'Luxury condo near city center', 'Piazza, Addis Ababa', 1800.00, 'condo', '{"wifi", "parking", "security"}', 2, 'APPROVED', 9.03, 38.75, to_tsvector('english', 'Condo in Piazza Luxury condo near city center'));

INSERT INTO TenantProfiles (user_id, job_school_location, salary, house_type, family_size, preferred_amenities)
VALUES
(1, 'Bole, Addis Ababa', 5000.00, 'apartment', 2, '{"wifi", "parking"}'),
(1, 'Piazza, Addis Ababa', 6000.00, 'condo', 3, '{"wifi", "security"}');
