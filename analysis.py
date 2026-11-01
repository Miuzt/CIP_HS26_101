import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Analysis of the Swiss Specialty List (SL), 2003–2026

    Last step of the pipeline: answers the research questions Q1–Q4 with the
    panel from `processing.py` (`data/sl_panel.parquet`, one row per package and
    monthly release, 2003-01 to 2026-07), enriched with the Swiss consumer price
    index (CPI, FSO table `su-d-05.02.10`, saved in `data/`).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    # ------------------------------------------------------------------
    # Setup: packages, paths and plot style
    # ------------------------------------------------------------------
    import re

    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.ticker import FuncFormatter, PercentFormatter

    # input files are in the (git-ignored) data folder next to this notebook
    DATA_DIR = mo.notebook_dir() / "data"
    PANEL_FILE = DATA_DIR / "sl_panel.parquet"
    CPI_FILE = DATA_DIR / "su-d-05.02.10.xlsx"  # FSO, CPI long series (download manually)

    # Q2 and the price index start in 2007: the originator code "O" exists only from then on
    START_2007 = pd.Timestamp("2007-01-01")

    # one fixed colour per category, used in every figure
    COLORS = {
        "Generic": "#2a78d6",
        "Originator": "#eb6834",
        "Complementary": "#1baf7a",
        "No code": "#9a9890",
    }

    # simple, consistent look for all figures
    plt.rcParams.update({
        "figure.dpi": 110,
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#e4e3df",
        "axes.axisbelow": True,
        "legend.frameon": False,
    })
    return (
        COLORS,
        CPI_FILE,
        FuncFormatter,
        PANEL_FILE,
        PercentFormatter,
        START_2007,
        mdates,
        np,
        pd,
        plt,
        re,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Data preparation

    Partial packs ("Teilpackung", 93 rows) and rows without Swissmedic number
    (5,457) are excluded. The generic code is mapped to *Generic* (G),
    *Originator* with generic competition (O), *Complementary* medicine (K) and
    *No code* (empty). Public prices of 0 are excluded from the price analysis.
    Manufacturer names are harmonised (lower case, without legal form and
    country).
    """)
    return


@app.cell(hide_code=True)
def _(PANEL_FILE, pd, re):
    # ------------------------------------------------------------------
    # Load the panel and add the analysis columns
    # ------------------------------------------------------------------
    # only the columns needed for Q2-Q4 (keeps memory use low)
    sl = pd.read_parquet(
        PANEL_FILE,
        columns=["ref_date", "swissmedic_nr", "name", "generic", "manufacturer", "pub_price"],
    )

    # translate the SL generic code into readable categories
    sl["category"] = sl["generic"].map(
        {"G": "Generic", "O": "Originator", "K": "Complementary"}
    ).fillna("No code")


    def clean_company(name):
        """Harmonise a manufacturer name, e.g. 'Pfizer (Schweiz) AG' -> 'pfizer'."""
        name = name.lower()
        name = re.sub(r"[().,&\-/']", " ", name)  # punctuation -> space
        name = re.sub(r"\b(schweiz|suisse|switzerland)\b", " ", name)  # country
        name = re.sub(r"\b(ag|gmbh|sa|sàrl|sarl|ltd|inc|co|kg)\b", " ", name)  # legal form
        return " ".join(name.split())


    # clean each distinct name once, then map the result to all rows
    unique_names = sl["manufacturer"].dropna().unique()
    sl["company"] = sl["manufacturer"].map({n: clean_company(n) for n in unique_names})

    # analysis set: without partial packs and without rows lacking an identifier
    is_partial = sl["name"].str.contains("Teilpackung", case=False, na=False)
    ana = sl[~is_partial & sl["swissmedic_nr"].notna()].copy()
    return (ana,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Q1 – Data integration

    *To what extent can the SL archive be transformed into a consistent
    longitudinal dataset, and which limitations remain?*

    281 of 282 possible monthly releases (only 2003-03 is missing) form one panel
    of 2.5 million rows. The number of packages grows smoothly from 6,500 to
    10,300; the only month-to-month jump above 3 % (2011-09, +5.4 %) is real growth.
    Duplicate Swissmedic numbers per release fall from 0.8 % (2003) to 0.05 % (2026).
    """)
    return


