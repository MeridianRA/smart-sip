import csv
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

INPUT_FILE = BASE_DIR / "data" / "nse" / "historical" / "ratio" / "csv" / "NIFTY_50.csv"
OUTPUT_DIR = BASE_DIR / "data" / "nse" / "historical" / "ratio" / "csv_transformed"

INDEX_NAME = "NIFTY 50"

DATE_COLUMN = "DATE"
COLUMN_MAP = {
    DATE_COLUMN: "date",
    "pe": "pe",
    "pb": "pb",
    "divYield": "div_yield",
}

def transform_file(csv_file):
    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not set(COLUMN_MAP).issubset(reader.fieldnames):
            raise ValueError()
        rows = []
        for row in reader:
            new_row = {new: row[old] for old, new in COLUMN_MAP.items()}
            new_row["date"] = (
                datetime.strptime(row[DATE_COLUMN], "%d %b %Y").date().isoformat()
            )
            rows.append(new_row)

    if not rows:
        raise ValueError()

    rows.sort(key=lambda r: r["date"])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / csv_file.name
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(COLUMN_MAP.values()))
        writer.writeheader()
        writer.writerows(rows)

    return output_file

def main():
    try:
        output_file = transform_file(INPUT_FILE)
        print(
            f"{INDEX_NAME} ratio data transformed and stored successfully "
            f"at {output_file.relative_to(BASE_DIR)}"
        )
    except Exception as e:
        print(f"ERROR : {e}")

if __name__ == "__main__":
    main()
