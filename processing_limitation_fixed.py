import marimo

__generated_with = "0.25.1"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Import of the SL limitation texts

    For hypothesis H2 we need the full limitation texts of the Specialty List.
    They are not part of the main panel from `processing.py`, but are stored in a
    separate sheet of the monthly files.

    The import uses the same raw files and file inventory as `processing.py`
    (the data pipeline is shared with another module), but runs in its own
    notebook so that the main import stays unchanged.

    Output: `data/sl_limitations.parquet`
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. Setup

    Path to the raw data (hard-coded, located outside the project because of its
    size) and the output directory within the project. The output path is resolved
    relative to this notebook and therefore works on every machine.

    **Environment:** Python 3.14, packages managed with `uv` and listed in
    `pyproject.toml` (`marimo`, `pandas`, `pyarrow`, `python-calamine`, `xlrd`,
    `openpyxl`). After changing packages, the notebook must be fully restarted;
    otherwise saving to Parquet fails with an `ArrowKeyError` because pandas is
    loaded twice.
    """)
    return


@app.cell
def _(mo):
    import re
    import pandas as pd
    from pathlib import Path


    # raw files are outside the project (too large), only needed for this import
    # adjust to the local download folder
    RAW_PATH = Path('/Users/michaelengel/Documents/HSLU Master/Semester 2/DS in Healthcare/ds_healthcare_project/data/raw')

    # output goes into the project, relative to this notebook
    OUT_DIR = mo.notebook_dir() / "data"
    OUT_DIR.mkdir(exist_ok=True)
    return OUT_DIR, RAW_PATH, pd, re


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. File inventory

    The download folder contains files from two naming eras:

    | Pattern | Source | Date format |
    |---|---|---|
    | `BSV_per_YYYY.MM.DD.xls(x)` | BSV (older files) | `%Y.%m.%d` |
    | `Publication(s)-YYYYMMDD.xls(x)` | Publications (newer files) | `%Y%m%d` |

    The reference date is parsed from the file name. Files that match neither pattern (e.g. supplementary lists, Excel lock files `~$…`) are ignored. Files with an invalid date in their name (e.g. 31 September 2017) are skipped and listed in the output.

    **Manual correction:** the file for 2008-12-01 was downloaded with a lower-case name (`publications…`). It was renamed manually to match the pattern above; no other files were modified.

    Only files dated on the **first of the month** up to **2026-07-01** are kept,
    yielding one snapshot per month. Two checks follow:
    - **Duplicates:** two files for the same month → error, must be resolved manually.
    - **Gaps:** months without a file are listed (warning only).
    """)
    return


@app.cell
def _(pd, re):

    END_DATE = pd.Timestamp("2026-07-01")

    # file name patterns: (regex, source, date format)
    patterns = [
        (r"^BSV_per_(\d{4}\.\d{2}\.\d{2})\.xlsx?$", "BSV", "%Y.%m.%d"),
        (r"^Publications?[-_](\d{8})\.xlsx?$", "Publications", "%Y%m%d"),
    ]


    def parse_name(name):
        for pattern, source, fmt in patterns:
            m = re.match(pattern, name)
            if m:
                ref_date = pd.to_datetime(m.group(1), format=fmt, errors="coerce")
                if pd.isna(ref_date):
                    print("Invalid date in file name, skipped:", name)
                    return None, None
                return source, ref_date
        return None, None


    def list_files(raw_path, end_date):
        rows = []
        for f in raw_path.rglob("*.xls*"):
            source, ref_date = parse_name(f.name)
            if source:
                rows.append({"file": f, "source": source, "ref_date": ref_date})

        df = pd.DataFrame(rows)

        # keep only first of month and dates up to end_date
        df = df[(df["ref_date"].dt.day == 1) & (df["ref_date"] <= end_date)]
        df = df.sort_values("ref_date").reset_index(drop=True)

        # stop if there are two files for the same month
        if df["ref_date"].duplicated().any():
            raise ValueError("Duplicate reference dates found")

        return df

    return END_DATE, list_files


