# CIP – 23 Years of the Swiss Specialty List

CIP group project (HSLU, MSc Applied Data Science and AI, HS26), group `101`.

The project builds a Python pipeline that collects the archive of the Swiss Specialty List (SL)
published by the Federal Office of Public Health (FOPH, [sl.bag.admin.ch](https://sl.bag.admin.ch/resources/current-and-archived-data))
and turns it into one consistent monthly panel (2003-01 to 2026-07). The panel is then used to
answer four research questions on data integration, generics, prices and suppliers.

## Pipeline

| Step | File | Input → Output |
|---|---|---|
| 1–2 Scraping & download | `data_scraping.py` | FFOPH archive page → `data/raw/zips/SL_YYYY.zip`, `data/meta/sl_zip_urls.csv`/`.json`, `data/meta/download_log.csv` (size, SHA-256) |
| 3 Unzip & inventory | `data_unzip.py` | yearly ZIPs → `data/raw/extracted/YYYY/`, `data/meta/file_inventory.csv`, `data/meta/monthly_selection.csv` |
| 4 Import & harmonisation | `processing.py` | monthly Excel releases → `data/sl_panel.parquet`, `data/import_log.csv` |
| 4b Limitation texts (extension) | `processing_limitation.py` | limitation sheet of the monthly releases → `data/sl_limitations.parquet` (see below) |
| 5 Analysis | `analysis.py` | panel + Swiss CPI (FSO `su-d-05.02.10`) → figures and answers Q1–Q4 |

- **Scraping:** Selenium operates the JavaScript archive page (opens the "Archiv" tab, selects each
  year, clicks the download button); the file URL is captured from the browser's network log.
  Years that fail are downloaded with `requests`, or from a manual fallback list (`manual_urls.csv`).
- **Import:** one release per month (first of the month), column names harmonised across all
  format generations, data types and value ranges checked.
- **Analysis:** missing-value heatmap (Q1), generic share (Q2), chained price index nominal/real (Q3),
  supplier count and concentration (Q4).

## Research questions

1. **Data integration:** To what extent can the SL archive be transformed into a consistent longitudinal dataset, and which limitations remain?
2. **Generics:** How have the number and share of generic versus originator packages developed since 2007?
3. **Prices:** How have published prices evolved, and how do originators and generics differ?
4. **Suppliers:** How has the number and composition of suppliers changed since 2003?

## Setup and run

Python 3.14, packages managed with uv (pyproject.toml, uv.lock). Google Chrome is required for step 1.

```bash
uv sync

# steps 1–3: scripts
uv run python data_scraping.py          # options: --years 2003-2005, --no-headless, --skip-scrape
uv run python data_unzip.py

# steps 4–5: marimo notebooks
uv run marimo edit processing.py
uv run marimo edit processing_limitation.py
uv run marimo edit analysis.py
```

- `RAW_PATH` in `processing.py` and `processing_limitation.py` must point to the local folder with the raw files.
- The CPI table `su-d-05.02.10.xlsx` (FSO) must be downloaded manually into `data/`.
- `data/` is git-ignored; all data is reproduced by running the pipeline.

## Contributions

| Member | Contribution |
|---|---|
| Hsiang-Chi Wang | `data_scraping.py`, `data_unzip.py` – scraping, download, unzip, file inventory, monthly selection |
| Michael Engel | `processing.py`, `processing_limitation.py` – import, header harmonisation, cleaning, Parquet export; README |
| Leonie Mueller | `analysis.py` – research questions Q1–Q4, CPI enrichment, figures |
## Note on data use

The FOPH archive is public; `robots.txt` was checked before scraping, and downloads are made sequentially with pauses.

## Extension: limitation texts

`processing_limitation.py` shows that the pipeline can be extended to further parts of the SL archive.
It reuses the file inventory and import logic of `processing.py` and imports the limitation sheet of
the monthly releases as a separate dataset (`data/sl_limitations.parquet`), including consistency checks
of the record IDs and a link to the main panel. The dataset was used for an analysis in the module
*Data Science in Health Care*; it is not part of the CIP research questions.
