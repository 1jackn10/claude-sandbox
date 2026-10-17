#!/usr/bin/env python3
"""Plot US baby-name popularity by year.

Data: US Social Security Administration (SSA) baby names
(https://www.ssa.gov/oact/babynames/limits.html). If ssa.gov is unreachable, falls
back to hadley/data-baby-names, a GitHub copy of the same SSA data (top 1000 names
per sex per year, 1880-2008).

Popularity is the share of that sex's births in the year given that name.

Usage:
    python baby_names.py Emma Olivia          # compare names
    python baby_names.py Jack --sex M         # restrict to one sex
    python baby_names.py Mary --save mary.png # write PNG instead of opening a window
    python baby_names.py                      # interactive prompt
"""
import argparse
import csv
import io
import re
import sys
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

SSA_URL = "https://www.ssa.gov/oact/babynames/names.zip"
MIRROR_URL = "https://raw.githubusercontent.com/hadley/data-baby-names/master/baby-names.csv"
CACHE_DIR = Path.home() / ".cache" / "baby_names"


def fetch(url, dest):
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            dest.write_bytes(r.read())
    return dest


def load_ssa():
    """Parse yobYYYY.txt files (name,sex,count) into {(NAME, sex): {year: share %}}."""
    path = fetch(SSA_URL, CACHE_DIR / "names.zip")
    rows, totals = [], defaultdict(int)
    with zipfile.ZipFile(path) as z:
        for fn in z.namelist():
            m = re.fullmatch(r"yob(\d{4})\.txt", fn)
            if not m:
                continue
            year = int(m.group(1))
            for name, sex, n in csv.reader(io.TextIOWrapper(z.open(fn), "utf-8")):
                rows.append((year, name.upper(), sex, int(n)))
                totals[year, sex] += int(n)
    data = defaultdict(dict)
    for year, name, sex, n in rows:
        data[name, sex][year] = 100 * n / totals[year, sex]
    return data


def load_mirror():
    """Parse the mirror CSV (year,name,percent,sex) into the same structure."""
    path = fetch(MIRROR_URL, CACHE_DIR / "baby-names.csv")
    data = defaultdict(dict)
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            sex = "M" if r["sex"] == "boy" else "F"
            data[r["name"].upper(), sex][int(r["year"])] = 100 * float(r["percent"])
    return data


def load():
    try:
        return load_ssa(), "SSA"
    except Exception as e:
        print(f"SSA download failed ({e}); using GitHub mirror (1880-2008).", file=sys.stderr)
        return load_mirror(), "SSA via hadley/data-baby-names"


def plot(data, names, sex, source, save=None):
    import matplotlib
    if save:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 5.5))
    found = False
    for name in names:
        for s in ("F", "M") if sex is None else (sex,):
            series = data.get((name.upper(), s))
            if not series:
                continue
            found = True
            years = range(min(series), max(series) + 1)
            ax.plot(years, [series.get(y, 0) for y in years], linewidth=2,
                    label=f"{name.title()} ({s})")
    if not found:
        print(f"No data for: {', '.join(names)}", file=sys.stderr)
        plt.close(fig)
        return False
    ax.set(xlabel="Year", ylabel="% of births of that sex",
           title="US baby name popularity by year")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.text(0.99, 0.01, f"Source: {source}", ha="right", fontsize=7, color="gray")
    fig.tight_layout()
    if save:
        fig.savefig(save, dpi=150)
        print(f"Saved {save}")
    else:
        plt.show()
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help="baby name(s) to plot")
    ap.add_argument("--sex", choices=["M", "F"], help="only this sex (default: both)")
    ap.add_argument("--save", metavar="PNG", help="save plot to file instead of showing it")
    args = ap.parse_args()

    data, source = load()
    if args.names:
        sys.exit(0 if plot(data, args.names, args.sex, source, args.save) else 1)
    while True:
        try:
            line = input("Name(s), space-separated (blank to quit): ").strip()
        except EOFError:
            break
        if not line:
            break
        plot(data, line.split(), args.sex, source)


if __name__ == "__main__":
    main()
