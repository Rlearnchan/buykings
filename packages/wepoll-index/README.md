# wepoll-index

Portable CLI for computing one Wepoll index row without Datawrapper or Notion.

## Install

```powershell
py -3 -m pip install ./packages/wepoll-index
```

The v1 package preserves the current Buykings formula. It therefore needs:

- a Wepoll posts CSV with `작성시각`, `제목`, `본문`, and engagement columns
- KOSPI, KOSDAQ, and VKOSPI market CSVs in the existing Investing.com export shape
- a state directory containing the published baseline CSVs
- access to the current `wepoll-panic` compute source via `WEPOLL_PANIC_ROOT`

If the command is run outside the Buykings repo, set `BUYKINGS_ROOT` so it can find the compatibility scripts.

## Compute

```powershell
wepoll-index compute `
  --posts posts.csv `
  --kospi kospi.csv `
  --kosdaq kosdaq.csv `
  --vkospi vkospi.csv `
  --state state `
  --date 2026-05-01 `
  --output result.json
```

Output:

```json
{
  "date": "2026-05-01",
  "state_label_ko": "중립",
  "psychology_index_0_100": 50.0,
  "participation_index_0_100": 50.0,
  "post_count": 0
}
```
