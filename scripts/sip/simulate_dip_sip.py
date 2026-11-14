import csv
import shutil
from datetime import date
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

INPUT_FILE = BASE_DIR / "data" / "nse" / "historical" / "csv_transformed" / "NIFTY_50.csv"
OUTPUT_DIR = BASE_DIR / "data" / "sip" / "dip" / "simulation"
OUTPUT_PATH_DISPLAY = f"{BASE_DIR.name}/{OUTPUT_DIR.relative_to(BASE_DIR)}"

INDEX_NAME = "NIFTY 50"
SIP_AMOUNT = 10000
# invest when close <= previous close reduced by this % (0.1% to 2.0%)
DROP_PERCENTS = [Decimal(i) / 10 for i in range(1, 21)]

def read_prices():
    with open(INPUT_FILE, "r", encoding="utf-8", newline="") as f:
        prices = [(date.fromisoformat(r["date"]), r["close"]) for r in csv.DictReader(f)]
    if not prices:
        raise ValueError()
    return sorted(prices)

def prepare_output_dir():
    if OUTPUT_DIR.exists():
        for child in OUTPUT_DIR.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        print(f"\nOutput directory exists : {OUTPUT_PATH_DISPLAY}")
        print("Cleared output directory")
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"\nCreated output directory : {OUTPUT_PATH_DISPLAY}")

def simulate_case(prices, drop_percent):
    rows = []
    factor = 1 - drop_percent / 100
    for (_, prev_close), (day, close) in zip(prices, prices[1:]):
        if Decimal(close) <= Decimal(prev_close) * factor:
            rows.append([day.isoformat(), close, f"{SIP_AMOUNT / float(close):.4f}"])

    if not rows:
        raise ValueError()

    with open(OUTPUT_DIR / f"{drop_percent:.1f}.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "price", "quantity"])
        writer.writerows(rows)

def main():
    try:
        prices = read_prices()
        prepare_output_dir()
    except Exception as error:
        print(f"ERROR : {type(error).__name__}")
        return

    print(f"\nSimulating SIP for {INDEX_NAME} ...\n")

    success = 0
    for drop_percent in DROP_PERCENTS:
        label = f"{'Drop ' + f'{drop_percent:.1f}' + '%':<8}  "
        try:
            simulate_case(prices, drop_percent)
        except Exception as error:
            print(f"{label}->  ERROR : {type(error).__name__}")
            continue
        print(f"{label}->  SUCCESS")
        success += 1

    print(f"\nExported data for {success}/{len(DROP_PERCENTS)} cases")
    print(f"Saved to : {OUTPUT_PATH_DISPLAY}")

if __name__ == "__main__":
    main()
