# Wepoll Index Migration Package

This note defines the handoff shape for Wepoll developers who want to run the index computation on their own server.

## Deliverable

The migration bundle should contain `packages/wepoll-index`, the compatibility scripts under `scripts/` that it calls, and the current `wepoll-panic/src/wepoll_fear_index` compute source. Visualization, Datawrapper publishing, Notion publishing, and Codex automation are intentionally excluded.

## Runtime Contract

The server provides:

- Wepoll posts CSV for the target date or a wider range
- KOSPI, KOSDAQ, and VKOSPI daily market CSVs covering the target date
- Baseline state CSVs copied from `projects/wepoll-panic/state`
- `OPENAI_API_KEY` when the second-pass classifier runs with the OpenAI backend

The command is:

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

The output JSON contains only `date`, `state_label_ko`, `psychology_index_0_100`, `participation_index_0_100`, and `post_count`.

## Formula Compatibility

The first migration target is compatibility with the current Buykings published formula. Because the current participation index blends Wepoll activity with market turnover and volatility context, the minimal package still requires KOSPI, KOSDAQ, and VKOSPI inputs. A future Wepoll-only formula should be versioned separately because it will not reproduce existing published values.