@app.cell(hide_code=True)
def _(PANEL_FILE, pd, plt):
    # ------------------------------------------------------------------
    # Figure 1: share of missing values per column and year (heatmap)
    # ------------------------------------------------------------------
    heat_cols = ["swissmedic_nr", "pharmacode", "gtin", "manufacturer",
                 "generic", "atc", "exf_price", "pub_price", "deductible",
                 "price_model", "limitation", "last_price_change"]

    # read only these columns; isna() gives True/False, and the mean per
    # year is the share of missing values
    _panel = pd.read_parquet(PANEL_FILE, columns=["ref_date"] + heat_cols)
    missing = _panel[heat_cols].isna().groupby(_panel["ref_date"].dt.year).mean().T * 100
    del _panel  # free memory

    fig1, ax1 = plt.subplots(figsize=(8, 2.9))
    image = ax1.imshow(missing, aspect="auto", cmap="Blues", vmin=0, vmax=100)
    ax1.set_xticks(range(len(missing.columns)), missing.columns, rotation=90)
    ax1.set_yticks(range(len(missing.index)), missing.index)
    ax1.grid(False)
    fig1.colorbar(image, ax=ax1, fraction=0.03, pad=0.01, label="Missing values (%)")
    ax1.set_title("Figure 1 · Share of missing values per column and year")
    fig1
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Interpretation.** Identifier, manufacturer and public price are complete
    over the whole period, but the content of the SL changed (Figure 1): the
    Pharmacode ends in 2014, the GTIN starts in 2015, the ATC code is complete
    from 2016 and the price model exists from 2021. The generic code is missing
    for 83 % of rows in 2003 and for 37 % in 2026. Each question can therefore
    only use the period in which its variables are filled.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Q2 – Generics

    *How have the number and share of generic versus originator packages
    developed since 2007?*
    """)
    return


@app.cell(hide_code=True)
def _(COLORS, PercentFormatter, START_2007, ana, mdates, pd, plt):
    # ------------------------------------------------------------------
    # Figure 2: share of packages per generic category (stacked area)
    # ------------------------------------------------------------------
    order = ["Generic", "Originator", "Complementary", "No code"]

    # number of packages per month and category -> share in % per month
    counts = pd.crosstab(ana["ref_date"], ana["category"])[order]
    counts = counts[counts.index >= START_2007]
    shares = counts.div(counts.sum(axis=1), axis=0) * 100

    fig2, ax2 = plt.subplots(figsize=(8, 2.3))
    ax2.stackplot(shares.index, shares.T, labels=order,
                  colors=[COLORS[c] for c in order], edgecolor="white", linewidth=0.5)
    ax2.yaxis.set_major_formatter(PercentFormatter(100))
    ax2.xaxis.set_major_locator(mdates.YearLocator(2))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax2.set_ylabel("Share of listed packages")
    ax2.set_title("Figure 2 · Packages by generic code, 2007–2026")
    ax2.legend(loc="upper left", ncol=4, fontsize=8)
    ax2.set_ylim(0, 115)  # room for the legend above the stack
    ax2.set_yticks(range(0, 101, 20))

    fig2
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Interpretation.** Generic packages more than tripled (1,457 → 4,717); their
    share of all packages rose from 21 % to 46 % (Figure 2), mainly between 2007
    and 2014 and again from 2020. Originators with generic competition grew as
    well (521 → 1,382), so the ratio of about three to four generics per
    originator stayed stable. *Limitation:* the meaning of an empty code is not
    documented (mostly originators without generic competition).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Q3 – Prices

    *How have published prices evolved, and how do originators and generics
    differ?* To avoid a bias from new, expensive products, we use a **chained
    price index**: the mean price change of the same package between two
    releases, chained to 2007-01 = 100; the **real** index divides it by the CPI.
    """)
    return


