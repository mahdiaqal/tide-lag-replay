# StudioNet proof matrix

[StudioNet contract](https://explorer-studio.genlayer.com/address/0x771CC54c8Cbf58EDFDD64Fa406d9774aA47a041c) · [Deployed source](https://github.com/mahdiaqal/tide-lag-replay/blob/540eeca352e8231a946e7565980cd4dffd585d32/contracts/TideLagReplay.py) · [Receipts and full reports](PROOFS.json)

Deployed source SHA-256 `1f74df6a01008ae9c0713f6499d28a3454101edbd250d7a48449886b54a97640`.
All receipts finalized with successful execution and majority agreement.
The proof runner fetched each report by its returned ID and compared every
field with the independent [pairwise residual reference](REFERENCE.json).

| Transaction | Result | Verified observations | Best lags by half, minutes | Agree votes / initial validators |
| --- | --- | --- | --- | --- |
| [deploy](https://explorer-studio.genlayer.com/tx/0x59ee84017116c3f3cdb8d264f231b85cb4afca846685cd6515d0f857cf5853f5) | Source matched | — | — | 4 / 5 |
| [2023-01-15](https://explorer-studio.genlayer.com/tx/0x09df4e068af9ae76aef05d8b2c17ecf7d84891843d6d7e05135ad64ca7c4df29) | `DIFFERENT_HALVES` | 240 | [[-18],[0]] | 3 / 5 |
| [2025-01-15](https://explorer-studio.genlayer.com/tx/0xf47c09fb35ab649beb33a03d73c6c37e8bafc992379c68f679330f100b756305) | `CONSISTENT_LAG` | 240 | [[-6],[-6]] | 3 / 5 |
| [2024-01-15](https://explorer-studio.genlayer.com/tx/0x89f6ce4dcc03afd5cb027fcde42527492aa35920742b5a4f0eee184a31b35639) | `PRELIMINARY_DATA` | 0 | — | 3 / 5 |

An unknown report read reverted. Local tests also cover tied minima, a
forged leader result, wrong station metadata and missing or duplicated timestamps.