@app.cell
def _(END_DATE, RAW_PATH, list_files, pd):
    inventory = list_files(RAW_PATH, END_DATE)

    # which months are missing?
    _months = pd.date_range(inventory["ref_date"].min(), END_DATE, freq="MS")
    missing_months = _months.difference(inventory["ref_date"])

    print(len(inventory), "files")
    print(len(missing_months), "missing months:", list(missing_months.strftime("%Y-%m")))
    inventory
    return (inventory,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Result:** 282 monthly files from 2003-01 to 2026-07. No file exists for
    2003-03; this month is missing in the panel. One file with an invalid date
    in its name (`Publications_20170931.xls`) is skipped; it is not a
    first-of-month file and would be excluded anyway.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Sheets per file

    We list the sheet names of every file to find out from when a separate
    limitation sheet exists. Sheet names contain dates (e.g.
    `SLMonthly_01_02_2003`), so in a second step the digits are replaced by `#`
    to group sheets of the same kind. Finally we list the months with a sheet
    `Limitationen` and the column names of this sheet.
    """)
    return


@app.cell
def _(inventory, pd):
    _rows = []
    for _, _r in inventory.iterrows():
        _sheets = pd.ExcelFile(_r["file"], engine="calamine").sheet_names
        _rows.append({"ref_date": _r["ref_date"], "sheets": " | ".join(_sheets)})

    sheet_overview = pd.DataFrame(_rows)
    sheet_names = sheet_overview.assign(sheet=sheet_overview["sheets"].str.split(" | ", regex=False)).explode("sheet")

    sheet_names.groupby("sheet")["ref_date"].agg(first="min", last="max", n_files="count").sort_values("first")
    return (sheet_names,)


@app.cell
def _(sheet_names):
    _norm = sheet_names.assign(sheet=sheet_names["sheet"].str.replace(r"\d+", "#", regex=True))

    _norm.groupby("sheet")["ref_date"].agg(first="min", last="max", n_files="count").sort_values("first")
    return


@app.cell
def _(sheet_names):
    _lim_dates = sheet_names.loc[sheet_names["sheet"] == "Limitationen", "ref_date"]
    _lim_dates.dt.strftime("%Y-%m").tolist()
    return


@app.cell
def _(inventory, pd):
    _rows = []
    for _, _r in inventory[inventory["ref_date"] >= "2020-03-01"].iterrows():
        _cols = pd.read_excel(_r["file"], sheet_name="Limitationen", nrows=0, engine="calamine").columns
        for _c in _cols:
            _rows.append({"ref_date": _r["ref_date"], "column": " ".join(str(_c).split())})

    lim_headers = pd.DataFrame(_rows)
    lim_headers.groupby("column")["ref_date"].agg(first="min", last="max", n_files="count").sort_values("first")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The limitation sheet (`Limitationen`) exists in every file from 2020-03 onward
    (77 files). It also appears once in 2010-10; we leave this single file out
    because it is isolated by more than nine years.
    """)
    return


