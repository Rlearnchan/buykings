# Datawrapper Notes

이 문서는 이 저장소에서 Datawrapper를 운영할 때 필요한 실무 메모를 모아두는 곳이다.

## 2026-04-11 확인 사항

확인 목적:

- Free 플랜으로 시작 가능한지
- API를 바로 붙일 수 있는지
- 유튜브 방송 첨부 같은 상업적 활용이 가능한지

## Official Source Summary

### Pricing / Free Plan

Datawrapper Academy의 가격 안내 문서는 Free, Custom, Enterprise 세 가지 플랜을 안내한다. 같은 문서에서 Free 플랜은 charts, maps, tables의 publish와 PNG export를 제한 없이 제공한다고 설명한다.

Source:

- [What pricing plans we offer](https://www.datawrapper.de/docs/datawrapper-pricing)

### API

Datawrapper는 별도 developer portal에서 REST API 문서를 제공한다. 인증 토큰 관련 엔드포인트와 chart API가 공개돼 있어, 기술적으로는 추후 자동화 연동이 가능한 구조다.

Source:

- [Datawrapper Developer API](https://developer.datawrapper.de/)
- [List API tokens](https://developer.datawrapper.de/reference/getauthtokens)

### Terms of Service

Datawrapper Terms of Service 페이지는 2022-03-07 업데이트 기준으로, 무료 및 유료 서비스를 모두 포괄하는 약관이라고 설명한다. 또한 법인, 조직, 회사의 behalf로 사용하는 경우 권한 있는 사용자가 약관에 동의해야 한다고 적고 있다. 문면상 조직/회사 단위 사용 자체를 전제하고 있다.

Source:

- [Terms of Service](https://www.datawrapper.de/terms)

## Commercial Use View

2026-04-11 기준으로 확인한 범위에서는, Free 플랜 사용자가 유튜브 방송 같은 상업적 맥락에서 Datawrapper 차트를 게시하는 것을 일반적으로 금지한다는 명시 조항은 찾지 못했다.

다만 아래는 분명히 주의가 필요하다.

- 사용 데이터의 재사용 권리와 저작권 책임은 사용자에게 있다.
- 재게시가 금지된 제3자 데이터를 업로드하면 안 된다.
- 브랜딩 제거, export 옵션, 커스터마이징은 플랜에 따라 달라질 수 있다.
- 실제 상업 운용 전에 약관과 pricing 페이지를 다시 확인하는 것이 안전하다.

즉 현재 실무 판단은 다음과 같다.

- `유튜브 방송 첨부 용도 자체는 가능해 보임`
- `무료 플랜으로도 초기 운영은 충분히 가능해 보임`
- `브랜드/디자인 통일성 요구가 커지면 유료 플랜 검토 필요`

이 문서는 법률 자문이 아니라, 공식 문서 기반의 운영 메모다.

## Practical Recommendation

초기 운영은 아래 순서가 무난하다.

1. Free 플랜으로 차트 제작 및 PNG export 중심 운영
2. 차트 ID, 제목, source 문구를 이 저장소에 문서화
3. 반복 작업이 늘어나면 API 토큰 발급 가능 여부와 자동화 범위를 점검
4. 브랜딩 통일, 고해상도 export, 팀 협업 요구가 커지면 유료 전환 검토
