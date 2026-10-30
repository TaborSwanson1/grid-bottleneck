# ==============================================================================
# Script: lease_notes.py
# Project: Grid Bottleneck - Leases signed but not yet started
# Objective: Leases show up on the balance sheet only when the building is
#            handed over. Before that, companies describe signed leases that
#            "have not yet commenced" in the lease note, as text. This pulls
#            those sentences from every 10-Q and 10-K since 2022.
# Inputs:  SEC submissions API and filing documents
# Outputs: data/raw/sec/filings/*.txt (cached text, git-ignored),
#          data/clean/lease_note_sentences.csv, data/clean/leases_not_commenced.csv,
#          charts/leases_not_commenced.png
# ==============================================================================

from pathlib import Path
import html
import json
import re
import ssl
import time
import urllib.request

import certifi
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

import style  # noqa: F401  (turns off math parsing so "$" prints as written)
import pandas as pd

from capex import user_agent

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data/raw/sec/filings"
CIKS = {
    "Amazon": "0001018724", "Microsoft": "0000789019", "Alphabet": "0001652044",
    "Meta": "0001326801", "Oracle": "0001341439", "CoreWeave": "0001769628", "IREN": "0001878848",
}
CTX = ssl.create_default_context(cafile=certifi.where())
PATTERN = re.compile(r"(not yet commenced|have not commenced|has not commenced|not commenced|yet to commence)", re.I)


def get(url: str) -> bytes:
    time.sleep(0.15)  # SEC asks for no more than 10 requests a second
    req = urllib.request.Request(url, headers={"User-Agent": user_agent()})
    return urllib.request.urlopen(req, context=CTX).read()


def filings(cik: str) -> list[dict]:
    sub = json.loads(get(f"https://data.sec.gov/submissions/CIK{cik}.json"))
    pages = [sub["filings"]["recent"]]
    pages += [json.loads(get(f"https://data.sec.gov/submissions/{f['name']}")) for f in sub["filings"]["files"]]
    out = []
    for p in pages:
        for form, acc, doc, period in zip(p["form"], p["accessionNumber"], p["primaryDocument"], p["reportDate"]):
            if form in ("10-Q", "10-K") and period >= "2022-01-01":
                out.append({"form": form, "acc": acc, "doc": doc, "period": period})
    return sorted(out, key=lambda f: f["period"])


def filing_text(name: str, cik: str, f: dict) -> str:
    path = CACHE / f"{name.lower()}_{f['period']}_{f['form']}.txt"
    if not path.exists():
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{f['acc'].replace('-', '')}/{f['doc']}"
        raw = get(url).decode("utf-8", errors="ignore")
        text = re.sub(r"<[^>]+>", " ", raw)
        text = re.sub(r"\s+", " ", html.unescape(text))
        path.write_text(text)
    return path.read_text()


def sentences(text: str) -> list[str]:
    # Split on sentence ends; keep only sentences about leases that haven't started
    parts = re.split(r"(?<=[.;])\s+(?=[A-Z(])", text)
    return [s.strip() for s in parts if PATTERN.search(s) and "lease" in s.lower() and len(s) < 1200]


AMOUNT = r"\$\s?([\d,]+(?:\.\d+)?)\s?(billion|million)"
# Each company words this differently; one rule each, checked by reading the matches.
# IREN is left out: in its leases it's the landlord, not the tenant.
RULES = {
    # Before mid-2025 Microsoft split it: "$8.6 billion and $108.4 billion, respectively"
    "Microsoft": [r"not yet commenced of " + AMOUNT + r"(?: and " + AMOUNT + r")?"],
    # Early Meta filings also split operating and finance
    "Meta": [r"lease obligations were approximately " + AMOUNT,
             r"not yet commenced[^$]{0,200}?" + AMOUNT + r"(?: and " + AMOUNT + r")?"],
    # Oracle only states a dollar figure from February 2025 on
    "Oracle": [r"we ha(?:d|ve) " + AMOUNT + r" of additional lease commitments"],
    # Alphabet's 10-Ks split short-term and long-term payments
    "Alphabet": [r"not yet commenced with (?:short-term and long-term )?(?:future )?(?:short-term and long-term )?"
                 r"lease payments of (?:approximately )?" + AMOUNT + r"(?: and " + AMOUNT + r")?",
                 AMOUNT + r" future payments for leases not yet commenced"],
    "CoreWeave": [r"leases is " + AMOUNT],
    # Amazon puts it in the commitments table, in millions; the last number is the total
    "Amazon": [r"Leases not yet commenced ((?:[\d,]+ ){5,8})"],
}