@app.cell
def _(inventory, pd):
    LIM_START = pd.Timestamp("2020-03-01")
    lim_inventory = inventory[inventory["ref_date"] >= LIM_START].reset_index(drop=True)
    len(lim_inventory)
    return (lim_inventory,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Before importing all 77 files we inspect the latest one (2026-07) to find a
    suitable key: how many rows, are GTIN, Swissmedic number and Rec-ID unique
    and complete, and does a package ever have more than one text?
    """)
    return


@app.cell
def _(lim_inventory, pd):
    # latest file (2026-07), used for the checks below
    lim_last = pd.read_excel(lim_inventory["file"].iloc[-1], sheet_name="Limitationen", dtype=str, engine="calamine")

    print(len(lim_last), "rows")
    print(lim_last["GTIN"].nunique(), "unique GTIN")
    print(lim_last["Swissmedic-Nr."].nunique(), "unique Swissmedic-Nr.")
    print(lim_last["Limitationen"].nunique(), "unique texts")
    print(lim_last["Hersteller"].nunique(), "Companies")
    lim_last.head()
    return (lim_last,)


@app.cell
def _(lim_last):
    # duplicated GTIN: same package twice, or different texts?
    _dup = lim_last[lim_last["GTIN"].duplicated(keep=False)].sort_values("GTIN")

    print("exact duplicates:", lim_last.duplicated().sum())
    print("packages with >1 distinct text:", (_dup.groupby("GTIN")["Limitationen"].nunique() > 1).sum())
    _dup[["GTIN", "Descr_DE_Full", "Limitationen"]]
    return


@app.cell
def _(lim_last):
    # packages without GTIN (partial packs)
    lim_last.loc[lim_last["GTIN"].isna(), ["Swissmedic-Nr.", "BAG-Dossier", "Rec-ID", "Descr_DE_Full"]]
    return


@app.cell
def _(lim_last):
    # missing and shared Swissmedic numbers
    print("missing Swissmedic-Nr.:", lim_last["Swissmedic-Nr."].isna().sum())
    _d = lim_last[lim_last["Swissmedic-Nr."].duplicated(keep=False)].sort_values("Swissmedic-Nr.")
    _d[["Swissmedic-Nr.", "GTIN", "Rec-ID", "Descr_DE_Full", "Limitationen"]]
    return


@app.cell
def _(lim_last):
    # Rec-ID: complete and unique?
    print("rows:", len(lim_last))
    print("missing Rec-ID:", lim_last["Rec-ID"].isna().sum())
    print("unique Rec-ID:", lim_last["Rec-ID"].nunique())
    lim_last[lim_last["Swissmedic-Nr."].isna()][["Rec-ID", "GTIN", "BAG-Dossier", "Descr_DE_Full"]]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. Structure of the limitation sheet

    The sheet has one row per package. The full limitation text of a package is
    in one cell. As key we use the `Rec-ID`: it is unique within each month.
    GTIN and Swissmedic number are not suitable on their own: partial packs
    (Teilpackungen) have no GTIN and share the Swissmedic number with the full
    pack, and a few packages have no Swissmedic number at all.

    ## 5. Import

    We read the sheet from all 77 files, rename the columns to the same English
    names as in the main panel and stack everything into one table
    (package × month).
    """)
    return


@app.cell
def _(lim_inventory, pd):
    LIM_MAP = {
        "Rec-ID": "rec_id",
        "BAG-Dossier": "dossier",
        "Swissmedic-Nr.": "swissmedic_nr",
        "GTIN": "gtin",
        "Pharmacode": "pharmacode",
        "Hersteller": "manufacturer",
        "Descr_DE_Full": "description",
        "Packsize": "pack_size",
        "Substanzen": "substances",
        "Therap. Gruppe": "therap_group",
        "ATC": "atc",
        "Lim-Pkte": "lim_points",
        "Limitationen": "limitation_text",
    }

    _parts = []
    for _i, _r in lim_inventory.iterrows():
        print(_i + 1, "/", len(lim_inventory), _r["file"].name)
        _df = pd.read_excel(_r["file"], sheet_name="Limitationen", dtype=str, engine="calamine")
        _df.columns = [" ".join(str(c).split()) for c in _df.columns]

        # co-payment: rate is part of the column name (20% until 2023, then 40%)
        _sb = [c for c in _df.columns if c.endswith("Selbstbehalt")]
        _df["deductible_rate"] = int(_sb[0].split("%")[0]) if _sb else None
        _df = _df.rename(columns={_sb[0]: "deductible"} if _sb else {})

        _df = _df.rename(columns=LIM_MAP)
        _df.insert(0, "ref_date", _r["ref_date"])
        _parts.append(_df)

    lim_raw = pd.concat(_parts, ignore_index=True)
    print(len(lim_raw), "rows")
    lim_raw.head()
    return (lim_raw,)


