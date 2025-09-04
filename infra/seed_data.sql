-- Seed data for Orchid Continuum v2.0
-- Sample data for development and testing

-- Insert sample users
INSERT INTO users (id, email, role, display_name, hashed_password) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'admin@fcos.org', 'admin', 'System Administrator', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewuY7On1/R5T3NK2'),
('550e8400-e29b-41d4-a716-446655440002', 'editor@fcos.org', 'editor', 'Collection Editor', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewuY7On1/R5T3NK2'),
('550e8400-e29b-41d4-a716-446655440003', 'member@fcos.org', 'member', 'FCOS Member', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewuY7On1/R5T3NK2');

-- Insert sample data sources
INSERT INTO sources (id, name, type, status) VALUES
('550e8400-e29b-41d4-a716-446655440010', 'GBIF Global Database', 'gbif', 'active'),
('550e8400-e29b-41d4-a716-446655440011', 'FCOS Google Drive', 'google_drive', 'active'),
('550e8400-e29b-41d4-a716-446655440012', 'User Uploads', 'user', 'active');

-- Insert sample orchids
INSERT INTO orchids (id, scientific_name, genus, species, hybrid_status, description, growth_habit, notes) VALUES
('550e8400-e29b-41d4-a716-446655440020', 'Paphiopedilum micranthum', 'Paphiopedilum', 'micranthum', false, 'Small-flowered slipper orchid endemic to Southeast Asia', 'terrestrial', 'Critically endangered species requiring cool, humid conditions'),
('550e8400-e29b-41d4-a716-446655440021', 'Cattleya labiata', 'Cattleya', 'labiata', false, 'Large-lipped Cattleya, the type species of the genus', 'epiphytic', 'Classic corsage orchid with fragrant purple flowers'),
('550e8400-e29b-41d4-a716-446655440022', 'Phalaenopsis amabilis', 'Phalaenopsis', 'amabilis', false, 'Lovely moth orchid with pure white flowers', 'epiphytic', 'Popular houseplant, easy to grow');

-- Insert sample photos
INSERT INTO photos (id, orchid_id, source, source_ref, url, credited_to, license, is_verified) VALUES
('550e8400-e29b-41d4-a716-446655440030', '550e8400-e29b-41d4-a716-446655440020', 'gbif', 'gbif_12345', 'https://example.com/paph_micro.jpg', 'Botanical Survey', 'CC BY-SA 4.0', true),
('550e8400-e29b-41d4-a716-446655440031', '550e8400-e29b-41d4-a716-446655440021', 'google_drive', '1BKz8H8n9pQ3jZ8QeH8N9pQ3jZ8QeH8N9', 'https://drive.google.com/uc?id=1BKz8H8n9pQ3jZ8QeH8N9pQ3jZ8QeH8N9', 'FCOS Member', 'CC BY 4.0', true),
('550e8400-e29b-41d4-a716-446655440032', '550e8400-e29b-41d4-a716-446655440022', 'user', 'user_upload_001', 'https://example.com/phal_amabilis.jpg', 'John Orchid Grower', 'CC BY 4.0', false);

-- Insert sample culture sheets (Baker and AOS data)
INSERT INTO culture_sheets (id, orchid_id, source, light_low, light_high, temp_min, temp_max, humidity_min, humidity_max, water_notes, seasonal_notes, citations) VALUES
('550e8400-e29b-41d4-a716-446655440040', '550e8400-e29b-41d4-a716-446655440020', 'baker', 800, 1200, 15.0, 22.0, 70.0, 85.0, 'Keep evenly moist, never allow to dry completely', 'Reduce watering slightly in winter', '{"source": "Baker Culture Sheet", "year": 1995}'),
('550e8400-e29b-41d4-a716-446655440041', '550e8400-e29b-41d4-a716-446655440021', 'baker', 2000, 3000, 18.0, 28.0, 50.0, 70.0, 'Water thoroughly then allow to dry between waterings', 'Bright light year round, reduce water in winter', '{"source": "Baker Culture Sheet", "year": 1995}'),
('550e8400-e29b-41d4-a716-446655440042', '550e8400-e29b-41d4-a716-446655440022', 'aos', 1200, 2000, 20.0, 30.0, 60.0, 80.0, 'Water when media approaches dryness', 'Consistent conditions year round', '{"source": "AOS Culture Sheet", "year": 2020}');

-- Insert sample traits
INSERT INTO traits (id, orchid_id, phenotypic) VALUES
('550e8400-e29b-41d4-a716-446655440050', '550e8400-e29b-41d4-a716-446655440020', '{"flower_color": ["pink", "white"], "flower_size": "small", "fragrance": false, "blooming_season": "spring"}'),
('550e8400-e29b-41d4-a716-446655440051', '550e8400-e29b-41d4-a716-446655440021', '{"flower_color": ["purple", "magenta"], "flower_size": "large", "fragrance": true, "blooming_season": "fall"}'),
('550e8400-e29b-41d4-a716-446655440052', '550e8400-e29b-41d4-a716-446655440022', '{"flower_color": ["white"], "flower_size": "medium", "fragrance": false, "blooming_season": "year_round"}');

-- Insert sample occurrences (GBIF-style data)
INSERT INTO occurrences (id, orchid_id, gbif_occurrence_id, lat, lon, country, date_observed, raw) VALUES
('550e8400-e29b-41d4-a716-446655440060', '550e8400-e29b-41d4-a716-446655440020', 'GBIF_001', 16.0471, 108.2068, 'Vietnam', '2023-03-15', '{"collector": "Field Survey Team", "elevation": 1200}'),
('550e8400-e29b-41d4-a716-446655440061', '550e8400-e29b-41d4-a716-446655440021', 'GBIF_002', -15.7797, -47.9297, 'Brazil', '2023-05-20', '{"collector": "Botanical Garden", "elevation": 800}'),
('550e8400-e29b-41d4-a716-446655440062', '550e8400-e29b-41d4-a716-446655440022', 'GBIF_003', 3.1390, 101.6869, 'Malaysia', '2023-07-10', '{"collector": "University Research", "elevation": 200}');

-- Insert sample citations
INSERT INTO citations (id, orchid_id, doi, title, source, year, notes) VALUES
('550e8400-e29b-41d4-a716-446655440070', '550e8400-e29b-41d4-a716-446655440020', '10.1234/example.2023.001', 'Conservation Status of Paphiopedilum micranthum', 'Journal of Orchid Conservation', 2023, 'Comprehensive IUCN assessment'),
('550e8400-e29b-41d4-a716-446655440071', '550e8400-e29b-41d4-a716-446655440021', '10.1234/example.2022.045', 'Historical Cultivation of Cattleya labiata', 'Orchid Review', 2022, 'Historical cultivation practices'),
('550e8400-e29b-41d4-a716-446655440072', '550e8400-e29b-41d4-a716-446655440022', '10.1234/example.2023.089', 'Phalaenopsis Species Distribution in Southeast Asia', 'Botanical Journal', 2023, 'Geographic distribution study');

-- Insert sample collections
INSERT INTO collections (id, user_id, name, notes, is_public) VALUES
('550e8400-e29b-41d4-a716-446655440080', '550e8400-e29b-41d4-a716-446655440003', 'My Orchid Collection', 'Personal greenhouse collection', true),
('550e8400-e29b-41d4-a716-446655440081', '550e8400-e29b-41d4-a716-446655440002', 'FCOS Reference Collection', 'Society reference specimens', true);

-- Insert sample collection items
INSERT INTO collection_items (id, collection_id, orchid_id, nick_name, acquired_at, status, care_prefs) VALUES
('550e8400-e29b-41d4-a716-446655440090', '550e8400-e29b-41d4-a716-446655440080', '550e8400-e29b-41d4-a716-446655440021', 'Purple Beauty', '2023-01-15', 'blooming', '{"location": "east_window", "watering": "weekly"}'),
('550e8400-e29b-41d4-a716-446655440091', '550e8400-e29b-41d4-a716-446655440080', '550e8400-e29b-41d4-a716-446655440022', 'White Wonder', '2023-03-20', 'active', '{"location": "grow_tent", "watering": "bi_weekly"}');

-- Insert sample audit log entries
INSERT INTO audit_log (id, user_id, action, entity, entity_id, diff) VALUES
('550e8400-e29b-41d4-a716-446655440100', '550e8400-e29b-41d4-a716-446655440002', 'CREATE', 'orchids', '550e8400-e29b-41d4-a716-446655440020', '{"action": "created_orchid", "scientific_name": "Paphiopedilum micranthum"}'),
('550e8400-e29b-41d4-a716-446655440101', '550e8400-e29b-41d4-a716-446655440002', 'UPDATE', 'photos', '550e8400-e29b-41d4-a716-446655440030', '{"action": "verified_photo", "is_verified": true}'),
('550e8400-e29b-41d4-a716-446655440102', '550e8400-e29b-41d4-a716-446655440003', 'CREATE', 'collections', '550e8400-e29b-41d4-a716-446655440080', '{"action": "created_collection", "name": "My Orchid Collection"}');