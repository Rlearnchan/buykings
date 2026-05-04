# Autopark Market Data Timing Notes

Autopark separates three concepts in public dashboard metadata:

- `기준`: the market session, observation date, or benchmark window represented by the data point.
- `확인`: when Autopark fetched or verified the data for the dashboard run.
- `캡처`: when a browser screenshot was captured.

For Datawrapper chart subtitles, keep this as one public-facing line:

`{YY.MM.DD HH:MM KST}`

Source-specific basis rules:

- Yahoo Finance daily market charts: interpret candle timestamps in the exchange timezone when available, not host local time.
- US 10Y: label the representative KST basis timestamp, e.g. `26.05.01 17:05 KST`.
- WTI, Brent, DXY, and USD/KRW: label the latest Yahoo market timestamp in KST.
- CoinGecko: label daily crypto data at UTC midnight converted to KST, e.g. `26.05.04 09:00 KST`; crypto has no US-style closing bell.
- FRED: label as `최근 관측치 {date} 기준`; do not imply market close.
- FedWatch: label the captured CME screen time in KST and keep the current policy-rate range, e.g. `26.05.04 09:58 KST · 현재 기준금리 3.50-3.75%`.
- Economic calendar: label the schedule date and filter rule only, e.g. `26.05.04 KST 일정 기준, 미국 2★ 이상`.

Reference notes:

- CoinGecko market chart daily data is timestamped, daily data is at 00:00 UTC, and the latest completed UTC day is available shortly after UTC midnight.
- CME describes NYMEX energy daily settlement as using the 14:28-14:30 ET window on normal trading days.
- ICE describes Brent crude daily settlement as a weighted average during the two-minute period from 19:28 London time.
