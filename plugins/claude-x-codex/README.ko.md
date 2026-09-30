<p align="center">
  <strong>claude-x-codex</strong>
</p>

<p align="center">
  <strong>Claude × Codex 동료 오케스트레이션 — 두 에이전트가 동료로서 서로의 계획·구현·리뷰를 주고받습니다.</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.3.1-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a>
</p>

<p align="center">
  <a href="#설치">설치</a> &bull;
  <a href="#명령">명령</a> &bull;
  <a href="#동작-방식">동작 방식</a> &bull;
  <a href="#설정">설정</a> &bull;
  <a href="#플랫폼">플랫폼</a>
</p>

<p align="center">
  <a href="README.md">English</a> &bull;
  <a href="README.ko.md">한국어</a> &bull;
  <a href="README.ja.md">日本語</a> &bull;
  <a href="README.zh-CN.md">简体中文</a> &bull;
  <a href="README.zh-TW.md">繁體中文</a>
</p>

<p align="center">
  <sub><a href="../../README.ko.md">because-i-needed</a>의 플러그인</sub>
</p>

---

**C**laude **×** **C**odex 동료 오케스트레이션입니다. 바탕이 다른 두 에이전트는 서로 다른 방식으로 실수하므로, 각자가 상대의 작업을 리뷰합니다 — 메인 에이전트의 계획도 예외가 아닙니다. 둘의 의견이 갈리면 역할이 아니라 테스트가 판정합니다.

claude-x-codex는 비공식 커뮤니티 플러그인입니다. Anthropic이나 OpenAI가 만들거나 보증하거나 지원하는 도구가 아닙니다.

## Codex

Codex CLI 0.158.0 이상이 필요합니다. 설치 후 새 세션을 시작하세요. Claude 명령은 `/plugin:skill`, Codex 명령은 `$plugin:skill`입니다. 공통 스킬과 자료는 이 플러그인 안에 포함됩니다. 자동 동작을 사용하기 전에 `/hooks`에서 함께 설치된 훅을 검토하고 신뢰하세요.

```bash
codex plugin marketplace add https://github.com/zeriong/because-i-needed.git
codex plugin add claude-x-codex@bin
```

`$claude-x-codex:run`, `$claude-x-codex:mode on|off|status|clear`, `$claude-x-codex:audit`을 사용합니다. 모드 변경은 두 호스트 모두 사용자의 명시적인 요청이 필요합니다. Codex가 메인이 될 수 있으며 기존 Codex 실행 지침에 따라 벤더 간 리뷰를 유지합니다. 감사에는 `.codex/hooks.json`과 커밋되지 않은 `.codex/`, `.agents/` 맥락이 포함됩니다. 자동 모드는 UserPromptSubmit 훅 신뢰가 필요하고, 명시적인 run 호출은 훅 없이도 시작할 수 있습니다. Codex가 메인일 때 교차 벤더 작업에는 Claude CLI가 필요하며, 없으면 기존 단일 벤더 대체 경로를 사용합니다.

### Codex 설정

두 호스트에서 같은 `CXC_*` 설정·모드 범위·교차 벤더 리뷰 규칙을 사용합니다. 연결된 Git 작업 폴더에서도 모드 파일을 로컬 제외 처리합니다. 감사는 설정을 변경하지 않고 `AGENTS.override.md`의 우선순위와 잘못된 훅 선언을 보고합니다.

각 호스트의 라우팅은 설정한 CXC 검토 모델·추론 강도를 사용하며 괄호의 이름은 기본값입니다. 파일명 언급이나 fallback 설정만으로는 지침 일치를 단정하지 않고, 실제 적용 내용을 확인하도록 CHECK로 표시합니다.

## 명령

