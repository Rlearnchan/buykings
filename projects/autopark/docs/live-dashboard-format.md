# Autopark Live Dashboard Format

This document freezes the current Notion dashboard format for Autopark daily runs.

## Page Header

- Title: `yy.mm.dd`.
- Final modified time is shown as inline code, e.g. `26.05.01 12:25 (KST)`.
- News/X collection window is shown as inline code.
- Market data 기준 is shown as inline code, e.g. `26.05.01 12:25 기준`.
- Source publication/capture times are shown as inline code, e.g. `작성 시점: 26.05.01 12:21`.

## Top Summary

- Keep the opening compact.
- Include only the day's main axis and 1-3 short summary bullets.
- Do not include a separate "오늘의 핵심 키워드" block in the final compact dashboard.

## Recommended Storylines

- Use Korean keyword-style titles for referenced materials.
- Do not keep raw English-truncated source titles in storyline references when a Korean title can explain the item.
- Slide 구성 should point to the role of each material, not ask extra follow-up questions.

## Market Section

- Section title: `시장은 지금`.
- Chart subheadings show only the instrument name, not the live value.
  - Good: `원/달러`
  - Avoid: `원/달러: 1,476.54원 +4.55원`
- Datawrapper chart images may keep values inside the image.
- Rate changes use basis points in chart titles and specs.
  - Good: `미국 10년물 국채금리: 4.400%(+4.2bp)`
  - Avoid: `미국 10년물 국채금리: 4.400%(+0.042%p)`
- Source 기준 labels are inline code.
- Screenshot sources must show actual capture time where metadata exists.

## FedWatch And Polymarket

- FedWatch and Polymarket belong in the market section.
- FedWatch should open the Probabilities tab and capture the lower target-rate probability table when possible.
- FedWatch failure must not block the whole publication.
- Polymarket should be captured only when a specific market helps explain the current issue.
- Generic `polymarket-fed-rates` is allowed only with explicit `--polymarket-policy always` or equivalent config.

## Misc Section

- Section title: `오늘의 이모저모`.
- Do not include "이 자료가 여는 질문".
- Do not include "다음에 붙일 자료".
- For image/X cards, summarize the text in Korean so the viewer can understand the image without reading the original post.
- Use Korean keyword-style titles, e.g. `구글 AI 컴퓨팅 부족`, not raw truncated source text.

## Earnings And Feature Stocks

- Earnings calendar source should show an actual capture/file time if capture metadata is unavailable.
- Finviz feature-stock screenshots should crop out lower ad sections where possible.
- A small top site banner is acceptable if removing it would lose the quote header or chart context.

## Publishing

- Default production-style run should publish to Notion only after the quality gate passes.
- For test runs, shorter scheduled one-shot runs are acceptable, but the final output should keep this format.