@app.cell(hide_code=True)
def _(CPI_FILE, START_2007, ana, np, pd):
    # ------------------------------------------------------------------
    # Chained price index (nominal and real)
    # ------------------------------------------------------------------
    # one row per package and month, valid public price only
    prices = ana.loc[ana["pub_price"] > 0, ["ref_date", "swissmedic_nr", "category", "pub_price"]]
    prices = prices.drop_duplicates(["ref_date", "swissmedic_nr"], keep=False)
    prices = prices.sort_values(["swissmedic_nr", "ref_date"])

    # price and category of the same package in its previous release
    prev = prices.groupby("swissmedic_nr")
    prices["prev_price"] = prev["pub_price"].shift()
    prices["prev_category"] = prev["category"].shift()
    prices["prev_date"] = prev["ref_date"].shift()

    # keep consecutive releases only (gap of max. 2 months because 2003-03 is missing)
    months_apart = (prices["ref_date"] - prices["prev_date"]).dt.days
    pairs = prices[(months_apart <= 62) & (prices["category"] == prices["prev_category"])].copy()

    # log change of the price; changes > factor 3 in one month are treated as errors
    pairs["log_change"] = np.log(pairs["pub_price"] / pairs["prev_price"])
    pairs = pairs[pairs["log_change"].abs() <= np.log(3)]


    def chained_index(df):
        """Average monthly log change -> cumulative index, 2007-01 = 100."""
        monthly = df.groupby("ref_date")["log_change"].mean()
        monthly = monthly[monthly.index > START_2007]
        return 100 * np.exp(monthly.cumsum()).reindex(
            monthly.index.union([START_2007]), fill_value=1.0
        )


    index = pd.DataFrame({
        "Generic": chained_index(pairs[pairs["category"] == "Generic"]),
        "Originator": chained_index(pairs[pairs["category"] == "Originator"]),
        "All packages": chained_index(pairs),
    })

    # CPI: column 5 of the FSO table is the continuous monthly series (base Dec 1982)
    cpi = pd.read_excel(CPI_FILE, sheet_name="LIK_multibasis_m", header=None, skiprows=4)
    cpi = cpi[pd.to_datetime(cpi[0], errors="coerce").notna()]
    cpi = pd.Series(cpi[5].astype(float).values, index=pd.to_datetime(cpi[0]))
    cpi = 100 * cpi / cpi[START_2007]  # rebase to 2007-01 = 100

    real_index = index.div(cpi.reindex(index.index), axis=0) * 100
    return cpi, index, real_index


@app.cell(hide_code=True)
def _(COLORS, cpi, index, mdates, pd, plt, real_index):
    # ------------------------------------------------------------------
    # Figure 3: price index, nominal and real (line chart, two panels)
    # ------------------------------------------------------------------
    fig3, axes3 = plt.subplots(1, 2, figsize=(9, 2.7), sharey=True)
    line_colors = {"Generic": COLORS["Generic"], "Originator": COLORS["Originator"],
                   "All packages": "black"}

    for _ax, _data, _title in [(axes3[0], index, "nominal"),
                            (axes3[1], real_index, "real (CPI-deflated)")]:
        for _col in _data.columns:
            _ax.plot(_data.index, _data[_col], color=line_colors[_col], label=_col,
                    lw=1.2 if _col == "All packages" else 1.8)
            if _col == "All packages":
                continue  # label only the two categories
            _ax.annotate(f"{_data[_col].iloc[-1]:.0f}", (_data.index[-1], _data[_col].iloc[-1]),
                        xytext=(3, 0), textcoords="offset points", fontsize=8, va="center")
        _ax.axhline(100, color="grey", lw=0.8)
        _ax.axvline(pd.Timestamp("2024-07-01"), color="grey", lw=0.7, ls=":")
        _ax.set_title(f"Price index, {_title}")
        _ax.xaxis.set_major_locator(mdates.YearLocator(4))
        _ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    axes3[0].plot(cpi.loc[index.index].index, cpi.loc[index.index], color="grey",
                  ls="--", lw=1, label="CPI")
    axes3[0].set_ylabel("Index (2007-01 = 100)")
    axes3[0].legend(loc="lower left", fontsize=8)
    fig3.suptitle("Figure 3 · Chained index of public prices (same package, month to month)",
                  x=0.01, ha="left", fontweight="bold", fontsize=10)
    fig3.tight_layout()
    fig3
    return


