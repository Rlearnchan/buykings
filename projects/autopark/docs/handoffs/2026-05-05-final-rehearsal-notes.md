# Autopark 0505 Final Rehearsal Notes

## Editorial Retry Caveat

The 2026-05-05 editorial brief can be `fallback=false` even when the first full
editorial request times out and the compact retry produces the accepted
storylines. This is not deterministic fallback, but it can make storylines feel
more repetitive because the retry packet is intentionally much smaller.

For the next quality pass, improve the normal editorial prompt/runtime path
before changing the public dashboard format. Keep logging first-attempt and retry
prompt size, token estimate, candidate count, timeout/fallback code, and elapsed
time in the post-publish review and sourcebook.

## Deferred Improvements

- Rework editorial input reduction so the first attempt succeeds more often without collapsing to a low-context retry.
- Improve media focus title variety further if LLM credits are available; the renderer now prefers evidence microcopy titles, but deterministic fallback can still be generic.
- Rebuild the earnings / feature-stock section after the ticker drilldown and Finviz feature-stock flow is reliable enough for public display.