def extract(name: str, text: str) -> tuple[float, str] | None:
    for rule in RULES[name]:
        m = re.search(rule, text, re.I)
        if not m:
            continue
        quote = text[max(0, m.start() - 120): m.end() + 60]
        if name == "Amazon":
            return float(m.group(1).split()[-1].replace(",", "")) * 1e6, quote
        total = 0.0
        groups = m.groups()
        for num, unit in zip(groups[0::2], groups[1::2]):
            if num:
                total += float(num.replace(",", "")) * (1e9 if unit.lower() == "billion" else 1e6)
        return total, quote
    return None

def chart(a: "pd.DataFrame", dest: Path) -> None:
    order = ["Microsoft", "Meta", "Oracle", "Amazon", "Alphabet", "CoreWeave"]
    a = a.assign(period=pd.to_datetime(a.period))
    fig, axes = plt.subplots(2, 3, figsize=(11, 6), dpi=150, sharey=True, sharex=True)
    for ax, name in zip(axes.flat, order):
        s = a[a.company == name].set_index("period").not_commenced_usd.sort_index() / 1e9
        ax.plot(s.index, s.values, color="#2a78d6", linewidth=2, marker="o", markersize=3)
        ax.annotate(f"${s.iloc[-1]:.0f}B", (s.index[-1], s.iloc[-1]), xytext=(-4, 6), textcoords="offset points",
                    ha="right", fontsize=9, color="#111111")
        ax.set_title(name, loc="left", fontsize=10, color="#111111")
        ax.grid(axis="y", color="#e6e6e6", linewidth=0.6)
        ax.tick_params(colors="#555555", labelsize=8)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    for ax in axes[:, 0]:
        ax.yaxis.set_major_formatter(lambda v, _: f"${v:.0f}B")
    axes[0, 0].xaxis.set_major_locator(mdates.YearLocator())
    axes[0, 0].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    for ax in axes.flat:
        ax.tick_params(labelbottom=True)  # sharex hides the top row's years otherwise
    fig.suptitle("Signed data center leases that haven't started yet have exploded since 2024",
                 x=0.01, ha="left", fontsize=11.5, color="#111111")
    fig.text(0.01, 0.905, "Future payments on leases signed but not yet on the balance sheet, from each 10-Q and 10-K. "
             "Total payments over terms of up to 20 years, not one year of spending.", fontsize=8.5, color="#555555")
    fig.text(0.01, 0.01, "Source: SEC filings, lease and commitment notes. Oracle gives a dollar figure from Feb 2025 on; "
             "CoreWeave reports from its 2025 IPO. Amazon's figure includes warehouses and stores.",
             fontsize=7, color="#777777")
    fig.subplots_adjust(left=0.07, right=0.98, top=0.84, bottom=0.08, hspace=0.35, wspace=0.12)
    fig.savefig(dest)


if __name__ == "__main__":
    CACHE.mkdir(parents=True, exist_ok=True)
    rows, amounts = [], []
    for name, cik in CIKS.items():
        fl = filings(cik)
        for f in fl:
            text = filing_text(name, cik, f)
            for s in sentences(text):
                rows.append({"company": name, "period": f["period"], "form": f["form"], "sentence": s})
            hit = extract(name, text) if name in RULES else None
            if hit:
                amounts.append({"company": name, "period": f["period"], "form": f["form"],
                                "not_commenced_usd": hit[0], "quote": hit[1]})
        print(f"{name}: {len(fl)} filings")
    out = pd.DataFrame(rows).drop_duplicates()
    out.to_csv(ROOT / "data/clean/lease_note_sentences.csv", index=False)
    a = pd.DataFrame(amounts)
    a.to_csv(ROOT / "data/clean/leases_not_commenced.csv", index=False)
    chart(a, ROOT / "charts/leases_not_commenced.png")
    print(a.pivot_table(index="period", columns="company", values="not_commenced_usd").div(1e9).round(1).to_string())
