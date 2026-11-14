import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

IN_DIR = BASE_DIR / "data" / "sip" / "dip_scaled" / "simulation"
PRICE_FILE = BASE_DIR / "data" / "nse" / "historical" / "csv_transformed" / "NIFTY_50.csv"
OUT_FILE = BASE_DIR / "data" / "sip" / "dip_scaled" / "summary.csv"
OUT_FILE_DISPLAY = str(OUT_FILE.relative_to(BASE_DIR))

INDEX_NAME = "NIFTY 50"
DECIMALS = 2
HEADER = ["drop_percent", "invested_amount", "quantity", "final_amount", "xirr", "investments"]

def read_latest_price():
    with PRICE_FILE.open(newline="", encoding="utf-8") as f:
        rows = [(date.fromisoformat(row["date"]), float(row["close"])) for row in csv.DictReader(f)]
    if not rows:
        raise ValueError()
    return max(rows)

def xirr(cashflows):
    first = cashflows[0][0]

    def npv(rate):
        return sum(amount / (1 + rate) ** ((day - first).days / 365) for day, amount in cashflows)

    low, high = -0.999999, 10.0
    if npv(low) * npv(high) > 0:
        raise ValueError()
    for _ in range(200):
        mid = (low + high) / 2
        if npv(low) * npv(mid) <= 0:
            high = mid
        else:
            low = mid
    return (low + high) / 2

def summarize(path, last_date, last_price):
    with path.open(newline="", encoding="utf-8") as f:
        rows = [
            (date.fromisoformat(row["date"]), float(row["quantity"]), float(row["amount"]))
            for row in csv.DictReader(f)
        ]
    if not rows:
        raise ValueError()

    invested = sum(amount for _, _, amount in rows)
    quantity = sum(qty for _, qty, _ in rows)
    final_amount = quantity * last_price

    cashflows = [(day, -amount) for day, _, amount in sorted(rows)]
    cashflows.append((last_date, final_amount))
    return [
        path.stem,
        round(invested, DECIMALS),
        round(quantity, DECIMALS),
        round(final_amount, DECIMALS),
        round(xirr(cashflows) * 100, DECIMALS),
        len(rows),
    ]

def main():
    try:
        if not IN_DIR.exists():
            raise FileNotFoundError()
        last_date, last_price = read_latest_price()
    except (OSError, KeyError, ValueError, csv.Error) as exc:
        print(f"ERROR : {type(exc).__name__}")
        return

    files = sorted(IN_DIR.glob("*.csv"), key=lambda p: Decimal(p.stem))
    rows = []
    for path in files:
        try:
            rows.append(summarize(path, last_date, last_price))
        except (OSError, KeyError, ValueError, csv.Error) as exc:
            print(f"ERROR : {type(exc).__name__}")

    if not rows:
        print("ERROR : ValueError")
        return

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(rows)

    print(f"{INDEX_NAME} scaled-amount dip SIP data summarized and exported successfully at {OUT_FILE_DISPLAY}")

if __name__ == "__main__":
    main()
