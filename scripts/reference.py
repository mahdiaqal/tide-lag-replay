"""Calculate proof scores independently using pairwise residual differences."""
import hashlib
import json
from decimal import Decimal
from itertools import combinations
from pathlib import Path


ROOT = Path(".gltest_cache")
STATION = 9414290


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode("ascii")).hexdigest()


def mm(row):
    exact = Decimal(row["v"]) * 1000
    assert exact == int(exact)
    return int(exact)


def case(short):
    day = f"{short[:4]}-{short[4:6]}-{short[6:]}"
    first = json.loads((ROOT / f"obs-{short}.json").read_text())["data"]
    second = json.loads((ROOT / f"pred-{short}.json").read_text())["predictions"]
    o = sorted(first, key=lambda r: r["t"])
    p = sorted(second, key=lambda r: r["t"])
    assert len(o) == len(p) == 240
    assert [row["t"] for row in o] == [row["t"] for row in p]
    verified = sum(row["q"] == "v" for row in o)
    assert all(row["q"] in ("p", "v") for row in o)
    observed = [mm(row) for row in o]
    predicted = [mm(row) for row in p]
    root = ("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
            f"?begin_date={short}&end_date={short}&station={STATION}&datum=MLLW"
            "&units=metric&time_zone=gmt&format=json&application=TideLagReplay&product=")
    base = {"schema": "tide-lag/1", "station": STATION, "utc_day": day,
            "datum": "MLLW", "sources": [root + "water_level", root + "predictions&interval=6"],
            "observed_sha256": digest([[n, r["q"]] for n, r in zip(observed, o)]),
            "predicted_sha256": digest(predicted), "verified_samples": verified}
    if verified < 240:
        return {**base, "status": "PRELIMINARY_DATA", "lag_minutes": None,
                "scores": [], "best_lags_by_half": []}

    def score(lag, sample):
        residuals = [observed[i] - predicted[i + lag] for i in sample]
        return sum((a - b) ** 2 for a, b in combinations(residuals, 2))

    curves = [[lag * 6, score(lag, range(10, 120)), score(lag, range(120, 230))]
              for lag in range(-10, 11)]
    best = [[row[0] for row in curves if row[column] == min(r[column] for r in curves)]
            for column in (1, 2)]
    lag = None
    if max(map(len, best)) > 1:
        status = "AMBIGUOUS"
    elif best[0] != best[1]:
        status = "DIFFERENT_HALVES"
    else:
        lag = best[0][0]
        status = "ZERO_LAG" if lag == 0 else "CONSISTENT_LAG"
    return {**base, "status": status, "lag_minutes": lag, "scores": curves, "best_lags_by_half": best}


cases = [case(short) for short in ("20230115", "20250115", "20240912", "20240115")]
for item in cases:
    print(item["utc_day"], item["status"], item["best_lags_by_half"])
selected = {}
for item in cases:
    selected.setdefault(item["status"], item)
assert len(selected) >= 2
out = {item["utc_day"]: item for item in selected.values()}
Path("REFERENCE.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
