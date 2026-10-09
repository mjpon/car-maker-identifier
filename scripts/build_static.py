"""Turn data/nhtsa_data.csv into site/data/vehicles.json for the static site.

Standard library only. Run from anywhere:

    python3 -I scripts/build_static.py

The "Raw" column (the unparsed PDF row, only useful for debugging the loader) is left out.
Numbers become integers; blank cells stay as empty strings.
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "nhtsa_data.csv"
TARGET = ROOT / "site" / "data" / "vehicles.json"

NUMERIC = {"Year", "% US/Canada", "Primary %", "Secondary %"}
DROP = {"Raw"}


def main() -> int:
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = [name for name in reader.fieldnames if name not in DROP]
        rows = []
        for record in reader:
            row = []
            for name in columns:
                value = record[name].strip()
                row.append(int(float(value)) if name in NUMERIC and value != "" else value)
            rows.append(row)

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    payload = {"columns": columns, "rows": rows}
    TARGET.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(rows):,} vehicles, {len(columns)} columns -> {TARGET.relative_to(ROOT)} ({TARGET.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
