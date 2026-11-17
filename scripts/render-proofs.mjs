import fs from 'node:fs';
import assert from 'node:assert/strict';

const proof = JSON.parse(fs.readFileSync('PROOFS.json', 'utf8'));
const github = 'https://github.com/mahdiaqal/tide-lag-replay';
const explorer = 'https://explorer-studio.genlayer.com';
assert(proof.verified && proof.source.source_match && proof.unknown_report_reverted);
assert.equal(proof.transactions.length, 4);
assert.equal(Object.keys(proof.replays).length, 3);
assert(proof.transactions.every(({receipt}) => receipt.committed && receipt.status === 'FINALIZED' &&
  receipt.execution === 'SUCCESS' && receipt.consensus === 'MAJORITY_AGREE' &&
  receipt.leader_only === false && receipt.agree_votes >= 2));

const deployment = `[StudioNet contract](${explorer}/address/${proof.address})`;
const source = `[Deployed source](${github}/blob/${proof.source_commit}/contracts/TideLagReplay.py)`;
const tx = t => `[${t.step}](${explorer}/tx/${t.hash})`;
const rows = proof.transactions.map(t => {
  const report = proof.replays[t.step]?.report;
  const fit = report?.best_lags_by_half.length ? JSON.stringify(report.best_lags_by_half) : '—';
  const outcome = report ? `\`${report.status}\`` : 'Source matched';
  return `| ${tx(t)} | ${outcome} | ${report?.verified_samples ?? '—'} | ${fit} | ${t.receipt.agree_votes} / ${t.receipt.initial_validators} |`;
});

fs.writeFileSync('LIVE_PROOFS.md', `# StudioNet proof matrix

${deployment} · ${source} · [Receipts and full reports](PROOFS.json)

Deployed source SHA-256 \`${proof.source.sha256}\`.
All receipts finalized with successful execution and majority agreement.
The proof runner fetched each report by its returned ID and compared every
field with the independent [pairwise residual reference](REFERENCE.json).

| Transaction | Result | Verified observations | Best lags by half, minutes | Agree votes / initial validators |
| --- | --- | --- | --- | --- |
${rows.join('\n')}

An unknown report read reverted. Local tests also cover tied minima, a
forged leader result, wrong station metadata and missing or duplicated timestamps.
`);

const notes = `TideLagReplay compares NOAA water-level observations with tide predictions at six-minute intervals. The leader and validators independently fetch both products, require the exact UTC grid, normalize values to integer millimetres, and check observation quality. They compare 21 candidate lags in two halves using exact centered residual scores. A lag is reported only when both halves have the same unique best shift. Preliminary observations suppress fitting. Consensus requires exact agreement on both input digests, all scores and the decision.

Three finalized StudioNet replays verified a shared minus-six-minute fit, disagreement between the halves, and preliminary data with no fit. The result describes a bounded fit to the archived series.`;
assert(notes.length <= 1000);
const published = process.argv.includes('--public-proof-link');
fs.writeFileSync('SUBMISSION.md', `**Contribution type** Builder → Intelligent Contracts

**Title** TideLagReplay — Consensus Verification of Tide Alignment

**Notes / Description**

${notes}

**Evidence**

- [Repository](${github})
- ${source}
- ${deployment}
${published ? `- [Live proof matrix](${github}/blob/main/LIVE_PROOFS.md)\n` : ''}${proof.transactions.map(t => '- ' + tx(t)).join('\n')}
`);
