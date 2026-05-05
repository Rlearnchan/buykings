# 2026-05-05 LLM Call Stability Experiment

Status: first pass executed at `2026-05-05 08:44-08:57 KST`

## Purpose

This experiment isolates Autopark LLM call reliability from writing quality. It uses the fixed sanitized 2026-05-05 packet and writes only to experiment paths, not production processed files or Notion.

## Synchronous Tests

| Step | Model | Input | Timeout | Output Path | Elapsed | Response ID | Result |
|---|---|---:|---:|---|---:|---|---|
| Evidence g30 | gpt-5-mini | 30 items | none | `data/processed/2026-05-05/experiments/evidence-g30.json` | 81.656s | `resp_00d5ee9a12e4d3cb0069f92f4c3c3c81949ef0430dda2a05b1` | success, 30 valid |
| Evidence g20 | gpt-5-mini | 30 items | none | `data/processed/2026-05-05/experiments/evidence-g20.json` | 88.688s | `resp_0cd82bf24099b7120069f92fa889288190bdf919ddc4b56f97`, `resp_05d7fdec369ad8f10069f92fe97868819385d1227a6d320897` | success, 30 valid |
| Evidence g10 | gpt-5-mini | 30 items | none | `data/processed/2026-05-05/experiments/evidence-g10.json` | 82.312s | `resp_0df34f40b5ea16a20069f92fa86a8881939f7f43bf986749c4`, `resp_059c55284dbf17620069f92fcef974819588200c13a70a4f71` | partial: group 3 failed with 502 |
| Pre-flight web | gpt-5-mini | 0505 preflight packet | none | `data/processed/2026-05-05/experiments/preflight.json` | 68.984s | `resp_0915ec7f77c3fe0d0069f93012e4148194baa401f770a182a8` | success, 8 agenda items |
| Market Focus | gpt-5-mini | 0505 focus packet | none | `data/processed/2026-05-05/experiments/market-focus.json` | 40.218s | `resp_03beffccb3afbe130069f930605be4819694f85f5524214ba6` | success, 4 focus items |
| Editorial c8 | gpt-5-mini | 12 candidates sent | none | `data/processed/2026-05-05/experiments/editorial-c8.json` | 123.719s | `resp_01e1ca1e23fee45c0069f93091edac8190845dcbeb6069e73b` | success, no retry |
| Editorial c12 | gpt-5-mini | 12 candidates sent | none | `data/processed/2026-05-05/experiments/editorial-c12.json` | 141.766s | `resp_0a6ca8d15aeab8900069f9313a25e48193a5d73d33d5d6f729` | success, no retry |
| Editorial c16 | gpt-5-mini | 16 candidates sent | none | `data/processed/2026-05-05/experiments/editorial-c16.json` | 121.906s | `resp_0771f3c997c9f38a0069f931d1b7dc8197968ba4f19125b338` | success, no retry |

Note: Evidence g10 and g20 were launched concurrently, so wall-clock comparison is noisy. Success/failure behavior is still useful: g10 had more request surface and one 502 Bad Gateway, while g20 completed both requests.

## Token / Usage Snapshot

| Step | Input Tokens | Output Tokens | Reasoning Tokens | Total Tokens |
|---|---:|---:|---:|---:|
| Evidence g30 | 8,759 | 6,940 | 4,160 | 15,699 |
| Evidence g20 | 9,219 | 8,355 | 5,376 | 17,574 |
| Evidence g10 | 6,729 | 6,319 | 4,160 | 13,048 partial |
| Pre-flight web | 5,499 | 6,571 | 2,048 | 12,070 |
| Market Focus | 48,607 | 5,175 | 1,408 | 53,782 |

## Batch Test

| Batch ID | Model | Requests | Completion Window | Submitted | Completed | Request Counts | Output File | Notes |
|---|---|---:|---|---|---|---|---|---|
| `batch_69f93254fab881909026b98f2e8de95e` | gpt-5-mini | 1 | 24h | `2026-05-05 08:57 KST` | pending | in_progress: 1/0/0 | pending | 08:57 validating, 08:58 in_progress |

## Commands

