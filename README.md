# CMS Hospitals take home

Downloads every CMS provider dataset with the theme "Hospitals", converts all CSV column names to snake_case, and saves the files to data/. Designed to run daily. Each run only downloads datasets that changed since the previous run.

Requires Python 3.10+.

## Run

From the project folder:

```
pip install -r requirements.txt
python main.py
```

## Schedule daily

- **Linux (cron):** `0 6 * * * cd /path/to/cms && python main.py`

## How it works

1. Fetches the CMS metastore catalog and keeps datasets whose theme includes "Hospitals".
2. Compares each dataset's modified date with state.json from the previous run, keeping only new or changed datasets.
3. Downloads and processes those CSVs in parallel with a thread pool, rewriting the header row to snake_case.
4. Records each successful dataset's modified date, plus the run time, in state.json.

## Design notes

- **Simple by design:** one file, Python's standard library plus requests.
- **Threads for parallelism:** the work is mostly waiting on the network, so threads are the simplest fit.
- **Failures retry automatically:** a dataset that fails to download isn't recorded, so the next run tries it again.
- **Scheduling is left to the OS** (cron or Task Scheduler) rather than built into the script.

## Known limitations

- CMS modified values are dates without times, so two updates on the same day look like one.
- Each CSV is processed in memory, which is fine for these file sizes.