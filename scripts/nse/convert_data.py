import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

INPUT_FILE = BASE_DIR / "data" / "nse" / "historical" / "json" / "NIFTY_50.json"
OUTPUT_DIR = BASE_DIR / "data" / "nse" / "historical" / "csv"

INDEX_NAME = "NIFTY 50"

COLUMNS = [
    "INDEX_NAME",
    "HistoricalDate",
    "OPEN",
    "HIGH",
    "LOW",
    "CLOSE",
]

def convert_file(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not isinstance(records, list) or not records:
        raise ValueError()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_file = OUTPUT_DIR / f"{json_file.stem}.csv"
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    return csv_file

def main():
    try:
        csv_file = convert_file(INPUT_FILE)
        print(
            f"{INDEX_NAME} data converted and stored successfully "
            f"at {csv_file.relative_to(BASE_DIR)}"
        )
    except Exception as e:
        print(f"ERROR : {e}")

if __name__ == "__main__":
    main()