```powershell
$env:AUTOPARK_EVIDENCE_MICROCOPY_ENABLED='1'
$env:AUTOPARK_EVIDENCE_MICROCOPY_MODEL='gpt-5-mini'

python projects/autopark/scripts/build_evidence_microcopy.py --date 2026-05-05 --group-size 30 --llm-limit 30 --max-elapsed 0 --no-api-timeout --output projects/autopark/data/processed/2026-05-05/experiments/evidence-g30.json
python projects/autopark/scripts/build_evidence_microcopy.py --date 2026-05-05 --group-size 10 --llm-limit 30 --max-elapsed 0 --no-api-timeout --output projects/autopark/data/processed/2026-05-05/experiments/evidence-g10.json
python projects/autopark/scripts/build_evidence_microcopy.py --date 2026-05-05 --group-size 20 --llm-limit 30 --max-elapsed 0 --no-api-timeout --output projects/autopark/data/processed/2026-05-05/experiments/evidence-g20.json

python projects/autopark/scripts/build_market_preflight_agenda.py --date 2026-05-05 --with-web --no-api-timeout --output projects/autopark/data/processed/2026-05-05/experiments/preflight.json --markdown-output projects/autopark/data/processed/2026-05-05/experiments/preflight.md --prompt-output projects/autopark/data/processed/2026-05-05/experiments/preflight-prompt.json
python projects/autopark/scripts/build_market_focus_brief.py --date 2026-05-05 --no-api-timeout --output projects/autopark/data/processed/2026-05-05/experiments/market-focus.json --markdown-output projects/autopark/data/processed/2026-05-05/experiments/market-focus.md --prompt-output projects/autopark/data/processed/2026-05-05/experiments/market-focus-prompt.json
python projects/autopark/scripts/build_editorial_brief.py --date 2026-05-05 --max-candidates 8 --no-api-timeout --output projects/autopark/data/processed/2026-05-05/experiments/editorial-c8.json --prompt-output projects/autopark/data/processed/2026-05-05/experiments/editorial-c8-prompt.json
python projects/autopark/scripts/build_editorial_brief.py --date 2026-05-05 --max-candidates 12 --no-api-timeout --output projects/autopark/data/processed/2026-05-05/experiments/editorial-c12.json --prompt-output projects/autopark/data/processed/2026-05-05/experiments/editorial-c12-prompt.json
python projects/autopark/scripts/build_editorial_brief.py --date 2026-05-05 --max-candidates 16 --no-api-timeout --output projects/autopark/data/processed/2026-05-05/experiments/editorial-c16.json --prompt-output projects/autopark/data/processed/2026-05-05/experiments/editorial-c16-prompt.json
```

```powershell
python projects/autopark/scripts/run_evidence_microcopy_batch_experiment.py --date 2026-05-05 --group-size 30 --llm-limit 30
python projects/autopark/scripts/run_evidence_microcopy_batch_experiment.py --date 2026-05-05 --group-size 30 --llm-limit 60 --submit
```

## Notes To Fill After Execution

- Evidence: `group_size=30` worked in 81.6s. `group_size=20` also worked. `group_size=10` had a transient 502 on the third request, suggesting smaller groups increase failure surface unless retry is added.
- Pre-flight: no-timeout web call returned in 69.0s, so the previous failure is consistent with client timeout / response timing rather than model inability.
- Market Focus: no-timeout returned in 40.2s despite a 185K-char prompt, so this stage is not the main bottleneck when the response is received cleanly.
- Editorial: c16 full first attempt succeeded in 121.9s. The previous 120s timeout was too tight; a production timeout around 210-240s is more realistic.
- Batch: submitted successfully; still validating on immediate retrieve. It should remain a non-critical enrichment option unless observed completion time is consistently within the morning window.

## First-Pass Conclusion

- The mini model is producing usable outputs; the main issue is client timeout and transient OpenAI/API gateway failure handling.
- For synchronous morning publishing, prefer fewer grouped Evidence requests (`group_size=20-30`) plus per-group retry for 502/503/504.
- Raise Pre-flight and Editorial read timeouts above the observed no-timeout elapsed times. Suggested starting point: Pre-flight 150s, Evidence per group 150s, Market Focus 180s, Editorial 240s.
- Keep Batch API out of the 05:00 critical path. It is appropriate for late-night/retrospective enrichment or cost comparison.
