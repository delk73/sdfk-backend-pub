import json
import sys

from app.database import SessionLocal
from app import models


def main(path: str) -> None:
    db = SessionLocal()
    try:
        for bundle in json.load(open(path)):
            db.add(models.RuleBundle(**bundle))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: import_rule_bundles.py <json_file>")
        sys.exit(1)
    main(sys.argv[1])
