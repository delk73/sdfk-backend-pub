#!/usr/bin/env python3
"""Generate database schema documentation from ORM models."""
from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path
from typing import List

import sqlalchemy as sa
from app.models import Base

# Ensure project root is on PYTHONPATH
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Dynamically import every module under app.models so Base.metadata is filled
for _, modname, _ in pkgutil.iter_modules(["app/models"]):
    importlib.import_module(f"app.models.{modname}")

meta = Base.metadata  # already populated

# Collect tables sorted by name
tables: dict[str, sa.Table] = {t.name: t for t in meta.sorted_tables}

# Build Mermaid ER diagram lines
lines: List[str] = ["erDiagram"]
for tbl in tables.values():
    for fk in tbl.foreign_keys:
        src = tbl.name
        dst = fk.column.table.name
        lines.append(f"    {src} }}o--|| {dst} : FK")
# Remove duplicates while preserving order
lines = list(dict.fromkeys(lines))

# Build per-table sections
sections: List[str] = []
for tname, table in tables.items():
    sections.append(f"## {tname}\n")
    if table.comment:
        sections.append(table.comment)
    sections.append("")
    sections.append("| Column | Type | Key | Nullable | Description |")
    sections.append("|--------|------|-----|----------|-------------|")
    for col in table.columns:
        col_type = str(col.type)
        key = "PK" if col.primary_key else ("FK" if col.foreign_keys else "")
        sections.append(
            f"| {col.name} | {col_type} | {key} | {not col.nullable} | {col.comment or ''} |"
        )
    sections.append("")

# Compose final document
doc_lines: List[str] = ["# Synesthetic Database Reference", "", "```mermaid"]
doc_lines += lines
doc_lines.append("```")
doc_lines.append("")
doc_lines += sections

Path("docs").mkdir(exist_ok=True)
Path("docs/db_schema.md").write_text("\n".join(doc_lines))
print("Generated docs/db_schema.md")
