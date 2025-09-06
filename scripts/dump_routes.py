from app.main import app

if __name__ == "__main__":
    paths = [r.path for r in app.routes]
    pattern = "/" + "lab"
    lab_paths = [p for p in paths if p.startswith(pattern)]
    print(f"LAB ROUTES ({len(lab_paths)})")
    for p in sorted(paths):
        print(p)
