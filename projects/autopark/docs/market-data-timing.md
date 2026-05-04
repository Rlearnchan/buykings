# Autopark Market Data Timing Notes

Autopark separates three concepts in public dashboard metadata:

- `기준`: the market session, observation date, or benchmark window represented by the data point.
- `확인`: when Autopark fetched or verified the data for the dashboard run.
- `캡처`: when a browser screenshot was captured.

For Datawrapper chart subtitles, keep this as one public-facing line:

`{basis_label} · 확인 {YY.MM.DD HH:MM KST}`

Source-specific basis rules:

- Yahoo Finance daily market charts: interpret candle timestamps in the exchange timezone when available, not host local time.
- WTI: label as `WTI 일봉 {date} 기준(정산 구간 14:28-14:30 ET)`.
- Brent: label as `Brent 일봉 {date} 기준(정산 구간 19:28-19:30 London)`.
- CoinGecko: label daily crypto data as `UTC 일봉 {date} 00:00 기준`; crypto has no US-style closing bell.
- FRED: label as `최근 관측치 {date} 기준`; do not imply market close.
- USD/KRW: label as `Yahoo FX 일봉 {date} 기준`; do not call it a US close.

Reference notes:

- CoinGecko market chart daily data is timestamped, daily data is at 00:00 UTC, and the latest completed UTC day is available shortly after UTC midnight.
- CME describes NYMEX energy daily settlement as using the 14:28-14:30 ET window on normal trading days.
- ICE describes Brent crude daily settlement as a weighted average during the two-minute period from 19:28 London time.

