# Autopark Manual Broadcast Retrospective

Broadcast retrospective is intentionally not part of the daily Autopark automation.
Run it only when the actual broadcast materials are ready.

## Inputs

Required:
- `AUTOPARK_RETRO_DATE`: dashboard date, for example `2026-05-05`

Recommended:
- `AUTOPARK_RETRO_PPT`: path inside the container to the final broadcast PPT/PPTX
- `AUTOPARK_RETRO_VIDEO_URL` or `AUTOPARK_RETRO_VIDEO_ID`: Wepoll/YouTube live URL or video id

Optional:
- `AUTOPARK_RETRO_LOCAL_TRANSCRIPT`: path inside the container to a local transcript file

If no local transcript is supplied, the runner uses the existing transcript fetch code to collect the script/title/video metadata.

## Docker Run

Copy or place the PPT/transcript under a mounted Autopark directory such as:

```text
projects/autopark/runtime/broadcast/2026-05-05/
```

Then run:

```powershell
$env:AUTOPARK_RETRO_DATE = "2026-05-05"
$env:AUTOPARK_RETRO_PPT = "/app/projects/autopark/runtime/broadcast/2026-05-05/final.pptx"
$env:AUTOPARK_RETRO_VIDEO_URL = "https://www.youtube.com/watch?v=..."
docker compose -f docker-compose.autopark.yml --profile manual run --rm autopark-retrospective
```

With a local transcript:

```powershell
$env:AUTOPARK_RETRO_DATE = "2026-05-05"
$env:AUTOPARK_RETRO_PPT = "/app/projects/autopark/runtime/broadcast/2026-05-05/final.pptx"
$env:AUTOPARK_RETRO_LOCAL_TRANSCRIPT = "/app/projects/autopark/runtime/broadcast/2026-05-05/transcript.txt"
docker compose -f docker-compose.autopark.yml --profile manual run --rm autopark-retrospective
```

## Outputs

- `projects/autopark/runtime/logs/{date}-broadcast-retrospective.json`
- `projects/autopark/runtime/reviews/{date}/broadcast-retrospective.json`
- `projects/autopark/runtime/reviews/{date}/broadcast-retrospective.md`
- `projects/autopark/runtime/broadcast/{date}/retrospective-feedback.md`

## Design Notes

- Daily publishing does not wait for retrospective.
- Retrospective learning is preference and scoring guidance, not market evidence.
- Scoring changes should be reviewed before they are applied to source policy or radar weights.
