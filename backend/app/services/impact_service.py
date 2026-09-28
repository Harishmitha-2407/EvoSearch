"""
When a function/class changes, finds other code files in the same project
(same `group`) whose raw text references its name. This is a conservative
textual-reference search (word-boundary match), NOT true call-graph
analysis - results are always labeled "potential impact", never guaranteed,
per spec section 21.
"""
import re
from sqlalchemy.orm import Session
from app import models


def find_potential_impact(db: Session, group: str, entity_name: str, exclude_file_id: str | None = None):
    pattern = re.compile(r"\b" + re.escape(entity_name) + r"\b")
    files = db.query(models.CodeFile).filter(models.CodeFile.group == group).all()

    referencing = []
    for f in files:
        if exclude_file_id and f.id == exclude_file_id:
            continue
        if not f.raw_text:
            continue
        matches = list(pattern.finditer(f.raw_text))
        if not matches:
            continue
        lines = [f.raw_text.count("\n", 0, m.start()) + 1 for m in matches]
        referencing.append({
            "file_id": f.id,
            "filename": f.filename,
            "reference_count": len(matches),
            "lines": lines[:10],
        })

    note = (
        f"Found {len(referencing)} file(s) in this project referencing '{entity_name}' by name. "
        "This indicates potential impact based on textual references, not a guarantee - "
        "always verify with the actual call graph before relying on this for a change."
        if referencing else
        f"No other files in this project reference '{entity_name}' by name."
    )
    return referencing, note
