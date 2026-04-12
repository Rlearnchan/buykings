# Semantic And Fightin Tables

기준일: 2026-04-12

## W2V

### candidate dots

- 검토용 CSV:
  - `projects/wepoll-samsung/prepared/dw_member_word2vec_candidate_dots.csv`
- 1차 선택본:
  - `projects/wepoll-samsung/prepared/dw_member_word2vec_selected_dots.csv`
  - 기간별 scatter 입력:
    - `projects/wepoll-samsung/prepared/dw_member_word2vec_selected_dots_2025.csv`
    - `projects/wepoll-samsung/prepared/dw_member_word2vec_selected_dots_2026.csv`
    - `projects/wepoll-samsung/prepared/dw_member_word2vec_selected_dots_eventweek.csv`
- 구성:
  - `period`
  - `rank`
  - `label`
  - `kind`
  - `candidate_group`
  - `recommended_keep`
  - `x`
  - `y`
- 운영 메모:
  - `recommended_keep=yes`는 anchor와 각 멤버 주변 similar 5개를 우선 표시 후보로 잡은 것이다.
  - 나머지 `top_token`은 최종 SVG 또는 scatter plot에서 일부만 선택적으로 남긴다.
  - 현재 후보 중 `오동석`처럼 별도 검토가 필요한 outlier도 포함되어 있으니, 최종판 전엔 수작업 선택이 필요하다.
  - `selected_dots`는 방송/PPT 기준으로 단어 수를 넓힌 shortlist다.
  - `2025`는 커뮤니티 이미지 + 투자 맥락, `2026`은 멤버별 생활형/시장형 단어 혼합, `이벤트주간`은 리서치/예측/도움/경고/위기 축을 우선 남겼다.
  - scatter 초안 스펙:
    - `projects/wepoll-samsung/charts/word2vec-pca-2025-datawrapper.json`
    - `projects/wepoll-samsung/charts/word2vec-pca-2026-datawrapper.json`
    - `projects/wepoll-samsung/charts/word2vec-pca-eventweek-datawrapper.json`
  - 현재 발행본:
    - 2025 scatter: `REjQy`
    - public url: `https://datawrapper.dwcdn.net/REjQy/1/`
    - 2026 scatter: `nI7xI`
    - public url: `https://datawrapper.dwcdn.net/nI7xI/1/`
    - 이벤트주간 scatter: `u08tZ`
    - public url: `https://datawrapper.dwcdn.net/u08tZ/1/`
    - 현재는 `2025 / 2026 / 이벤트주간` 3시기 scatter가 모두 발행된 상태다.

### most similar 5

- 표용 CSV:
  - `projects/wepoll-samsung/prepared/dw_member_word2vec_similar_table.csv`
- 권장 표현:
  - Datawrapper table
  - 열: `period`, `member`, `rank`, `neighbor`, `cosine`
- 메모:
  - 이 자산은 scatter plot과 별개로 독립 표로 써도 된다.
  - table 초안 스펙:
    - `projects/wepoll-samsung/charts/word2vec-similar-table-datawrapper.json`
  - 현재 발행본:
    - chart id: `Q1Xdw`
    - public url: `https://datawrapper.dwcdn.net/Q1Xdw/1/`
  - 현재는 `2025 / 2026 / 이벤트주간`을 한 표에 합쳐 보여준다.
  - 멤버별 3기간 비교표:
    - 슈카: `Y8oWd` `삼전 이벤트: 슈카 유사 단어`
    - 알상무: `fgHQC` `삼전 이벤트: 알상무 유사 단어`
    - 니니: `P1f7d` `삼전 이벤트: 니니 유사 단어`
    - PNG:
      - `exports/wepoll-samsung/member-tables/similar-shuka.png`
      - `exports/wepoll-samsung/member-tables/similar-alsangmu.png`
      - `exports/wepoll-samsung/member-tables/similar-nini.png`

## Fightin Words

### overall

- 표용 CSV:
  - `projects/wepoll-samsung/prepared/dw_fightin_words_overall_table.csv`
- 권장 표현:
  - Datawrapper table
  - 멤버별 top 10~15만 노출
  - table 초안 스펙:
    - `projects/wepoll-samsung/charts/fightin-words-overall-table-datawrapper.json`
  - 현재 발행본:
    - chart id: `6cmWE`
    - public url: `https://datawrapper.dwcdn.net/6cmWE/1/`
  - 현재는 overall 표만 먼저 발행했다.

### period split

- 표용 CSV:
  - `projects/wepoll-samsung/prepared/dw_fightin_words_period_table_슈카.csv`
  - `projects/wepoll-samsung/prepared/dw_fightin_words_period_table_알상무.csv`
  - `projects/wepoll-samsung/prepared/dw_fightin_words_period_table_니니.csv`
- 메모:
  - 형식은 `rank + 2025 / 2026 / 이벤트주간` 3열 비교표다.
  - 이벤트주간은 아직 `4/12` 완전 반영 전이라 파이프라인 점검용 성격이 강하다.
  - 멤버별 차트:
    - 슈카: `v8AfO` `삼전 이벤트: 슈카 차별 단어`
    - 알상무: `HGf2C` `삼전 이벤트: 알상무 차별 단어`
    - 니니: `gUxLZ` `삼전 이벤트: 니니 차별 단어`
  - PNG:
    - `exports/wepoll-samsung/member-tables/fightin-shuka.png`
    - `exports/wepoll-samsung/member-tables/fightin-alsangmu.png`
    - `exports/wepoll-samsung/member-tables/fightin-nini.png`

### pre/post

- 표용 CSV:
  - `projects/wepoll-samsung/prepared/dw_fightin_words_prepost_table.csv`
- 권장 표현:
  - Datawrapper table
  - 현재는 post 표본이 매우 작아서 차트보다 표가 맞다.
  - table 초안 스펙:
    - `projects/wepoll-samsung/charts/fightin-words-prepost-table-datawrapper.json`

### next target

- 최종 방향:
  - `2025 / 2026 / 이벤트주간` 3분할 fightin words
  - 멤버별 대표 단어를 같은 포맷의 표로 비교
- 핵심 질문:
  - `슈카는 이번 이벤트를 통해 이미지 개선을 보였는가`
- 해석 가설:
  - 이벤트주간에서 `리서치`, `예측`, `도움`처럼 신뢰/기여 맥락 단어가 강화되면 개선 신호로 볼 수 있다.
  - 반대로 기존 시장 일반어만 반복되면 이벤트 고유 효과는 약하다고 볼 수 있다.

## 추천 우선순위

1. `W2V similar 5`는 Datawrapper table로 먼저 발행
2. `W2V selected dots`를 기준으로 scatter 최종판을 확정
3. `fightin words overall`은 table로 보조자료화
4. `fightin words`는 4/12 데이터가 온전히 들어온 뒤 `2025 / 2026 / 이벤트주간` 3분할로 재산출
