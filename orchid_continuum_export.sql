PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE orchid_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scientific_name TEXT,
            genus TEXT,
            species TEXT,
            display_name TEXT,
            common_name TEXT,
            google_drive_id TEXT,
            image_url TEXT,
            validation_status TEXT DEFAULT 'approved',
            is_featured BOOLEAN DEFAULT 0,
            photographer TEXT,
            ai_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
INSERT INTO orchid_record VALUES(1,'Cattleya trianae','Cattleya','trianae','Cattleya trianae','Christmas Orchid','185MlwyxBU8Dy6bqGdwXXPeBXTlhg5M0I','/static/orchid_photos/Cattleya trianae.jpg','approved',1,'FCOS Collection','Beautiful Christmas orchid in full bloom','2025-08-27 03:47:16','2025-08-27 03:47:16');
INSERT INTO orchid_record VALUES(2,'Phalaenopsis amabilis','Phalaenopsis','amabilis','Phalaenopsis amabilis','Moon Orchid','1BKz8H8n9pQ3jZ8QeH8N9pQ3jZ8QeH8N9','/static/orchid_photos/Phalaenopsis amabilis.jpg','approved',1,'FCOS Collection','Elegant white moon orchid','2025-08-27 03:47:16','2025-08-27 03:47:16');
INSERT INTO orchid_record VALUES(3,'Dendrobium nobile','Dendrobium','nobile','Dendrobium nobile','Noble Dendrobium','1CXz9I9o0sR4kA9RfI9O0sR4kA9RfI9O0','/static/orchid_photos/Dendrobium nobile.jpg','approved',0,'FCOS Collection','Classic dendrobium with purple flowers','2025-08-27 03:47:16','2025-08-27 03:47:16');
INSERT INTO orchid_record VALUES(4,'Vanda coerulea','Vanda','coerulea','Vanda coerulea','Blue Vanda','1DYa0J0p1tS5lB0SgJ0P1tS5lB0SgJ0P1','/static/orchid_photos/Vanda coerulea.jpg','approved',0,'FCOS Collection','Stunning blue vanda orchid','2025-08-27 03:47:16','2025-08-27 03:47:16');
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('orchid_record',4);
COMMIT;
