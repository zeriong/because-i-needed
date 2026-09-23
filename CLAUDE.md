# because-i-needed — 저장소 공통 규칙

이 저장소는 플러그인 3개(plan-smith, harness-builder, ux-ui-builder)를 담은 Claude Code 마켓플레이스다.
**공통 규칙은 이 파일**, **플러그인별 규칙은 `plugins/<이름>/CLAUDE.md`** 에 있다(그 플러그인의 파일을 읽을 때 자동으로 로드된다).
플러그인 파일은 이 파일을 반복하지 않고 그 플러그인에만 해당하는 것만 쓴다 — 두 파일이 충돌하면 둘 다 고친다.

각 조항에 근거를 함께 적는다. 근거를 모르면 조항이 요식행위로 퇴화한다.

---

## 제1조 — 설치본에 도달하는 것은 `plugins/<이름>/` 뿐이다

- 설치 시 캐시 `~/.claude/plugins/cache/because-i-needed/<플러그인>/<버전>/` 에는 **플러그인 폴더만** 복사된다.
  루트 README·이 파일은 설치한 사용자에게 가지 않는다. 사용자가 읽어야 할 내용은 플러그인 README에 쓴다.
- `plugins/<이름>/CLAUDE.md` 는 패키지에 실려 가지만 **사용자 세션에는 로드되지 않는다**
  (Claude Code는 작업 디렉터리 계층과 사용자 전역 CLAUDE.md만 읽는다). 그래서 이 파일들은 메인테이너용이다.
  설치한 사용자에게 적용할 지시는 스킬·에이전트·훅으로 넣는다.

**근거:** plan-smith 1.1.3 검증에서 캐시에 루트 CHANGELOG가 0건이었다. 2026-09-23, 활성화된
humanize-korean 플러그인의 설치본에 CLAUDE.md가 있었지만 세션 컨텍스트에 로드되지 않았고,
`claude plugin validate` 도 "CLAUDE.md at the plugin root is not loaded as project context" 경고로 같은 사실을 알린다.

## 제2조 — 동작이 바뀌면 버전을 올린다. 버전 문자열은 전부 같이 바꾼다

- 플러그인은 **버전 키 캐시**에서 서비스된다. 소스만 고치면 설치된 클라이언트에 도달하지 않으면서
  클라이언트는 자신을 "최신"으로 보고한다. 따라서 동작에 영향을 주는 변경은 반드시 버전을 올린다.
  내용 변경 없이 버전만 올리는 전달용 릴리스도 정당하다.
- 플러그인 하나의 버전 문자열은 **12곳**이다:

  | 파일 | 위치 |
  |---|---|
  | `plugins/<이름>/.claude-plugin/plugin.json` | `"version"` |
  | `.claude-plugin/marketplace.json` | 그 플러그인 엔트리의 `"version"` (최상위 `metadata.version`은 마켓플레이스 자체 버전 — 별개) |
  | `plugins/<이름>/README*.md` 5개 | 상단 shields.io 버전 배지 |
  | `README*.md` 5개 (루트) | 플러그인 제목 옆 `` `vX.Y.Z` `` |

- 확인: `grep -rn --include='*.md' --include='*.json' -F '<이전버전>' . | grep -v CHANGELOG` 에
  그 플러그인 줄이 남지 않아야 한다. 다른 플러그인이나 마켓플레이스가 같은 버전 문자열을 쓰면
  (현재 harness-builder `1.0.0` = `metadata.version` `1.0.0`) 걸린 줄이 어느 것인지 눈으로 구분한다.
- 버전 문자열·CHANGELOG(있는 플러그인만)·README 변경은 **한 커밋**으로 묶는다. 쪼개지 않는다.
- SemVer: **MAJOR** 기존 사용법이 깨짐 / **MINOR** 동작 추가·변경 / **PATCH** 문서·오타·전달용(동작 변경 없음).
  플러그인별 구체 기준은 각 플러그인 CLAUDE.md에 있다.

