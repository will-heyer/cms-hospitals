import csv
import io
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import requests

catalog_url = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items"
data_dir = Path("data")
state_file = Path("state.json")


def to_snake_case(name):
    """Convert a header like "Patients’ rating" to "patients_rating"."""
    text = name.lower().replace("'", "").replace("’", "")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def process_dataset(dataset):
    """Download one CSV and save it with snake_case headers. Return True on success."""
    try:
        url = dataset["distribution"][0]["downloadURL"]
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        rows = csv.reader(io.StringIO(response.content.decode("utf-8-sig")))
        header = next(rows)
        with open(data_dir / f"{dataset['identifier']}.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([to_snake_case(column) for column in header])
            writer.writerows(rows)
        print("OK    ", dataset["title"])
        return True
    except Exception as error:
        print("FAILED", dataset["title"], error)
        return False


def main():
    state = json.loads(state_file.read_text()) if state_file.exists() else {"datasets": {}}

    catalog = requests.get(catalog_url, timeout=60).json()
    hospitals = [d for d in catalog if "Hospitals" in d.get("theme", [])]
    changed = [d for d in hospitals if state["datasets"].get(d["identifier"]) != d["modified"]]
    print(f"{len(hospitals)} hospital datasets, {len(changed)} new or modified")

    data_dir.mkdir(exist_ok=True)
    with ThreadPoolExecutor() as pool:
        results = list(pool.map(process_dataset, changed))

    for dataset, succeeded in zip(changed, results):
        if succeeded:
            state["datasets"][dataset["identifier"]] = dataset["modified"]
    state["last_run"] = datetime.now().isoformat(timespec="seconds")
    state_file.write_text(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()