| 명령 | 하는 일 |
|---|---|
| `/claude-x-codex:run` | 작업을 오케스트레이션합니다: 메인 에이전트가 계획하고 모든 관문을 판단하며, 작업을 `claude-fast` / `codex-bulk` / `main` 레인으로 보내고, 각 벤더가 상대 벤더의 작업을 리뷰하게 합니다 |
| `/claude-x-codex:mode on\|off\|status\|clear [--global]` | 자동 오케스트레이션을 켜고 끄는 한 줄 스위치입니다. 사용자 전용이라 모델은 바꿀 수 없습니다 |
| `/claude-x-codex:audit` | 두 벤더가 같은 프로젝트 맥락에서 출발하는지 읽기 전용으로 점검합니다. 수정안만 제안하고 아무것도 바꾸지 않습니다 |

`on`·`off` 는 이 프로젝트의 플래그(`.claude-x-codex/mode`, git 제외)를 쓰고, `--global` 은 모든 프로젝트에 적용되는 기본값(`~/.config/claude-x-codex/mode`)을 씁니다. `clear` 는 프로젝트 플래그를 지우고, `CXC_MODE=on|off` 는 셸 하나에서 둘 다보다 우선합니다. 모드가 꺼져 있으면 `run` 은 요청할 때만 시작합니다.

## 설치

### Claude Code 플러그인 마켓플레이스 경유

1. Claude Code에서 `/plugin` 을 실행합니다.
2. Marketplaces → Add Marketplace.
3. URL 입력: `https://github.com/zeriong/because-i-needed.git` (또는 이 레포의 로컬 경로).
4. `claude-x-codex` 를 설치합니다.

