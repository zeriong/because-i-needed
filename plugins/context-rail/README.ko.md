<p align="center"><strong>context-rail</strong></p>

<p align="center"><strong>Claude Code</strong>와 <strong>Codex CLI</strong>에서만 동작합니다. 측정은 Claude Code에서 했습니다.</p>

<p align="center"><strong>기록된 결정이 매 턴이 아니라, 에이전트가 그 결정이 관할하는 파일을 여는 순간 도착합니다.</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.3.1-blue" alt="Version"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a></p>

<p align="center"><a href="#시작하기">시작하기</a> &bull; <a href="#무엇을-쓰는가">무엇을 쓰는가</a> &bull; <a href="#기록">기록</a> &bull; <a href="#도착-훅">도착 훅</a> &bull; <a href="#결정-바꾸기">결정 바꾸기</a> &bull; <a href="#측정한-것">측정한 것</a> &bull; <a href="#codex">Codex</a> &bull; <a href="#요구사항">요구사항</a> &bull; <a href="#설치">설치</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub><a href="../../README.ko.md">because-i-needed</a>의 일부</sub></p>

---

`CLAUDE.md`와 `AGENTS.md`는 매 턴 실립니다. 그래서 거기 적은 결정은 모두 매 턴 비용이 들고, 다른 내용 사이에 묻히기 쉽습니다. context-rail은 파일별 결정을 그 결정이 관할하는 코드 옆으로 옮깁니다. 그리고 에이전트가 그 파일을 읽거나 고칠 때 그 결정을 맥락에 넣는 훅을 설치합니다. 늘 실리는 파일은 줄어들기만 합니다.

## 시작하기

- Claude Code: `/context-rail:build` — 현재 레포에 rail을 설치합니다.
- Codex: `$context-rail:build`.
- `/context-rail:audit`(Codex: `$context-rail:audit`)는 설치된 rail을 점검만 하고 아무것도 바꾸지 않습니다.

`build`는 지시 파일을 읽고 항목마다 번호를 붙인 뒤 표 하나를 보여 줍니다. 표에는 남는 것, 결정 기록이 되는 것, 경로 규칙이 되는 것, 제안만 하는 것(자동화·개인 설정·이미 도구가 강제하는 규칙)이 나뉘어 있습니다. 답하기 전에는 아무것도 쓰지 않습니다. 개인 항목은 대신 옮기지 않습니다.

## 무엇을 쓰는가

모두 프로젝트 파일이며, 레포를 클론하는 모두와 공유됩니다.

| 파일 | 내용 |
|---|---|
| `<dir>/PRECEDENT.md` | 그 디렉터리 파일들의 결정 기록 |
| `.claude/rules/<topic>.md` | 경로 묶음에 적용되는 규칙, `paths:` frontmatter 포함 |
| `.claude/hooks/precedent-context.py` | 도착 훅 |
| `.claude/settings.json` | PostToolUse(Read·Edit·Write·MultiEdit·Bash)와 PostToolUseFailure(Bash)에 훅을 연결합니다. 다른 설정은 그대로 둡니다 |
| `.claude/context-rail.json` | 훅이 관할하는 소스 확장자 |

`CLAUDE.md`에서 옮긴 항목은 거기서 지우고, 포인터 줄은 남기지 않습니다. `build`는 지시 파일의 크기를 전후로 글자와 바이트 양쪽으로 잽니다. 둘 중 하나라도 늘면 실패로 처리합니다.

## 기록

```markdown
## tab-keys.mjs

### §stable-tab-keys — closing a tab never renumbers the others
- Since: 2026-09-02
- Decision: a key is assigned once and is never reused or shifted.
- Forbidden: renumbering the remaining keys after a close.
- Reason: shifting keys remounts the tabs to the right and drops their form input.
- Evidence: `tab-keys.test.mjs`
```

파일은 자기 디렉터리나 그 위에서 가장 가까운 `PRECEDENT.md`의 관할을 받습니다. `## ` 제목에는 파일 하나 이상의 이름을 적습니다(`a.ts · b.ts`). 이름이 실제 파일을 가리키면 그 파일에만 붙습니다. 전체 형식은 [`skills/build/references/record-format.md`](skills/build/references/record-format.md)에 있습니다.

## 도착 훅

에이전트가 관할 파일을 읽거나 고치면, 훅이 그 파일의 절을 맥락에 넣고 결정 변경에 관한 짧은 단락을 뒤에 붙입니다. 읽기에는 Read 도구뿐 아니라 셸의 `cat`·`sed`·`grep` 등도 포함됩니다.

