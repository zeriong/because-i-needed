# harness-builder — 개발 규칙

루트 `CLAUDE.md`의 공통 규칙이 전부 적용된다. 여기에는 harness-builder에만 해당하는 것을 쓴다.
이 플러그인은 원본 레포에 개발 규칙 파일이 없었다. 아래는 전부 2026-09-23 기준 코드에서 확인한 사실에서 도출했다.

구성: 스킬 1개 `skills/harness-builder/SKILL.md` 뿐이다. 에이전트·훅·스크립트·references 없음.
이 스킬은 **대상 프로젝트에** `.claude/` 하네스를 생성한다 — 이 플러그인 자체가 훅을 설치하는 것이 아니다.

---

## 제1조 — SKILL.md와 README는 같은 사실을 말해야 한다

README 5개가 SKILL.md의 다음 사실을 옮겨 적고 있다. SKILL.md에서 바꾸면 README 5개도 같은 커밋에서 고친다.

| 사실 | SKILL.md의 출처 |
|---|---|
| 8-phase 워크플로우와 phase별 책임 표 | `## Phase 0` ~ `## Phase 8` |
| 생성 파일 트리 (`.claude/settings.json`, `hooks/inject-context.sh`, `scripts/review-gate.sh`, `skills/project-rules`, `skills/harness-engineering`, `docs/conventions/<rule>.md`) | 상단 산출물 목록, `## harness-builder complete` |
| 트리거 키워드 6개 | frontmatter `description` |
| 품질 6축과 평균 3.5 미만 reject | `## Absolute laws` 4번, `## Phase 8` |
| 회귀 cap = 3 | `## Phase 6`(6.2), `## Phase 8`, `## Notes for Claude` |
| Opus 1 + Sonnet 1, 1-shot 리뷰 | `## Phase 6`(6.2), `## Phase 8` |
| YAGNI — 위반 0 + 사용자 언급 0인 룰은 도입 금지 | `## Phase 2`, `## Notes for Claude` |

## 제2조 — SKILL.md는 플러그인 안의 파일만 참조한다

설치한 사용자의 Claude가 읽을 수 있는 것은 플러그인 폴더뿐이다(루트 제1조).
SKILL.md가 참조하는 문서는 `skills/harness-builder/references/` 에 넣고 상대 경로로 가리킨다.

**알려진 결함 (2026-09-23 확인, 미수정):** SKILL.md는 비공개 문서를 "그대로 사용"하라고 지시한다 —
`setup-guide` §4(`inject-context.sh`), §5(11-phase 워크플로우), §7(gate 스크립트 뼈대·diff 범위),
§8(hard-stop 보고 형식), `research-foundation` §2. 원본은 `~/WorkSpace/Z-Work/__private__MY-CONFIG/claude/harness/` 에
있고 플러그인에 없으므로, 설치본에서는 이 절들을 읽을 수 없어 Claude가 추측으로 채운다.
README의 하네스 우회 문구 목록(`!`, `harness 빼고`, `without harness`, `skip harness`, `no harness`)도
SKILL.md가 아니라 setup-guide §4에서 온 것이다.

- 고치려면 필요한 절을 `references/` 로 옮기고 SKILL.md가 그 파일을 가리키게 한다.
  비공개 문서를 공개 레포에 싣는 일이므로 **어느 절을 옮길지는 사용자가 정한다.**
- 동작이 바뀌는 변경이므로 버전을 올린다(루트 제2조).
- README 요구사항의 `bash 4+` 도 SKILL.md에 근거가 없다. 생성 스크립트 기준으로 확인되기 전에는 근거 있는 주장으로 취급하지 않는다.

## 제3조 — 이름

플러그인명·스킬명 `harness-builder` 는 README 10개의 `/harness-builder:harness-builder` 에 박혀 있다. 이름을 바꾸면 전부 같이 바꾼다.
