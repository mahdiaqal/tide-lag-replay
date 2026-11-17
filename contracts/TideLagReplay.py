# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
import hashlib
import json
import re
from datetime import date

from genlayer import TreeMap, gl

BASE = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
DAY_SAMPLES = 240
MAX_LAG = 10
HALVES = (range(MAX_LAG, DAY_SAMPLES // 2), range(DAY_SAMPLES // 2, DAY_SAMPLES - MAX_LAG))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate response key")
        result[key] = value
    return result


def urls(station, day):
    short = day.replace("-", "")
    root = (
        f"{BASE}?begin_date={short}&end_date={short}&station={station}&datum=MLLW"
        "&units=metric&time_zone=gmt&format=json&application=TideLagReplay&product="
    )
    return root + "water_level", root + "predictions&interval=6"


def millimetres(value):
    if not isinstance(value, str):
        raise ValueError("Reading must be a fixed-point string")
    matched = re.fullmatch(r"(-?)([0-9]{1,2})(?:\.([0-9]{1,3}))?", value)
    if not matched:
        raise ValueError("Unexpected water-level precision")
    sign, whole, fraction = matched.groups()
    number = int(whole) * 1000 + int((fraction or "").ljust(3, "0"))
    return -number if sign else number


def parse_series(body, station, day, observation):
    if not isinstance(body, bytes) or not 0 < len(body) <= 65536:
        raise ValueError("Missing or oversized NOAA body")
    doc = json.loads(body, object_pairs_hook=unique_keys)
    if not isinstance(doc, dict) or "error" in doc:
        raise ValueError("NOAA series unavailable")
    if observation and doc.get("metadata", {}).get("id") != str(station):
        raise ValueError("Unexpected NOAA observation station")
    rows = doc.get("data" if observation else "predictions")
    if not isinstance(rows, list) or len(rows) != DAY_SAMPLES:
        raise ValueError("Incomplete NOAA series")
    ordered = {}
    for row in rows:
        label = row["t"]
        if label in ordered:
            raise ValueError("Duplicate NOAA sample timestamp")
        value = millimetres(row["v"])
        if observation:
            quality = row.get("q")
            if quality not in ("v", "p"):
                raise ValueError("Unknown observation quality")
            ordered[label] = [value, quality]
        else:
            ordered[label] = value
    stamps = [f"{day} {i // 10:02d}:{(i % 10) * 6:02d}" for i in range(DAY_SAMPLES)]
    if set(ordered) != set(stamps):
        raise ValueError("NOAA timestamps do not cover the requested grid")
    return [ordered[t] for t in stamps]


def centered_error(observed, predicted, indexes, lag):
    residuals = [observed[i] - predicted[i + lag] for i in indexes]
    return len(residuals) * sum(x * x for x in residuals) - sum(residuals) ** 2


def model(station, day, observations, predictions):
    observed = [n for n, _ in observations]
    verified = sum(q == "v" for _, q in observations)
    report = {
        "schema": "tide-lag/1", "station": station, "utc_day": day,
        "sources": list(urls(station, day)), "datum": "MLLW",
        "observed_sha256": digest(observations), "predicted_sha256": digest(predictions),
        "verified_samples": verified,
    }
    if verified != DAY_SAMPLES:
        return {**report, "status": "PRELIMINARY_DATA", "lag_minutes": None,
                "scores": [], "best_lags_by_half": []}

    scores = [
        [lag * 6, *[centered_error(observed, predictions, group, lag) for group in HALVES]]
        for lag in range(-MAX_LAG, MAX_LAG + 1)
    ]
    best = []
    for index in (1, 2):
        minimum = min(row[index] for row in scores)
        best.append([row[0] for row in scores if row[index] == minimum])
    lag = None
    if any(len(group) > 1 for group in best):
        status = "AMBIGUOUS"
    elif best[0] != best[1]:
        status = "DIFFERENT_HALVES"
    else:
        lag = best[0][0]
        status = "CONSISTENT_LAG" if lag else "ZERO_LAG"
    return {**report, "status": status, "lag_minutes": lag,
            "scores": scores, "best_lags_by_half": best}


class TideLagReplay(gl.Contract):
    reports: TreeMap[str, str]

    def __init__(self):
        pass

    @gl.public.write
    def replay(self, station: int, utc_day: str) -> str:
        if type(station) is not int or not 1_000_000 <= station <= 9_999_999:
            raise gl.vm.UserError("Expected a seven-digit NOAA station")
        if not isinstance(utc_day, str) or not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}", utc_day):
            raise gl.vm.UserError("Expected a day in YYYY-MM-DD format")
        try:
            date.fromisoformat(utc_day)
        except ValueError:
            raise gl.vm.UserError("Invalid calendar day")

        def evaluate():
            try:
                observations, predictions = urls(station, utc_day)
                observed = gl.nondet.web.get(observations)
                predicted = gl.nondet.web.get(predictions)
                if observed.status == predicted.status == 200:
                    samples = parse_series(observed.body, station, utc_day, True)
                    forecast = parse_series(predicted.body, station, utc_day, False)
                    return canonical(model(station, utc_day, samples, forecast))
            except Exception:
                raise gl.vm.UserError("NOAA evidence unavailable or invalid")
            raise gl.vm.UserError("NOAA returned an unsuccessful response")

        def validate(leader):
            if not isinstance(leader, gl.vm.Return):
                return False
            try:
                return evaluate() == leader.calldata
            except Exception:
                return False

        agreed = gl.vm.run_nondet_unsafe(evaluate, validate)
        key = hashlib.sha256(agreed.encode("ascii")).hexdigest()
        if key not in self.reports:
            self.reports[key] = agreed
        return key

    @gl.public.view
    def get_report(self, report_id: str) -> dict:
        if report_id not in self.reports:
            raise gl.vm.UserError("Unknown replay report")
        return json.loads(self.reports[report_id])
