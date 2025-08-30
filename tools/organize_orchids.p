import csv, hashlib, json, re, shutil, sys, zipfile
from pathlib import Path
from typing import Dict, List

# ---------- CONFIG ----------
UPLOADS_DIR      = Path("uploads")          # where your zips/folders live
IMAGES_OUT_DIR   = Path("assets/images")    # normalized image home
TAXONOMY_CSV     = Path("assets/data/taxonomy.csv")  # your exported Google Sheet tab
GALLERY_JSON     = Path("assets/data/gallery.json")
REPORT_DIR       = Path("tools")
ALLOWED_EXTS     = {".jpg",".jpeg",".png",".webp",".gif"}
RESIZE_MAX_PX    = None  # e.g. 1600 to enable (requires Pillow); None = no resizing
# ----------------------------

def slug(s:str) -> str:
    return re.sub(r"[^a-z0-9]+","-", s.lower()).strip("-")

def norm_genus(genus:str) -> str:
    # Genus capitalized: Cattleya
    s = (genus or "").strip()
    return s[:1].upper() + s[1:].lower() if s else s

def norm_species(species:str) -> str:
    # species lowercase: dowiana
    return (species or "").strip().lower()

def sha1_file(p:Path) -> str:
    h = hashlib.sha1()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def unzip_all():
    for z in UPLOADS_DIR.glob("**/*.zip"):
        print(f"Unzipping: {z}")
        try:
            with zipfile.ZipFile(z) as zf:
                zf.extractall(UPLOADS_DIR)
        except Exception as e:
            print(f"  ! Failed to unzip {z}: {e}")

def index_images() -> List[Path]:
    imgs = []
    for p in UPLOADS_DIR.rglob("*"):
        if p.is_file() and p.suffix.lower() in ALLOWED_EXTS:
            imgs.append(p)
    return imgs

def load_taxonomy() -> List[Dict]:
    rows = []
    with TAXONOMY_CSV.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows

def make_manifest(imgs: List[Path]) -> List[Dict]:
    manifest = []
    seen_hash = {}
    for p in imgs:
        try:
            h = sha1_file(p)
        except Exception as e:
            print(f"  ! Hash fail {p}: {e}")
            continue
        manifest.append({
            "path": str(p.as_posix()),
            "name": p.name,
            "ext": p.suffix.lower(),
            "bytes": p.stat().st_size,
            "hash": h,
        })
    return manifest