### 또는 CLI로

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git   # 또는 로컬 경로
claude plugin install claude-x-codex@bin
```

### 또는 `~/.claude/settings.json`에 직접 연결

```json
{
  "extraKnownMarketplaces": {
    "bin": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": { "claude-x-codex@bin": true }
}
```

- **참고:** 설치하면 `UserPromptSubmit` 훅이 등록됩니다. 모든 프롬프트마다 실행되지만 모드가 꺼져 있으면 아무것도 출력하지 않고, 켜져 있으면 구현 작업을 `run` 으로 보내라는 네 줄짜리 메모(프롬프트당 입력 약 100토큰)를 추가합니다.

## 요구 사항

- **Claude Code**(또는 메인 에이전트로서의 Codex), **git** 저장소, bash 3.2+.
- **선택 — Codex CLI**(`codex`). 없으면 `run` 은 single-vendor 모드로 전환해 모든 리뷰를 같은 벤더의 별도 리뷰어 인스턴스에 맡기고, 그 사실을 알려 줍니다.
- **선택 — Orca**(오케스트레이션 활성화). 있으면 워커가 작업 중에 질문할 수 있고 관문이 사용자의 결정을 기다립니다. 없으면 워커는 서브에이전트나 CLI 호출로 단방향 실행됩니다.
- 감사의 훅 표에는 `python3` 이, Codex가 메인 에이전트로서 Claude 리뷰어를 돌릴 때는 `jq` 가 필요합니다.
- Claude Code 2.1.283, Codex CLI 0.157.1, Orca 1.4.215 기준으로 확인했습니다.

## 동작 방식

- **레인** — 워커는 effort `high` 로 실행합니다. `claude-fast`(Claude 최신 Sonnet: UI, 인터랙션, 코드 감각, Claude 쪽 도구), `codex-bulk`(Codex 최신 `luna`: 기존 계약에 대한 테스트, 타입, 기계적 마이그레이션처럼 결과가 완전히 정해진 작업), `main`(메인 에이전트: 강하게 결합된 작업이나 아직 명세를 찾아가는 작업).
- **교차 벤더 리뷰** — 리뷰어는 항상 작성자와 다른 벤더이고, 메인 에이전트 자신의 계획과 선별 결정도 상대 벤더의 리뷰를 받습니다. Claude는 최신 Opus로, Codex는 최신 `sol`로 리뷰하며, 둘 다 effort `xhigh` — 두 CLI 모두에서 `max` 바로 아래 단계 — 입니다. 인증·결제·데이터 마이그레이션 같은 고위험 단계라도 최상위 모델(최신 `astra` 또는 `max` 의 최신 Opus) 리뷰를 추가하기 전에 먼저 사용자에게 묻고, 스스로 올리지 않습니다. 리뷰어는 읽기 전용으로 실행되며, 두 CLI가 스키마로 강제하는 JSON을 반환합니다.
- **반론 1회** — 기각된 blocking·major 지적은 이유와 함께 한 번 리뷰어에게 돌아갑니다. 리뷰어는 수긍하거나 새 증거로 반박하고, 그래도 풀리지 않으면 양쪽 주장과 함께 DISPUTED로 사용자에게 올라옵니다.
- **증거가 판정** — 의견이 갈리면 테스트·재현·추적이 판정하며, 증거를 가진 쪽이 이깁니다. 증거가 없으면 사용자가 결정합니다.
- **컨텍스트 브리지** — 감사가 두 벤더가 서로 다른 지침 파일을 읽는 곳, 한 벤더에만 걸리는 훅, 워커 worktree에 빠질 커밋되지 않은 맥락을 찾아냅니다. `run` 이 직접 하는 Codex 호출은 Codex의 폴백 설정으로 `CLAUDE.md` 를 읽으므로 레포를 바꿀 필요가 없습니다. 대화형 Codex 세션(Orca 워커, 또는 메인 에이전트로서의 Codex)에는 같은 설정이 사용자의 Codex 설정에 있어야 합니다. 사용자 설정이나 레포를 바꾸는 수정은 계획 승인 단계에서 제안합니다.
- **디스크의 상태** — `.claude-x-codex/`(git 제외)에 계획·결정·리뷰가 남으므로, 실행이 압축(compaction)을 거쳐도 이어서 재개할 수 있습니다.

전용 계획 스킬이 있으면 `run`이 계획을 그 스킬에 맡깁니다.

## 설정

`run` 은 아래 값을 환경변수에서 읽고, 없으면 기본값을 씁니다:

| 변수 | 기본값 |
|---|---|
| `CXC_WORKER_MODEL` | `luna` |
| `CXC_REVIEW_MODEL` | `sol` |
| `CXC_FINAL_MODEL` | `astra` |
| `CXC_CLAUDE_WORKER` | `sonnet` |
| `CXC_CLAUDE_REVIEWER` | `opus` |
| `CXC_REVIEW_EFFORT` | `xhigh` |
| `CXC_WORKER_EFFORT` | `high` |
| `CXC_MAX_CYCLES` | `3` |
| `CXC_PARALLEL` | `3` |

모델 설정값은 제품군을 지정하며, 설치된 CLI가 제공하는 해당 제품군의 최신 버전이 항상 실행됩니다. `gpt-6-sol` 같은 버전 값도 해당 제품군의 최신 버전으로 올려집니다. 최신 버전을 확인할 수 없으면 레인이 이유를 알리고 멈춥니다.

CXC = **C**laude **×** **C**odex — 셸에서 설정하는 변수의 접두어입니다.

## 플랫폼

스크립트는 POSIX 도구만 쓰는 bash입니다(macOS의 bash 3.2와 BSD 유틸리티와 호환).

| 플랫폼 | 상태 |
|---|---|
| Linux | 지원 |
| macOS | 지원 |
| Windows + WSL | 지원 (Linux와 동일하게 동작) |
| Windows + Git Bash | 동작할 것으로 예상. 경로는 Git Bash를 따름 (`~` = `/c/Users/<you>`) |
| Windows PowerShell / cmd 단독 | 미지원 — Git for Windows를 설치하거나 WSL을 사용하세요 |

Windows에서는 스크립트가 LF를 유지해야 합니다. 플러그인의 `.gitattributes` 가 이를 강제하며, git 없이 파일을 복사했다면 줄바꿈을 LF로 바꿔 주세요.

## 라이선스

MIT. [LICENSE](../../LICENSE)를 참고하세요.
