PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE species (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scientific_name TEXT UNIQUE NOT NULL,
  rhs_accepted_name TEXT,
  genus TEXT,
  epithet TEXT,
  functional_group TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
INSERT INTO species VALUES(1,'Phalaenopsis equestris','Phalaenopsis equestris','Phalaenopsis','equestris','CAM_epiphyte','2025-09-09 23:23:13','2025-09-09 23:23:13');
INSERT INTO species VALUES(2,'Cattleya labiata','Cattleya labiata','Cattleya','labiata','CAM_epiphyte','2025-09-09 23:23:13','2025-09-09 23:23:13');
INSERT INTO species VALUES(3,'Angraecum sesquipedale','Angraecum sesquipedale','Angraecum','sesquipedale','C3_epiphyte','2025-09-09 23:23:13','2025-09-09 23:23:13');
CREATE TABLE physiology_measurements (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  species_id INTEGER,
  method TEXT,
  date_range TEXT,
  fv_fm REAL,
  phi_psii REAL,
  etr_max REAL,
  a_max REAL,
  gs REAL,
  sla REAL,
  chlorophyll_a_b REAL,
  stomatal_density REAL,
  provenance TEXT,
  license TEXT,
  uncertainty TEXT,
  last_updated TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(species_id) REFERENCES species(id) ON DELETE CASCADE
);
CREATE TABLE light_env_profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  species_id INTEGER,
  location TEXT,
  ppfd_mean REAL,
  ppfd_max REAL,
  spectrum TEXT,
  canopy_openness REAL,
  photoperiod_hours REAL,
  provenance TEXT,
  license TEXT,
  uncertainty TEXT,
  last_updated TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(species_id) REFERENCES species(id) ON DELETE CASCADE
);
CREATE TABLE cam_cycles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  species_id INTEGER,
  titratable_acidity_day REAL,
  titratable_acidity_night REAL,
  delta_hplus REAL,
  noct_temp_c REAL,
  noct_rh REAL,
  cam_phase_notes TEXT,
  provenance TEXT,
  license TEXT,
  uncertainty TEXT,
  last_updated TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(species_id) REFERENCES species(id) ON DELETE CASCADE
);
CREATE TABLE mycorrhiza_links (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  species_id INTEGER,
  fungus_taxon TEXT,
  substrate TEXT,
  ph REAL,
  ec REAL,
  success_probability REAL,
  provenance TEXT,
  license TEXT,
  uncertainty TEXT,
  last_updated TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(species_id) REFERENCES species(id) ON DELETE CASCADE
);
CREATE TABLE pollination_traits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  species_id INTEGER,
  spur_len_mm REAL,
  color_lab TEXT,
  volatile_ids TEXT,
  known_pollinators TEXT,
  provenance TEXT,
  license TEXT,
  uncertainty TEXT,
  last_updated TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(species_id) REFERENCES species(id) ON DELETE CASCADE
);
CREATE TABLE quantum_params (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  species_id INTEGER,
  k_coh REAL,
  tau_tun_ps REAL,
  evidence_level TEXT,
  source_ref TEXT,
  provenance TEXT,
  license TEXT,
  uncertainty TEXT,
  last_updated TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(species_id) REFERENCES species(id) ON DELETE CASCADE
);
INSERT INTO quantum_params VALUES(1,1,0.119999999999999995,2.0,'low',NULL,'seed','unknown','wide','2025-09-09 23:23:13');
INSERT INTO quantum_params VALUES(2,2,0.119999999999999995,2.0,'low',NULL,'seed','unknown','wide','2025-09-09 23:23:13');
INSERT INTO quantum_params VALUES(3,3,0.0800000000000000016,2.0,'low',NULL,'seed','unknown','wide','2025-09-09 23:23:13');
CREATE TABLE media_assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  species_id INTEGER,
  storage_url TEXT NOT NULL,
  filename TEXT,
  exif TEXT,
  uploaded_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(species_id) REFERENCES species(id) ON DELETE SET NULL
);
CREATE TABLE media_ai_annotations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  media_id INTEGER,
  model_name TEXT,
  version TEXT,
  annotations TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  visibility TEXT CHECK (visibility IN ('public','private')) DEFAULT 'private',
  FOREIGN KEY(media_id) REFERENCES media_assets(id) ON DELETE CASCADE
);
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('species',3);
INSERT INTO sqlite_sequence VALUES('quantum_params',3);
COMMIT;
