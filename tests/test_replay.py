import json
import re
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "contracts/TideLagReplay.py"
STATION = 9414290
DAY = "2024-02-29"


@pytest.fixture
def replay(direct_deploy):
    contract = direct_deploy(str(CODE))
    return contract, sys.modules[type(contract._instance).__module__]


def synthetic():
    return [(i ** 3 + 11 * i * i) % 997 for i in range(240)]


def observations(predicted, first, second):
    return [[predicted[max(0, min(239, i + (first if i < 120 else second)))] + 201, "v"]
            for i in range(240)]


@pytest.mark.parametrize("first,second,status,lag", [
    (3, 3, "CONSISTENT_LAG", 18),
    (0, 0, "ZERO_LAG", 0),
    (-2, 3, "DIFFERENT_HALVES", None),
])
def test_centered_fit_in_each_half(replay, first, second, status, lag):
    _, mod = replay
    predictions = synthetic()
    observed = observations(predictions, first, second)
    report = mod.model(STATION, DAY, observed, predictions)
    assert report["status"] == status and report["lag_minutes"] == lag
    assert report["best_lags_by_half"] == [[first * 6], [second * 6]]


def test_ties_and_preliminary_cannot_set_lag(replay):
    _, mod = replay
    predicted = [400] * 240
    observed = [[418, "v"] for _ in range(240)]
    ambiguous = mod.model(STATION, DAY, observed, predicted)
    assert ambiguous["status"] == "AMBIGUOUS" and ambiguous["lag_minutes"] is None
    assert all(len(group) == 21 for group in ambiguous["best_lags_by_half"])
    observed[115][1] = "p"
    provisional = mod.model(STATION, DAY, observed, predicted)
    assert provisional["status"] == "PRELIMINARY_DATA" and provisional["scores"] == []


def body(values, observed=False):
    rows = []
    for i, n in enumerate(values):
        sample = {"t": f"{DAY} {i // 10:02d}:{i % 10 * 6:02d}", "v": f"{n / 1000:.3f}"}
        if observed:
            sample["q"] = "v"
        rows.append(sample)
    if observed:
        return {"metadata": {"id": str(STATION)}, "data": rows}
    return {"predictions": rows}


def test_direct_consensus_and_changed_source(replay, direct_vm):
    contract, mod = replay
    predicted = synthetic()
    observed = [n for n, _ in observations(predicted, 3, 3)]
    def install(values):
        direct_vm.clear_mocks()
        for url, sample in zip(mod.urls(STATION, DAY), (body(observed, True), body(values))):
            direct_vm.mock_web(re.escape(url) + "$", {"method": "GET", "response": {
                "status": 200, "headers": {}, "body": json.dumps(sample).encode(),
            }})
    install(predicted)
    key = contract.replay(STATION, DAY)
    result = contract.get_report(key)
    assert result["lag_minutes"] == 18
    assert direct_vm.run_validator()
    forged = {**result, "lag_minutes": -18}
    assert not direct_vm.run_validator(leader_result=mod.canonical(forged))
    install([predicted[0] + 1, *predicted[1:]])
    assert not direct_vm.run_validator()
    assert contract.get_report(key) == result


@pytest.mark.parametrize("edit", ["bad-station", "duplicate-time", "invalid-number", "quality", "gap"])
def test_invalid_evidence_rejected(replay, edit):
    _, mod = replay
    doc = body(synthetic(), True)
    rows = doc["data"]
    if edit == "bad-station":
        doc["metadata"]["id"] = "8518750"
    elif edit == "duplicate-time":
        rows[1]["t"] = rows[0]["t"]
    elif edit == "invalid-number":
        rows[2]["v"] = "0.0001"
    elif edit == "quality":
        rows[2]["q"] = "unknown"
    else:
        rows.pop()
    with pytest.raises(ValueError):
        mod.parse_series(json.dumps(doc).encode(), STATION, DAY, True)


def test_exact_public_series_when_cached(replay):
    _, mod = replay
    cached = ROOT / ".gltest_cache"
    reference = json.loads((ROOT / "REFERENCE.json").read_text(encoding="utf-8"))
    for day, expected in reference.items():
        short = day.replace("-", "")
        paths = [cached / f"{name}-{short}.json" for name in ("obs", "pred")]
        if not all(path.is_file() for path in paths):
            pytest.skip("Download the daily NOAA responses for full-fixture verification")
        obs = mod.parse_series(paths[0].read_bytes(), STATION, day, True)
        pred = mod.parse_series(paths[1].read_bytes(), STATION, day, False)
        assert mod.model(STATION, day, obs, pred) == expected
