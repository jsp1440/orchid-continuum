# main.py
# Single-file Orchid Continuum starter with:
# - SQLite DB created at startup (migration in Python)
# - FastAPI endpoints: /simulate/care, /simulate/cam, /status/roadmap, /literature/search, /media/analyze
# - Serves the Quantum Toggle widget at /public/quantum-toggle-widget.js

import math, sqlite3, os
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Response
from pydantic import BaseModel, Field
from starlette.responses import PlainTextResponse, JSONResponse
from starlette.middleware.cors import CORSMiddleware

DB_PATH = os.getenv("OC_DB_PATH", "orchid.db")

app = FastAPI(title="Orchid Continuum (Single-file Demo)", version="0.1.0")

# CORS so the widget can call from Neon One if needed (you can restrict origins later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# ------------------------- DB bootstrap (SQLite) -------------------------

MIGRATION_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS species (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scientific_name TEXT UNIQUE NOT NULL,
  rhs_accepted_name TEXT,
  genus TEXT,
  epithet TEXT,
  functional_group TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS physiology_measurements (
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

CREATE TABLE IF NOT EXISTS light_env_profiles (
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

CREATE TABLE IF NOT EXISTS cam_cycles (
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

CREATE TABLE IF NOT EXISTS mycorrhiza_links (
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

CREATE TABLE IF NOT EXISTS pollination_traits (
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

CREATE TABLE IF NOT EXISTS quantum_params (
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

CREATE TABLE IF NOT EXISTS media_assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  species_id INTEGER,
  storage_url TEXT NOT NULL,
  filename TEXT,
  exif TEXT,
  uploaded_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(species_id) REFERENCES species(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS media_ai_annotations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  media_id INTEGER,
  model_name TEXT,
  version TEXT,
  annotations TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  visibility TEXT CHECK (visibility IN ('public','private')) DEFAULT 'private',
  FOREIGN KEY(media_id) REFERENCES media_assets(id) ON DELETE CASCADE
);
"""

SEED_SPECIES = [
    ("Phalaenopsis equestris", "Phalaenopsis", "equestris", "CAM_epiphyte"),
    ("Cattleya labiata", "Cattleya", "labiata", "CAM_epiphyte"),
    ("Angraecum sesquipedale", "Angraecum", "sesquipedale", "C3_epiphyte"),
]

def db():
    return sqlite3.connect(DB_PATH)

def migrate_and_seed():
    con = db()
    con.executescript(MIGRATION_SQL)
    cur = con.cursor()
    for sci, genus, epithet, fg in SEED_SPECIES:
        cur.execute("""
            INSERT OR IGNORE INTO species (scientific_name, rhs_accepted_name, genus, epithet, functional_group)
            VALUES (?,?,?,?,?)
        """, (sci, sci, genus, epithet, fg))
    # default quantum params
    cur.execute("SELECT id, functional_group FROM species")
    for sid, fg in cur.fetchall():
        k = 0.12 if (fg or "").startswith("CAM") else 0.08
        cur.execute("""
            INSERT OR IGNORE INTO quantum_params (species_id, k_coh, tau_tun_ps, evidence_level, provenance, license, uncertainty)
            VALUES (?,?,?,?,?,?,?)
        """, (sid, k, 2.0, "low", "seed", "unknown", "wide"))
    con.commit()
    con.close()

migrate_and_seed()

# ------------------------- Models -------------------------

class CarePayload(BaseModel):
    species_id: Optional[int] = Field(None)
    scientific_name: Optional[str] = None
    temp_c: float
    rh: float
    ppfd: Optional[float] = None
    lux: Optional[float] = None
    light_type: Optional[str] = "white_led"
    quantum: bool = False

class CareResult(BaseModel):
    vpd_kpa: float
    target_ppfd: float
    target_rh: List[float]
    watering_days: List[int]
    notes: str
    uncertainty: str

class CamPayload(BaseModel):
    species_id: Optional[int] = None
    scientific_name: Optional[str] = None
    noct_temp_c: float
    noct_rh: float
    photoperiod_hours: float
    quantum: bool = False

class CamResult(BaseModel):
    expected_ta_swing: List[float]
    phase_schedule: Dict[str, str]
    sensitivity: Dict[str, float]
    uncertainty: str

# ------------------------- Helpers -------------------------

def vpd_kpa(temp_c: float, rh: float) -> float:
    es = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
    ea = es * (rh / 100.0)
    return max(es - ea, 0.0)

def ppfd_from_lux(lux: float, light_type: str="white_led") -> float:
    factor = 0.018 if light_type == "white_led" else 0.015
    return lux * factor

def lookup_quantum_params(species_id: Optional[int], scientific_name: Optional[str]):
    # try exact species by id or name; else functional group heuristic
    con = db(); cur = con.cursor()
    sid = None
    if species_id:
        sid = species_id
    elif scientific_name:
        cur.execute("SELECT id FROM species WHERE scientific_name = ?", (scientific_name,))
        row = cur.fetchone()
        if row: sid = row[0]
    if sid:
        cur.execute("SELECT k_coh, tau_tun_ps FROM quantum_params WHERE species_id = ?", (sid,))
        row = cur.fetchone()
        if row:
            con.close()
            return {"k_coh": row[0] or 0.1, "tau_tun_ps": row[1] or 2.0}
    # fallback
    con.close()
    return {"k_coh": 0.10, "tau_tun_ps": 2.0}

# ------------------------- Endpoints -------------------------

@app.post("/simulate/care", response_model=CareResult)
def simulate_care(payload: CarePayload):
    ppfd = payload.ppfd or (ppfd_from_lux(payload.lux, payload.light_type or "white_led") if payload.lux else 120.0)
    vpd = vpd_kpa(payload.temp_c, payload.rh)

    target_ppfd = min(max(ppfd, 80.0), 250.0)
    target_rh_low, target_rh_high = 55.0, 75.0
    watering_days = [2, 5]
    stress = max(min((vpd - 1.2) / 1.0, 1.0), 0.0)

    if payload.quantum:
        q = lookup_quantum_params(payload.species_id, payload.scientific_name)
        alpha, beta = 0.15, 0.10
        bump = 1.0 + alpha * q["k_coh"]
        penalty = 1.0 - beta * stress
        target_ppfd = target_ppfd * bump * penalty
        target_rh_low = max(50.0, target_rh_low - 3.0)
        target_rh_high = min(80.0, target_rh_high + 3.0)
        watering_days = [3, 6]

    return CareResult(
        vpd_kpa=round(vpd, 3),
        target_ppfd=round(target_ppfd, 1),
        target_rh=[round(target_rh_low), round(target_rh_high)],
        watering_days=watering_days,
        notes="Care targets with optional quantum correction (coherence bump & stress penalty).",
        uncertainty="Demo ranges; calibrate to ΦPSII/Fv/Fm as data accrues."
    )

@app.post("/simulate/cam", response_model=CamResult)
def simulate_cam(payload: CamPayload):
    base_swing = max(10.0 * (payload.noct_rh/70.0) * (22.0 / max(payload.noct_temp_c, 10.0)), 2.0)
    if payload.quantum:
        q = lookup_quantum_params(payload.species_id, payload.scientific_name)
        gamma = 0.12
        base_swing *= (1.0 + gamma * (q["tau_tun_ps"] / 10.0))
    lo = round(base_swing * 0.85, 2)
    hi = round(base_swing * 1.15, 2)
    sensitivity = {"dTA_dRH": round(base_swing * 0.01, 4), "dTA_dT": round(-base_swing * 0.02, 4)}

    return CamResult(
        expected_ta_swing=[lo, hi],
        phase_schedule={
            "Phase I": "Late night CO₂ fixation (PEPc) → malate storage",
            "Phase II": "Dawn transition; mixed PEPc/Rubisco",
            "Phase III": "Daytime decarboxylation; stomata closed",
            "Phase IV": "Dusk transition; stomata reopening"
        },
        sensitivity=sensitivity,
        uncertainty="Demo; refine with species TA logs + nocturnal traces."
    )

ROADMAP = {
    "phase": "Phase 1–2 (Physio+Env & CAM)",
    "updated": datetime.utcnow().isoformat() + "Z",
    "next_actions": [
        "Load physiology_measurements for ≥25 species (ΦPSII, Fv/Fm).",
        "Backfill light_env_profiles (PPFD ranges, photoperiod).",
        "Calibrate CAM with TA logs if available.",
        "Seed quantum_params by functional group with evidence_level.",
        "Embed the widget and collect feedback on quantum vs. classical."
    ],
    "resource_checklist": [
        "At least 10 gallery images to test /media/analyze",
        "Any curated ΦPSII/Fv/Fm dataset",
        "Optional: literature keys (Crossref/EuropePMC)"
    ]
}

@app.get("/status/roadmap")
def status_roadmap():
    return ROADMAP

@app.get("/literature/search")
def literature_search(q: str):
    # stub; wire real APIs later
    return {"results":[{"title":"(stub) Quantum coherence in photosynthesis","doi":"10.xxxx/xxxx","year":2010,"score":0.42}]}

class MediaAnalyzePayload(BaseModel):
    media_id: Optional[int] = None
    image_url: Optional[str] = None
    make_public: bool = True

@app.post("/media/analyze")
def media_analyze(payload: MediaAnalyzePayload):
    annotations = {
        "exif": {"lens_mm": 50, "aperture": 2.8},
        "detected_parts": {"flowers": 3, "buds": 2, "roots_visible": True, "leaf_venation": "parallel"},
        "color_palette_lab": [{"L":70,"a":20,"b":-5}],
        "quality": {"sharpness": 0.82, "exposure_ok": True},
        "phenology": {"in_bud": True, "in_bloom": True}
    }
    vis = "public" if payload.make_public else "private"
    return {"media_id": payload.media_id, "annotations": annotations, "visibility": vis}

# ------------------------- Widget JS (served from the API) -------------------------

WIDGET_JS = r"""
(function(){
  class OrchidQuantumWidget extends HTMLElement {
    constructor(){
      super();
      this.attachShadow({mode:'open'});
      this.apiBase = this.getAttribute('api-base') || '';
      this.scientificName = this.getAttribute('scientific-name') || '';
      this.speciesId = this.getAttribute('species-id') || '';
      this.render();
    }
    render(){
      const s = document.createElement('style');
      s.textContent = `
        .card{font-family:system-ui, Arial; border:1px solid #ddd; border-radius:8px; padding:12px; max-width:420px}
        .row{display:flex; gap:8px; align-items:center; margin:6px 0}
        .switch{position:relative; display:inline-block; width:46px; height:24px}
        .switch input{opacity:0;width:0;height:0}
        .slider{position:absolute; cursor:pointer; inset:0; background:#ccc; transition:.2s; border-radius:24px}
        .slider:before{position:absolute; content:""; height:18px; width:18px; left:3px; top:3px; background:white; transition:.2s; border-radius:50%}
        input:checked + .slider{background:#4caf50}
        input:checked + .slider:before{transform:translateX(22px)}
        button{padding:8px 12px; border:1px solid #444; background:#fff; cursor:pointer; border-radius:6px}
        .out{background:#f9fafb; border-radius:6px; padding:8px; margin-top:8px; font-size:14px}
        label.small{font-size:12px; color:#555}
      `;
      this.shadowRoot.innerHTML = '';
      this.shadowRoot.appendChild(s);
      const card = document.createElement('div'); card.className='card';
      card.innerHTML = `
        <div class="row"><strong>Orchid Care Optimizer</strong></div>
        <div class="row">
          <label class="small">Temp (°C)</label><input id="temp" type="number" value="24" style="width:70px">
          <label class="small">RH (%)</label><input id="rh" type="number" value="60" style="width:70px">
          <label class="small">Lux</label><input id="lux" type="number" value="8000" style="width:90px">
        </div>
        <div class="row">
          <label class="small">Quantum</label>
          <label class="switch">
            <input id="quantum" type="checkbox">
            <span class="slider"></span>
          </label>
          <button id="go">Simulate</button>
        </div>
        <div class="out" id="out">Ready.</div>
      `;
      this.shadowRoot.appendChild(card);
      const $ = id => this.shadowRoot.getElementById(id);
      $('#go').addEventListener('click', async () => {
        const payload = {
          temp_c: parseFloat($('#temp').value),
          rh: parseFloat($('#rh').value),
          lux: parseFloat($('#lux').value),
          quantum: $('#quantum').checked
        };
        if (this.speciesId) payload.species_id = Number(this.speciesId);
        if (this.scientificName) payload.scientific_name = this.scientificName;
        $('#out').textContent = 'Simulating...';
        try{
          const res = await fetch(this.apiBase.replace(/\/$/,'') + '/simulate/care', {
            method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)
          });
          const data = await res.json();
          $('#out').innerHTML =
            `VPD: <b>${data.vpd_kpa} kPa</b><br>` +
            `Target PPFD: <b>${data.target_ppfd}</b><br>`+
            `Target RH: <b>${data.target_rh[0]}–${data.target_rh[1]}%</b><br>`+
            `Watering: days <b>${data.watering_days.join(', ')}</b><br>`+
            `<i>${data.notes}</i>`;
        } catch(e){
          $('#out').textContent = 'Error: ' + (e.message || e);
        }
      });
    }
  }
  customElements.define('orchid-quantum-widget', OrchidQuantumWidget);
})();
"""

@app.get("/public/quantum-toggle-widget.js")
def serve_widget():
    return PlainTextResponse(WIDGET_JS, media_type="application/javascript")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)