- 파일마다 세션·에이전트당 한 번 울리므로 서브에이전트도 기록을 받습니다.
- 실패한 셸 읽기는 PostToolUseFailure가 맡습니다.
- 출력은 10,000자 아래로 유지합니다.
  - 6,000자 이하의 절은 통째로 넣고, 더 길면 제목과 결정 줄로 압축합니다.
  - 10,000자를 넘으면 Claude Code는 미리보기만 보여 줘서, 끝에 붙은 단락이 잘립니다.
- git이 무시하는 파일에는 아무것도 주지 않습니다.
- 내부 오류는 조용히 종료하고 에이전트를 막지 않습니다.

관할 파일을 고치면 기록당 한 번, 「이 변경이 새 결정을 만들면 같은 변경에서 그 기록에 적으라(파일의 `## ` 절이 없으면 추가)」는 한 줄을 받습니다. 어떤 `PRECEDENT.md` 도 관할하지 않는 파일을 고치면, 그 한 줄이 대신 어디에 만들지 알려 줍니다. 파일 옆 `<dir>/PRECEDENT.md` 에 `## <파일>` 절과 결정 블록을 쓰라는 내용이고, 디렉터리당 한 번입니다. 그런 파일을 읽기만 하면 아무것도 주지 않습니다.

## 결정 바꾸기

각 절 뒤의 단락은 결정이 사용자의 확인으로만 바뀐다고 말합니다.

- 기록된 결정을 이름으로 지목하며 뒤집으라고 하면, 에이전트는 변경하고 결정 블록을 제자리에서 고쳐 쓰며 사용자가 뒤집었다고 남깁니다. 예: 「`src/tabs/PRECEDENT.md` §stable-tab-keys가 막고 있지만 뒤집겠다」.
- 그 밖에 결정과 충돌하는 요청은, 아무리 단호해도, 에이전트가 편집 전에 멈춥니다. 결정과 충돌 지점을 말하고 묻습니다. 이때 상류 변경, 새 측정, 보고된 결함, 다른 축 중 해당하는 것이 있는지도 짚습니다.
- 다른 에이전트가 맡긴 일(서브에이전트, peer-coding 같은 작업자)이라면, 그 위임은 사용자가 결정을 지목해 뒤집으라고 했다고 전할 때만 확인으로 칩니다. 「그래도 진행하라」나 「새 결정이 기록을 대체한다」는 위임은 확인이 아니며, 에이전트는 멈추고 일을 맡긴 에이전트에게 보고해 사용자에게 묻게 합니다.

## 측정한 것

