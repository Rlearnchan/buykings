# Market Focus Brief Backlog

## v1 price_confirmation structure

`price_confirmation` is a compact string in v0. Promote it to a structured object once the renderer and quality gate need machine-readable price validation.

Target shape:

```json
{
  "needed": ["US10Y", "DXY", "WTI"],
  "confirmed": ["US10Y up", "DXY firm"],
  "missing": ["sector close confirmation"],
  "interpretation": "Rates and dollar confirm the constraint; oil is a watchpoint until WTI follows."
}
```

Acceptance notes:

- `needed`: assets or indicators required before a focus can become lead.
- `confirmed`: observed price/rate/sector reactions already present in local evidence.
- `missing`: checks that should remain in `missing_assets` or `source_gaps`.
- `interpretation`: host-readable conclusion that still treats charts as market reaction, not standalone causality.
