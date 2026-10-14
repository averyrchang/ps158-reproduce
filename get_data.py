"""Download Stanford/ADP Canaries dashboard aggregates for Nov 2022–Jun 2026.

Default archived July release contains June observations (vintage 2026-07-16).
Dashboard sample differs from the August 2026 paper. No private microdata.
Requires pandas and curl. --release latest downloads the latest revised vintage,
but retains the requested observation window. --refresh replaces cached archives.
"""
import argparse
import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
BASE = "https://storage.googleapis.com/aviary-del-public/release_memos"
START, END = "2022-11-01", "2026-06-01"
AGES = ["Early Career 1 (22-25)", "Senior (50+)"]
PRODUCTS = ["canaries_age_by_exposure", "canaries_anthropic_usage_patterns_by_age", "canaries_by_age"]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--release", default="2026-07", choices=["2026-07", "latest"])
    p.add_argument("--refresh", action="store_true")
    args = p.parse_args()
    raw = ROOT / "data" / "raw" / "canaries" / args.release
    raw.mkdir(parents=True, exist_ok=True)
    sources, frames = [], []
    for product in PRODUCTS:
        url = f"{BASE}/{args.release}/downloads/{product}_results.zip"
        archive = raw / f"{product}_results.zip"
        if args.refresh or not archive.exists():
            temporary = archive.with_suffix(".part")
            subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error",
                            "--retry", "3", "--max-time", "120", url,
                            "--output", str(temporary)], check=True)
            with zipfile.ZipFile(temporary) as z:
                if z.testzip() is not None:
                    raise ValueError("Corrupt archive")
            temporary.replace(archive)
        with zipfile.ZipFile(archive) as z:
            df = pd.read_csv(z.open(product + ".csv"))
            dictionary = product + "_data_dictionary.md"
            (raw / dictionary).write_bytes(z.read(dictionary))
        source_min, source_max = df.observation_date.min(), df.observation_date.max()
        if source_min > START or source_max < END:
            raise ValueError("Source does not cover requested window")
        if product == PRODUCTS[0]:
            df = df.melt(id_vars=["observation_date", "exposure_quintile", "vintage"],
                         value_vars=AGES, var_name="age_group", value_name="employment_index")
            df = df.rename(columns={"exposure_quintile": "quintile"})
            df["measure"] = "AI exposure"
        elif product == "canaries_by_age":
            df = df.melt(id_vars=["observation_date", "vintage"], value_vars=AGES,
                         var_name="age_group", value_name="employment_index")
            df["quintile"] = "Quintile 0"
            df["measure"] = "Overall"
        else:
            df = df[(df.usage_pattern == "Automation") & df.age_bucket.isin(AGES)]
            df = df.melt(id_vars=["observation_date", "age_bucket", "vintage"],
                         value_vars=[c for c in df if c.startswith("Quintile")],
                         var_name="quintile", value_name="employment_index")
            df = df.rename(columns={"age_bucket": "age_group"})
            df["measure"] = "Automation ratio"
        df["quintile"] = df.quintile.str.extract(r"Quintile (\d)").astype(int)
        df = df[df.observation_date.between(START, END)].copy()
        keys = ["observation_date", "measure", "age_group", "quintile"]
        if df.duplicated(keys).any() or df.employment_index.isna().any():
            raise ValueError("Duplicate or missing observations")
        months = pd.date_range(START, END, freq="MS").strftime("%Y-%m-%d").tolist()
        for _, group in df.groupby(["measure", "age_group", "quintile"]):
            if sorted(group.observation_date) != months:
                raise ValueError("Non-contiguous series")
        expected_quintiles = 1 if product == "canaries_by_age" else 5
        if len(df) != len(months) * 2 * expected_quintiles:
            raise ValueError("Unexpected series count")
        if not (df[df.observation_date == START].employment_index.sub(100).abs() < 1e-6).all():
            raise ValueError("Expected November 2022 = 100")
        df["change_percent"] = df.employment_index - 100
        frames.append(df)
        sources.append(dict(url=url, sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                            source_start=source_min, source_end=source_max,
                            vintage=sorted(df.vintage.unique().tolist()), rows=len(df)))
        print(f"{product}: {source_min} to {source_max}; selected {len(df)} rows")
    output = pd.concat(frames, ignore_index=True).sort_values(
        ["measure", "age_group", "quintile", "observation_date"])
    output.to_csv(ROOT / "data" / "canaries.csv", index=False)
    (ROOT / "data" / "canaries_manifest.json").write_text(json.dumps(dict(
        retrieved_utc=datetime.now(timezone.utc).isoformat(), release=args.release,
        observation_start=START, observation_end=END, sources=sources,
        paper="https://digitaleconomy.stanford.edu/app/uploads/2026/08/Canaries_August2026.pdf",
        dashboard="https://digitaleconomy.stanford.edu/project/indicators/canaries-dashboard/",
        notes="Public dashboard indices; balanced ADP firms, occupation-matched workers. "
              "Not nationally representative employment rates or causal replacement estimates. "
              "Dashboard rolling sample differs from paper sample. "
              "AI exposure and automation ratio are distinct occupational measures."
    ), indent=2) + "\n")


if __name__ == "__main__":
    main()