def write_csv(path:Path, rows:List[Dict], header=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = []
    if header is None and rows:
        header = list(rows[0].keys())
    elif header is None:
        header = []
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        if header:
            w.writeheader()
        for r in rows:
            w.writerow(r)

def group_duplicates(manifest:List[Dict]) -> Dict[str, List[Dict]]:
    groups = {}
    for m in manifest:
        groups.setdefault(m["hash"], []).append(m)
    return {h:rows for h,rows in groups.items() if len(rows) > 1}

def ensure_pillow():
    global Image
    try:
        from PIL import Image
        return Image
    except Exception:
        print("Pillow not installed; skipping resize. To enable: pip install pillow")
        return None

def maybe_resize(src:Path, dst:Path):
    if not RESIZE_MAX_PX:
        shutil.copy2(src, dst)
        return
    Image = ensure_pillow()
    if Image is None:
        shutil.copy2(src, dst)
        return
    try:
        with Image.open(src) as im:
            im = im.convert("RGB")
            w,h = im.size
            scale = max(w,h) / float(RESIZE_MAX_PX)
            if scale > 1.0:
                nw, nh = int(w/scale), int(h/scale)
                im = im.resize((nw,nh))
            dst.parent.mkdir(parents=True, exist_ok=True)
            im.save(dst, "JPEG", quality=85, optimize=True)
    except Exception as e:
        print(f"  ! Resize fail {src}: {e}")
        shutil.copy2(src, dst)

def build_lookup_by_filename(manifest:List[Dict]) -> Dict[str, Dict]:
    look = {}
    for m in manifest:
        look.setdefault(m["name"].lower(), m)
    return look

def guess_filename_for_taxon(genus:str, species:str, manifest_names:set) -> str:
    base = f"{slug(genus)}-{slug(species)}"
    # try prefix match
    for name in manifest_names:
        if name.startswith(base):
            return name
    # try contains species only (fallback)
    for name in manifest_names:
        if slug(species) in name:
            return name
    return ""

def main():
    print("== Orchid Rescue Kit ==")
    print("1) Unzipping any archives in /uploads …")
    unzip_all()

    print("2) Indexing images under /uploads …")
    imgs = index_images()
    print(f"   Found {len(imgs)} images.")

    print("3) Building manifest …")
    manifest = make_manifest(imgs)
    write_csv(REPORT_DIR / "report_manifest.csv", manifest,
              header=["path","name","ext","bytes","hash"])

    print("4) Detecting duplicates …")
    dups = group_duplicates(manifest)
    dup_rows = []
    for h, rows in dups.items():
        for r in rows:
            dup_rows.append({"hash": h, **r})
    write_csv(REPORT_DIR / "report_duplicates.csv", dup_rows,
              header=["hash","path","name","ext","bytes"])
    print(f"   Duplicate groups: {len(dups)} (see tools/report_duplicates.csv)")

    print("5) Loading taxonomy CSV …")
    taxa = load_taxonomy()
    print(f"   Taxa rows: {len(taxa)}")

    # map filename -> manifest entry
    by_name = build_lookup_by_filename(manifest)
    manifest_names = set(by_name.keys())

    gallery = []
    unmatched_taxa = []
    unlinked_images = set(manifest_names)

    for t in taxa:
        g = norm_genus(t.get("genus",""))
        s = norm_species(t.get("species",""))
        if not g or not s:
            continue

        # If CSV already has image_url pointing to something local-like, try to use filename
        csv_url = (t.get("image_url") or "").strip()
        chosen = None
        if csv_url:
            # pull just the last segment as candidate filename
            tail = csv_url.split("/")[-1].lower()
            if tail in by_name:
                chosen = by_name[tail]
        if not chosen:
            # guess by genus-species slug prefix
            guess = guess_filename_for_taxon(g, s, manifest_names)
            if guess:
                chosen = by_name[guess]

        if chosen:
            unlinked_images.discard(chosen["name"].lower())
            # normalized destination
            genus_dir = IMAGES_OUT_DIR / g
            safe_base = f"{g}_{s}__{chosen['name']}".replace(" ", "_")
            dest = genus_dir / safe_base
            dest = dest.with_suffix(".jpg") if dest.suffix.lower() not in {".jpg",".jpeg"} else dest

            # write/resize/copy
            maybe_resize(Path(chosen["path"]), dest)

            web_path = "/" + dest.as_posix()
            entry = {
                "genus": g,
                "species": s,
                "image": web_path,
            }
            # Pass through selected metadata if present
            for k in ["bloom_months","country","photographer","grower","notes"]:
                if t.get(k):
                    entry[k] = t[k]
            gallery.append(entry)
        else:
            unmatched_taxa.append({
                "genus": g, "species": s, "note": "no image matched"
            })

    print("6) Writing gallery.json …")
    GALLERY_JSON.parent.mkdir(parents=True, exist_ok=True)
    with GALLERY_JSON.open("w", encoding="utf-8") as f:
        json.dump(gallery, f, ensure_ascii=False, indent=2)
    print(f"   Wrote {len(gallery)} records → {GALLERY_JSON}")

    print("7) Writing mismatch reports …")
    write_csv(REPORT_DIR / "report_unmatched.csv", unmatched_taxa,
              header=["genus","species","note"])

    # any images that never got linked
    unlinked_rows = [{"name": n, "path": by_name[n]["path"]} for n in sorted(unlinked_images)]
    write_csv(REPORT_DIR / "report_unlinked.csv", unlinked_rows, header=["name","path"])
    print("   See tools/report_unmatched.csv and tools/report_unlinked.csv")

    print("\n✅ Done.\n- Images normalized to assets/images/\n- Data written to assets/data/gallery.json\n- Reports in tools/")

if __name__ == "__main__":
    main()