@app.cell
def _(lim_raw):
    # 1. unique within every month?
    _per_month = lim_raw.groupby("ref_date")["rec_id"].agg(["size", "nunique"])
    print("months with duplicate rec_id:", (_per_month["size"] != _per_month["nunique"]).sum())
    print("missing rec_id:", lim_raw["rec_id"].isna().sum())

    # 2. stable over time: does one rec_id always describe the same package?
    _stab = lim_raw.groupby("rec_id")[["swissmedic_nr", "description"]].nunique()
    print("rec_ids with >1 Swissmedic-Nr.:", (_stab["swissmedic_nr"] > 1).sum())
    print("rec_ids with >1 description:", (_stab["description"] > 1).sum())
    print("total rec_ids:", len(_stab))

    # 3. which rec_ids change their Swissmedic number?
    _ids = _stab[_stab["swissmedic_nr"] > 1].index
    lim_raw[lim_raw["rec_id"].isin(_ids)].groupby(["rec_id", "swissmedic_nr", "description"])["ref_date"].agg(["min", "max", "count"])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The `Rec-ID` is unique within every month and never missing. Over time it
    identifies the same package: of 5,213 Rec-IDs, only two change their
    Swissmedic number, and in both cases it is the same product with a new pack
    code (Dialvit 2021-08, Conbriza 2020-08). We therefore use the `Rec-ID` to
    follow packages over time and to link the texts to the main panel.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6. Data types and export

    As in the main import, IDs stay text (trailing `.0` from Excel numbers is
    removed) and the co-payment rate is stored as integer. The limitation texts
    are saved unchanged; normalising them is part of the classification step.
    """)
    return


@app.cell
def _(OUT_DIR, lim_raw):
    lim = lim_raw.copy()

    for _c in ["rec_id", "dossier", "swissmedic_nr", "gtin", "pharmacode"]:
        lim[_c] = lim[_c].astype("string").str.strip().str.replace(r"\.0$", "", regex=True)

    lim["deductible_rate"] = lim["deductible_rate"].astype("Int64")

    lim.to_parquet(OUT_DIR / "sl_limitations.parquet", index=False)
    print("saved:", lim.shape)

    _per_month = lim.groupby("ref_date").size()
    print("limited packages per month:", _per_month.min(), "-", _per_month.max())
    print("distinct raw texts:", lim["limitation_text"].nunique())
    print("empty pack_size / pharmacode:", lim["pack_size"].isna().all(), "/", lim["pharmacode"].isna().all())
    return (lim,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Link to the main panel

    Every text row should match a package in the main panel that is flagged as
    limited, and every limited package in the panel should have a text.
    """)
    return


@app.cell
def _(OUT_DIR, lim, pd):
    _panel = pd.read_parquet(OUT_DIR / "sl_panel.parquet", columns=["ref_date", "rec_id", "name", "limitation"])
    _panel = _panel[_panel["ref_date"] >= "2020-03-01"]

    # texts -> panel
    _m = lim[["ref_date", "rec_id"]].merge(_panel, on=["ref_date", "rec_id"], how="left")
    print("text rows not found in panel:", _m["limitation"].isna().sum())
    print("text rows not flagged as limited:", (_m["limitation"].str.strip() != "Y").sum())

    # limited packages in the panel -> texts
    _flagged = _panel[_panel["limitation"].str.strip() == "Y"]
    _f = _flagged.merge(lim[["ref_date", "rec_id"]], on=["ref_date", "rec_id"], how="left", indicator=True)
    _no_text = _f[_f["_merge"] == "left_only"]
    print("limited package-months without text:", len(_no_text))
    _no_text[["ref_date", "rec_id", "name"]]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Result:** 257,761 rows (package × month) from 77 files, 2020-03 to 2026-07,
    between 2,308 and 4,216 limited packages per month and 3,297 distinct raw
    texts (3,244 after normalisation in the classification step). Every text row
    links to a package in the main panel that is flagged as limited, and only one
    limited package-month in the panel has no text (Jentadueto, 2021-12). An empty
    limitation flag in the panel therefore means "not limited". The columns
    `pack_size` and `pharmacode` are empty in all files.
    """)
    return


if __name__ == "__main__":
    app.run()
