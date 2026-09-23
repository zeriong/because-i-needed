# plan-smith — 개발 규칙

루트 `CLAUDE.md`의 공통 규칙(설치 경계·버전업·README 5개 언어·커밋)이 전부 적용된다. 여기에는 plan-smith에만 해당하는 것을 쓴다.
원본은 `zeriong/plan-smith` 의 `.claude/CLAUDE.md` 릴리스 법령이다. 그 레포에서는 gitignore된 로컬 전용 파일이었고,
이 저장소로 옮기면서 경로를 맞췄다. 원 법령 제6조("이 파일은 커밋되지 않는다")는 폐기했다 — 여기서는 커밋한다.

구성: 스킬 `skills/plan-smith/SKILL.md`, references 3개(`frames.md`, `styles.md`, `packet-template.md`), 에이전트 `agents/plan-writer.md`, `CHANGELOG.md`.

---

## 제1조 — 버전업은 3종 세트다 (하나라도 빠지면 릴리스가 아니다)

같은 커밋에서 셋을 함께 처리한다.

1. **버전 문자열 12곳** — 루트 `CLAUDE.md` 제2조의 표.
2. **`CHANGELOG.md` 항목** — Keep a Changelog 형식. `Added` / `Changed` / `Fixed` / `Removed` 로 분류하고
   **`Why` 를 반드시 쓴다**(무엇을 바꿨는지가 아니라 왜 바꿨는지가 나중에 필요한 정보다).
   버전 경계는 기억이 아니라 git에서 확인한다: `git log -p -- plugins/plan-smith/.claude-plugin/plugin.json`
   (1.4.2 이전은 `zeriong/plan-smith` 레포 이력 — 루트 제7조).
   이 저장소에서 CHANGELOG는 플러그인 폴더 안에 있으므로 **설치본에 도달한다**(원본 레포에서는 루트에 있어 도달하지 않았다).
3. **README 개념 반영** — 프레임·게이트·파이프라인 단계·스타일처럼 **사용자가 이해해야 하는 개념**이 바뀌거나
   추가되면 `plugins/plan-smith/README*.md` 5개를 갱신한다. 한 줄 소개가 바뀌면 루트 README 5개도. 내부 리팩터링·오타는 해당 없음.

**숫자는 세어서 쓴다.** 프레임 수:

```bash
grep -cE '^### [a-z-]+ — ' plugins/plan-smith/skills/plan-smith/references/frames.md   # 2026-09-23 기준 26
```

`grep -c '^### '` 는 프레임이 아닌 섹션 6개(`Gate 0`, `The four predicates`, `The load-bearing path`,
`Requirements get verbs`, `Implementer contract`, `The machinery budget`)까지 세서 32가 나온다 — 쓰지 않는다.
README의 "26"은 두 가지다: **프레임 수**(26 frames)와 **실험 규모**(26-plan experiment). 프레임 수가 바뀌어도 실험 규모는 그대로 둔다.

**근거:** README가 프레임 수를 24개로 적고 있는 동안 실제 라이브러리는 25개였고, 이후 26개가 됐다.
원 법령의 "`grep -c '^### '` 에서 2를 뺀다"는 명세 규칙 섹션 4개가 추가되면서 틀린 방법이 됐다(2026-09-23 확인).

## 제2조 — 릴리스 후 설치본을 대조한다

버전을 올린 뒤 캐시(`~/.claude/plugins/cache/because-i-needed/plan-smith/<버전>/`)의 해당 파일이 실제로
바뀌었는지 대조한다(예: `frames.md` 줄 수 비교).

**근거:** 1.1.1 — 문서 예산·Gate 0 타이브레이크 조항을 소스에 썼는데 설치본은 1.1.0을 계속 서비스했고
(355줄 vs 364줄), 버전을 올려서야 전달됐다.

## 제3조 — SemVer 기준

- **MAJOR** — 기존 사용법이 깨진다(스킬 인터페이스, 패킷 형식의 비호환 변경).
- **MINOR** — 프레임·게이트·파이프라인 단계 **추가**, 라우팅 규칙 변경 등 동작이 늘거나 달라진다.
- **PATCH** — 문서·오타·전달용 버전 상승. **동작 변경 없음.**

문서만 바뀌었는데 MINOR를 붙이지 않는다. 프레임을 추가했는데 PATCH를 붙이지 않는다.

## 제4조 — 근거 없는 주장을 문서에 쓰지 않는다

README·CHANGELOG의 실증 주장("A/B에서 이겼다", "N플랜으로 검증했다")에는 **어디서 나온 관측인지**
(z-lab `plan-smith-lab/` 의 어느 계열인지)가 따라붙어야 한다. 관측이 1회면 1회라고 쓰고, 한계는 같은 문단에 쓴다.

**근거:** 1.1.0은 **자기 산출물이 무프레임 베이스라인에 패배한** 통제 A/B에서 나왔다. 그 사실을 README에
적었기 때문에 다음 사람이 같은 함정을 피할 수 있다. 좋은 결과만 적으면 라이브러리는 광고가 되고, 실패를 적으면 도구가 된다.

## 제5조 — 이름과 불변식

- 플러그인명 `plan-smith` 는 SKILL.md의 에이전트 참조(`plan-smith:plan-writer`)와 README 10개의
  `/plan-smith:plan-smith` 에 박혀 있다. 이름을 바꾸면 전부 같이 바꾼다.
- `SKILL.md`·`agents/plan-writer.md` 를 고칠 때 README "Design invariants" 5개(메인은 플랜을 쓰지 않는다 /
  확인된 패킷 없이 집필 없음 / 집필자 입력은 자기완결 / 원문 릴레이 / 스타일은 모델 선택이 아니다)를 깨지 않는다.
  깨야 한다면 그것은 설계 변경이므로 사용자와 먼저 합의하고, README 불변식 목록도 함께 고친다.