@app.cell(hide_code=True)
def _(COLORS, FuncFormatter, ana, plt):
    # ------------------------------------------------------------------
    # Figure 4: price level per package, January releases (box plot)
    # ------------------------------------------------------------------
    years = [2007, 2011, 2015, 2019, 2023, 2026]
    january = ana[(ana["ref_date"].dt.month == 1) & (ana["pub_price"] > 0)]

    fig4, ax4 = plt.subplots(figsize=(8, 2.2))
    for i, year in enumerate(years):
        for j, cat in enumerate(["Generic", "Originator"]):
            values = january[(january["ref_date"].dt.year == year)
                             & (january["category"] == cat)]["pub_price"]
            box = ax4.boxplot(values, positions=[i * 3 + j], widths=0.8,
                              patch_artist=True, showfliers=False,
                              medianprops={"color": "black"})
            box["boxes"][0].set(facecolor=COLORS[cat], edgecolor=COLORS[cat])

    ax4.set_yscale("log")
    ax4.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:g}"))  # 10 instead of 10^1
    ax4.set_xticks([i * 3 + 0.5 for i in range(len(years))], years)
    ax4.set_ylabel("Public price (CHF, log scale)")
    ax4.set_title("Figure 4 · Public price per package, January releases")
    legend_boxes = [plt.Rectangle((0, 0), 1, 1, color=COLORS["Generic"]),
                    plt.Rectangle((0, 0), 1, 1, color=COLORS["Originator"])]
    ax4.set_ylim(1, 1500)  # room for the legend
    ax4.legend(legend_boxes, ["Generic", "Originator"], loc="upper left", ncol=2)
    ax4.grid(axis="x", visible=False)
    fig4
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Interpretation.** Prices of identical packages fell markedly (Figure 3):
    in July 2026 the nominal index is 48 for originators and 66 for generics, in
    real terms 44 and 59 (CPI +11 %). The steps match the periodic price reviews
    of the FOPH (e.g. 2010, 2012–2014, 2018); originators lost clearly more than
    generics. The only increase (July 2024, dotted line) results from the new
    distribution share, which raised public prices of very cheap packages while
    ex-factory prices stayed unchanged. The price **level** of a typical package
    still rose slightly (Figure 4, median generic CHF 30 → 39), because new
    packages enter at higher prices. *Limitations:* no sales volumes; for packages
    with a confidential price model the published price is not the effective one.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Q4 – Suppliers

    *How has the number and composition of suppliers changed since 2003?*
    """)
    return


@app.cell(hide_code=True)
def _(COLORS, PercentFormatter, ana, mdates, plt):
    # ------------------------------------------------------------------
    # Figure 5: concentration (line) and largest suppliers (bars)
    # ------------------------------------------------------------------
    # share of each company in all listed packages per month
    per_company = ana.groupby(["ref_date", "company"]).size()
    share = per_company / per_company.groupby("ref_date").transform("sum")
    top10_share = share.groupby("ref_date").apply(lambda s: s.nlargest(10).sum()) * 100

    first, last = ana["ref_date"].min(), ana["ref_date"].max()


    def top_suppliers(date, n=6):
        """Number of listed packages of the n largest suppliers in one release."""
        return ana[ana["ref_date"] == date].groupby("manufacturer").size().nlargest(n)


    fig5, axes5 = plt.subplots(1, 3, figsize=(10, 2.6),
                               gridspec_kw={"width_ratios": [1.2, 1, 1]})

    # left: share of the ten largest suppliers over time
    axes5[0].plot(top10_share.index, top10_share, color=COLORS["Originator"])
    axes5[0].set_ylim(0, 100)
    axes5[0].yaxis.set_major_formatter(PercentFormatter(100))
    axes5[0].xaxis.set_major_locator(mdates.YearLocator(6))
    axes5[0].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axes5[0].set_ylabel("Share of listed packages")
    axes5[0].set_title("Top-10 share")

    # middle and right: largest suppliers in the first and last release
    for _ax, _date in [(axes5[1], first), (axes5[2], last)]:
        _top = top_suppliers(_date).sort_values()
        _ax.barh(_top.index, _top.values, color=COLORS["Generic"])
        _ax.set_xlim(0, 1300)
        _ax.set_xlabel("Listed packages")
        _ax.set_title(f"Largest suppliers {_date:%Y-%m}")
        _ax.tick_params(axis="y", labelsize=7)
        _ax.grid(axis="y", visible=False)

    fig5.suptitle("Figure 5 · Concentration and largest suppliers",
                  x=0.01, ha="left", fontweight="bold", fontsize=10)
    fig5.tight_layout()
    fig5
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Interpretation.** The number of suppliers is stable at 175–200 per release,
    but concentration increased: the ten largest suppliers list 50 % of all
    packages in 2026, compared with 35 % in 2003 (Figure 5). In 2003 the leaders
    were a mix of originator (Novartis, Pharmacia) and generic companies
    (Streuli, Mepha); in 2026 generic companies clearly dominate, and Sandoz and
    Mepha each list three times as many packages as the leader in 2003.
    *Limitations:* shares are based on listings, not sales; takeovers and
    renamings are not merged.
    """)
    return


if __name__ == "__main__":
    app.run()