측정은 모두 [z-lab `precedent-lab/`](https://github.com/zeriong/z-lab/tree/main/precedent-lab)에 있습니다. 조건은 Claude Code 2.1.296–2.1.312와 Codex 0.163.0, headless이고, 행에 다른 에이전트가 적혀 있지 않으면 Opus, effort `xhigh`입니다.

| 주장 | 결과 | 실험 |
|---|---|---|
| 포인터가 아니라 절 본문을 넣으면 금지 줄이 첫 편집 전에 맥락에 들어온다 | 함정 런 3/15 → 44/45 | `real-env-rail-2.1.296` |
| 단락은 기록을 지목하지 않은 충돌 요청을 멈추게 한다 | 금지 깸: 단락 없음 11/12 → 단락 있음 0/12 | `stop-en-r2-2.1.306` |
| …명시적 뒤집기는 통과시킨다 | 12/12 진행, 기록을 제자리에서 고쳐 씀 | `stop-en-r2-2.1.306` |
| …충돌 없는 편집은 막지 않는다 | 0/15 멈춤 | `stop-en-r2-2.1.306` |
| `build`는 항목을 맞는 자리로 옮긴다 | 5/5 런: 14/14 항목, 검사 모두 통과, `CLAUDE.md` 1,906 → 540자 | `build-fidelity-0.1.0` |
| `audit`는 아무것도 바꾸지 않고 점검하며 심어 둔 결함을 짚는다 | 4/4 런: 변경 0, 검사 모두 실행, 심은 결함 3/3 지목, 거짓 결함 0 | `audit-canary-0.1.0` |
| `build`로 정규화한 프로젝트는 같은 결정을 `CLAUDE.md`에 둔 경우보다 잘 지킨다 | 권위 요청에서 금지 깸: 상주 12/12 → 정규화 0/12, 오정지 둘 다 0/15 | `fresh-project-0.1.0` |
| 경로 규칙은 맞는 파일에 처음 닿을 때 로딩된다 | Read·셸 읽기·Write 모두 규칙이 붙었다 | `platform-r2-2.1.308-0.163.0` |
| 다른 에이전트의 위임은 사용자의 지목을 전할 때만 확인이다 | 메인이 쓴 「그래도 진행하라」 위임에서 0.1.0 단락의 Sonnet 서브에이전트가 6/9 깸. 같은 문장을 고정한 위임에서 0.1.0 단락 12/12 → 0.2.0 단락 0/12 | `leaf-2.1.309`, `leaf-r2-2.1.309` |
| …다만 실제 비공개 레포 포크에서는 결정 이름 없이 미리 승인한 위임이 한 번 새었다 | Sonnet 서브에이전트 1/12 깸(최상위 세션 0/12, 훅 없는 대조 12/12). 깬 1건은 결정을 지목하지 않은 메인의 「이미 결정됐다, 다시 따지지 말고 항목을 갱신하라」 위임 뒤였다 | `real-repo-0.2.0` |
| …결정을 지목하지 않고 「이미 결정됐다, 기록을 갱신하라」고만 하는 위임도 확인이 아니다 | 그 모양의 고정 위임을 받은 Sonnet 작업자: 0.1.0 단락 12/12 깸, A3 0/12 | `unnamed-preauth-0.3.1` |
| 기록이 없는 경로를 고치면 코드 옆에 기록이 생긴다 | 그 경로의 기록: 훅 없음 0/9, 0.2.0 3/9, 0.3.0 8/9. 결정이 없는 편집은 기록을 만들지 않음(0/6) | `record-0.3.0` |
| 압축된 절도 프로젝트 자체 도착 훅이 주던 결정을 그대로 준다 | 비공개 레포 관할 파일 2,681개에서 결정이 줄어든 파일 0개(0.2.0: 3개) | `record-0.3.0` |
| 한정어가 붙은 결정 줄(`- 결정(범위):`, `- 결정 B1:`)도 압축과 `records-lint` 에서 결정 줄로 센다 | 비공개 레포 관할 파일 2,681개: 주입된 한정어 결정 줄 243 → 292, 결정 없는 블록으로 센 수 277 → 266, 결정이 빠진 파일 0 | `labels-0.3.1` |
| 일을 위임받은 에이전트도 규칙을 지킨다 | Opus·Sonnet 서브에이전트, Sonnet `claude -p`·Codex `gpt-6-luna` 작업자 모든 경로에서 금지 깸 0/12, 뒤집기 진행 12/12, 멈춤 0/15 | `leaf-r2-2.1.309` |

함정과 build 결과는 합성 fixture와 비공개 레포 하나에서 나왔고, 칸당 12–15런입니다.

셸 명령(`cat > file`, `sed -i`)으로 고친 파일은 편집으로 보지 않아 기록 알림을 받지 못합니다. `record-0.3.0` 에서 기록을 남기지 않은 0.3.0 런 3개는 모두 그렇게 파일을 썼습니다.

**측정하지 않은 것**
- 다른 모델·effort, 대화형 세션
- 다른 언어로 쓴 기록과 이 단락의 조합
- 큰 레포, Orca의 양방향 작업자
- Codex에서 `build`·`audit`를 돌리는 것

## Codex

Codex에서도 같은 스킬이 같은 훅을 설치합니다(`$context-rail:build`, `install-hooks.py --host codex` → `.codex/hooks/`, `.codex/hooks.json`).

- **플랫폼**(Codex 0.163.0, 실험용 probe 훅)
  - PostToolUse 출력이 모델에 전달됩니다.
  - 셸 읽기는 `Bash`, 편집은 `apply_patch`로 들어옵니다.
  - 실패한 셸 호출에도 PostToolUse가 옵니다.
- **Codex에서 이 플러그인의 훅**(`install-hooks.py --host codex`로 설치): Codex 작업자(`gpt-6-luna`, effort high, peer-coding의 위임)가 규칙을 지켰습니다. 금지 깸 0/12, 뒤집기 진행 12/12, 멈춤 0/15(`leaf-r2-2.1.309`).
- **측정하지 않은 것**: Codex에서 `build`·`audit`를 돌리는 것, 중첩 `AGENTS.md`가 언제 로딩되는지, `apply_patch` 쪽 전달.

기대기 전에 `/hooks`에서 훅을 신뢰하세요.

## 요구사항

- `PATH`의 `python3`(3.9 이상).
- `git` — 훅이 레포 루트를 찾고 무시된 파일을 건너뛰는 데 씁니다.

## 설치

먼저 마켓플레이스를 추가한 뒤 플러그인을 설치합니다.

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install context-rail@because-i-needed
```

Codex는 [마켓플레이스 안내](../../README.ko.md#codex)를 따르세요.

## 라이선스

MIT. [LICENSE](../../LICENSE)를 보세요.
