**Contribution type** Builder → Intelligent Contracts

**Title** TideLagReplay — Consensus Verification of Tide Alignment

**Notes / Description**

TideLagReplay compares NOAA water-level observations with tide predictions at six-minute intervals. The leader and validators independently fetch both products, require the exact UTC grid, normalize values to integer millimetres, and check observation quality. They compare 21 candidate lags in two halves using exact centered residual scores. A lag is reported only when both halves have the same unique best shift. Preliminary observations suppress fitting. Consensus requires exact agreement on both input digests, all scores and the decision.

Three finalized StudioNet replays verified a shared minus-six-minute fit, disagreement between the halves, and preliminary data with no fit. The result describes a bounded fit to the archived series.

**Evidence**

- [Repository](https://github.com/mahdiaqal/tide-lag-replay)
- [Deployed source](https://github.com/mahdiaqal/tide-lag-replay/blob/540eeca352e8231a946e7565980cd4dffd585d32/contracts/TideLagReplay.py)
- [StudioNet contract](https://explorer-studio.genlayer.com/address/0x771CC54c8Cbf58EDFDD64Fa406d9774aA47a041c)
- [Live proof matrix](https://github.com/mahdiaqal/tide-lag-replay/blob/main/LIVE_PROOFS.md)
- [deploy](https://explorer-studio.genlayer.com/tx/0x59ee84017116c3f3cdb8d264f231b85cb4afca846685cd6515d0f857cf5853f5)
- [2023-01-15](https://explorer-studio.genlayer.com/tx/0x09df4e068af9ae76aef05d8b2c17ecf7d84891843d6d7e05135ad64ca7c4df29)
- [2025-01-15](https://explorer-studio.genlayer.com/tx/0xf47c09fb35ab649beb33a03d73c6c37e8bafc992379c68f679330f100b756305)
- [2024-01-15](https://explorer-studio.genlayer.com/tx/0x89f6ce4dcc03afd5cb027fcde42527492aa35920742b5a4f0eee184a31b35639)
