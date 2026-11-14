import json
import time
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
import requests

BASE_DIR = Path(__file__).resolve().parent.parent.parent

INDEX_NAME = "NIFTY 50"
OUTPUT_DIR = BASE_DIR / "data" / "nse" / "historical" / "json"
OUTPUT_FILE = OUTPUT_DIR / f"{INDEX_NAME.replace(' ', '_')}.json"
OUTPUT_PATH_DISPLAY = f"{BASE_DIR.name}/{OUTPUT_DIR.relative_to(BASE_DIR)}"

START_YEAR = 2001

CHUNK_SLEEP = 1

BASE_URL = "https://www.niftyindices.com"
API_URL = f"{BASE_URL}/BackPage/getHistoricaldatatabletoString"

HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-GB,en;q=0.7",
    "content-type": "application/json; charset=UTF-8",
    "origin": BASE_URL,
    "referer": f"{BASE_URL}/reports/historical-data",
    "x-requested-with": "XMLHttpRequest",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/156.0.0.0 Safari/537.36"
    ),
}

def build_chunks():
    today = date.today()
    last_month_end = today.replace(day=1) - timedelta(days=1)
    chunks = []
    for year in range(START_YEAR, last_month_end.year + 1):
        end = date(year, 12, 31) if year < last_month_end.year else last_month_end
        chunks.append((year, date(year, 1, 1), end))
    return chunks

CHUNKS = build_chunks()

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

def create_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    session.get(BASE_URL, timeout=10).raise_for_status()
    time.sleep(1)
    return session

def fetch_chunk(session, start, end):
    cinfo = (
        f"{{'name':'{INDEX_NAME}','startDate':'{start.strftime('%d-%b-%Y')}',"
        f"'endDate':'{end.strftime('%d-%b-%Y')}','indexName':'{INDEX_NAME}'}}"
    )
    resp = session.post(API_URL, data=json.dumps({"cinfo": cinfo}), timeout=30)
    resp.raise_for_status()
    records = resp.json()
    if not isinstance(records, list):
        raise ValueError()
    return records

def parse_date(record):
    return datetime.strptime(record["HistoricalDate"], "%d %b %Y").date()

def process_year(session, year, start, end, records):
    try:
        chunk = fetch_chunk(session, start, end)
        for record in chunk:
            records[parse_date(record)] = record
    except (requests.RequestException, ValueError, KeyError, TypeError) as error:
        print(f"{year}  ->  ERROR : {type(error).__name__}")
        return False
    print(f"{year}  ->  {len(chunk):>3} records")
    return True

def main():
    try:
        session = create_session()
        prepare_output_dir()
    except Exception as error:
        print(f"ERROR : {type(error).__name__}")
        return

    total = len(CHUNKS)
    print(f"\nDownloading data for {INDEX_NAME} ...\n")

    records = {}
    success = 0
    for index, (year, start, end) in enumerate(CHUNKS):
        if index:
            time.sleep(CHUNK_SLEEP)
        success += process_year(session, year, start, end, records)

    try:
        rows = [records[key] for key in sorted(records)]
        OUTPUT_FILE.write_text(
            json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError as error:
        print(f"\nERROR : {type(error).__name__}")
        return

    print(f"\nDownloaded data for {success}/{total} years")
    print(f"Saved to : {OUTPUT_PATH_DISPLAY}")

if __name__ == "__main__":
    main()