**근거:** plan-smith 1.1.1이 존재하는 이유가 이것뿐이다 — 소스에 쓴 조항을 설치본이 1.1.0으로 계속 서비스했다.

## 제3조 — README는 5개 언어, 같은 커밋

- 모든 README는 5개 파일이다: `README.md`(영어, **원본**), `README.ko.md`, `README.ja.md`, `README.zh-CN.md`, `README.zh-TW.md`.
  번역본은 영어 원본 기준으로 맞춘다.
- README를 고치면 **5개를 같은 커밋에서** 고친다. 새 플러그인은 첫 커밋부터 5개를 갖춘다.
- 사용자가 이해해야 하는 개념·동작이 바뀌면 그 플러그인 README 5개를, 플러그인 한 줄 소개가 바뀌면 루트 README 5개도 고친다.
  내부 리팩터링·오타는 해당 없음.
- 링크: 플러그인 README의 상대 경로는 플러그인 폴더 기준, 루트 README의 플러그인 링크는 `plugins/<이름>`(폴더 트리).
  번역본의 페이지 내 앵커는 **번역된 제목의 GitHub slug** 다. README를 고친 뒤 상대 링크와 앵커가 전부 살아 있는지 확인한다.
- 숫자 주장은 **세어서** 쓴다.

**근거:** 2026-09-23 사용자 결정(루트 README "Language policy"에 공개). 원본 레포 시절 README가 실물과
어긋난 사례가 있다 — ux-ui-builder 루트 README는 1.1.0의 모바일 기능을 빠뜨린 채 1.0.0 배지를 달고 있었다.

## 제4조 — 파일별 언어

- 사용자 세션에서 Claude가 읽는 파일 — `SKILL.md`, `references/*.md`, `agents/*.md`, 훅이 내보내는 메시지 — 은 **영어**.
- `CLAUDE.md`(이 파일과 플러그인별 파일)는 **한국어 단일**. README가 아니므로 5개 언어 대상이 아니다.
- `plugins/plan-smith/CHANGELOG.md` 는 영어 단일(기존 항목 전부 영어).

## 제5조 — 매니페스트는 검증기로 확인한다

- `.claude-plugin/marketplace.json` 이나 `plugin.json` 을 고치면:
  `claude plugin validate .` 와 `claude plugin validate plugins/<이름>` 이 통과해야 한다.
  플러그인 검증의 경고 `CLAUDE.md at the plugin root is not loaded as project context` 는 **예상된 것**이다 —
  그 파일은 메인테이너용이라 로드되지 않는 게 맞다(제1조). 그 외의 경고는 원인을 확인한다.
- 새 플러그인 추가 = `plugins/<이름>/`(매니페스트·README 5개·CLAUDE.md) + `marketplace.json` 엔트리 + 루트 README 5개의 소개 섹션.

## 제6조 — 커밋 규약

- Conventional Commits. 헤더 ≤ 50자, 본문 줄 ≤ 72자, 본문은 *무엇*이 아니라 *왜*.
- author/committer는 항상 `zeriong <jaeryong95@gmail.com>`.
  **Claude 속성 금지** — `Co-Authored-By`, "Generated with", 로봇 이모지 전부.
- `--no-verify` 금지, amend 금지, force-push 금지.

**근거:** plan-smith 릴리스 법령 제5조와 zeriong-commit 스킬의 절대 규칙을 저장소 전체로 넓힌 것.

## 제7조 — 이력은 두 곳에 있다

이 저장소의 이력은 `3714dd5`(2026-09-23, 세 플러그인을 들여온 커밋)부터다. 그 이전 이력 —
plan-smith ≤ 1.4.2, harness-builder 1.0.0, ux-ui-builder ≤ 1.1.0 — 은 원본 레포
`zeriong/plan-smith`, `zeriong/harness-builder`, `zeriong/ux-ui-builder` 에 있다.
버전 경계를 git으로 확인할 때 이 저장소만 보면 그 이전이 비어 보인다.
