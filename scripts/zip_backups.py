import sys, zipfile, pathlib

def latest_backup_folder():
    backups_root = pathlib.Path("backups")
    folders = [p for p in backups_root.glob("*") if p.is_dir()]
    if not folders:
        return None
    return sorted(folders, reverse=True)[0]

def main():
    if len(sys.argv) == 2:
        folder = pathlib.Path("backups") / sys.argv[1]
    else:
        folder = latest_backup_folder()

    if not folder or not folder.exists():
        print("No backups folder found to zip.")
        raise SystemExit(1)

    out = pathlib.Path("backups") / f"orchid_backup_{folder.name}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in folder.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(folder.parent))
    print("ZIP created:", out)

if __name__ == "__main__":
    main()
