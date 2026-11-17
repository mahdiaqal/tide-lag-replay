# TideLagReplay

TideLagReplay checks whether NOAA's measured water levels and predicted
tides have the same best-fitting time shift in two halves of a UTC day.
It records complete comparable score curves and withholds a single lag
when the halves disagree, optima tie, or any observation is preliminary.

Anyone can call `replay(station, utc_day)`. The leader and validators fetch
the six-minute water level and prediction products, both in metres on NOAA's
MLLW datum and GMT timestamps. They require the requested station in the
measurement metadata and all 240 unique timestamps in each series.
Each normalizes the published decimal values to integer millimetres and
checks the observation quality flags. They require exact agreement on the
normalized input digests, quality count, scores, and decision.
`get_report(report_id)` reads the agreed immutable report.

For each candidate shift from −60 to +60 minutes in six-minute steps, the
contract pairs the same 110 observed timestamps per half with shifted
prediction samples. A positive shift uses prediction values from later
timestamps. It compares residuals after removing a constant vertical
offset independently in each half. The exact integer score is
`n × sum(residual²) − sum(residual)²`. The day edges are excluded from the
comparison so all shifts use the same measured timestamps.

| Status | Meaning |
| --- | --- |
| `CONSISTENT_LAG` | Both halves have the same unique best nonzero shift within the model range. |
| `ZERO_LAG` | Both halves uniquely favour zero shift. |
| `DIFFERENT_HALVES` | The halves have different unique optima. |
| `AMBIGUOUS` | At least one half has tied optima. |
| `PRELIMINARY_DATA` | NOAA marks at least one observation preliminary. The report omits the scores and lag. |

The lag is a descriptive fit to the archived products over a bounded
search range. NOAA is the source for both series. The comparison uses
centred residuals and does not assign a cause to any fitted difference.
[NOAA CO-OPS Data API](https://api.tidesandcurrents.noaa.gov/api/prod/) ·
[Observation flags](https://api.tidesandcurrents.noaa.gov/api/prod/responseHelp.html)

```sh
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
genvm-lint check contracts/TideLagReplay.py
```

`REFERENCE.json` records the independent calculations for the proof days.
`scripts/reference.py` derives the scores by summing pairwise residual
differences over the downloaded daily data in `.gltest_cache`. The StudioNet
proof runner compares every field to those vectors. Use the pinned JS SDK
with `npm ci` and its `--verify-only` flag to recheck existing receipts.
