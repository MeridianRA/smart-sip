import csv
import shutil
import calendar
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

INPUT_FILE = BASE_DIR / "data" / "nse" / "historical" / "csv_transformed" / "NIFTY_50.csv"
OUTPUT_DIR = BASE_DIR / "data" / "sip" / "stepup_amount" / "simulation"
OUTPUT_PATH_DISPLAY = f"{BASE_DIR.name}/{OUTPUT_DIR.relative_to(BASE_DIR)}"

INDEX_NAME = "NIFTY 50"
SIP_AMOUNT = 10000
STEP_UP_AMOUNT = 1000
SIP_DAYS = range(1, 32)

def read_prices():
    with open(INPUT_FILE, "r", encoding="utf-8", newline="") as f:
        prices = [(date.fromisoformat(r["date"]), r["close"]) for r in csv.DictReader(f)]
    if not prices:
        raise ValueError()
    return sorted(prices)

def group_by_month(prices):
    months = {}
    for day, close in prices:
        months.setdefault((day.year, day.month), []).append((day, close))
    return months

def ordinal(n):
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

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

def pick_trading_day(days, target):
    for day, close in days:
        if day >= target:
            return day, close
    return days[-1]

def simulate_day(months, sip_day):
    rows = []
    first_month = min(months)
    for (year, month), days in sorted(months.items()):
        target = date(year, month, min(sip_day, calendar.monthrange(year, month)[1]))
        day, close = pick_trading_day(days, target)
        months_elapsed = (year - first_month[0]) * 12 + month - first_month[1]
        amount = SIP_AMOUNT + STEP_UP_AMOUNT * (months_elapsed // 12)
        rows.append([day.isoformat(), close, f"{amount / float(close):.4f}", amount])

    if not rows:
        raise ValueError()

    with open(OUTPUT_DIR / f"{sip_day}.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "price", "quantity", "amount"])
        writer.writerows(rows)

def main():
    try:
        months = group_by_month(read_prices())
        prepare_output_dir()
    except Exception as error:
        print(f"ERROR : {type(error).__name__}")
        return

    print(f"\nSimulating step-up SIP (amount) for {INDEX_NAME} ...\n")

    success = 0
    for sip_day in SIP_DAYS:
        label = f"{'Monthly ' + ordinal(sip_day):<12}  "
        try:
            simulate_day(months, sip_day)
        except Exception as error:
            print(f"{label}->  ERROR : {type(error).__name__}")
            continue
        print(f"{label}->  SUCCESS")
        success += 1

    print(f"\nExported data for {success}/{len(SIP_DAYS)} dates")
    print(f"Saved to : {OUTPUT_PATH_DISPLAY}")

if __name__ == "__main__":
    main()
