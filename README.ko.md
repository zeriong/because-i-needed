<p align="center">
  <strong>because-i-needed</strong>
</p>

<p align="center">
  <strong>필요해서 만든 Claude Code와 Codex 플러그인 모음 — 프로젝트 하네스, 실측 기반 UI, Claude × Codex 오케스트레이션.</strong>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin%20Marketplace-orange" alt="Claude Code Plugin Marketplace"></a>
</p>

<p align="center">
  <a href="README.md">English</a> &bull;
  <a href="README.ko.md">한국어</a> &bull;
  <a href="README.ja.md">日本語</a> &bull;
  <a href="README.zh-CN.md">简体中文</a> &bull;
  <a href="README.zh-TW.md">繁體中文</a>
</p>

---

이 레포는 독립된 플러그인 3개를 담은 Claude Code와 Codex **플러그인 마켓플레이스**입니다. 필요한 것만 골라 설치하면 됩니다.

## Codex

같은 플러그인 3개를 Codex CLI 0.158.0 이상에서도 사용할 수 있습니다. 필요한 플러그인을 골라 설치하세요:

```bash
curl -fsSL https://raw.githubusercontent.com/zeriong/because-i-needed/main/install.sh | bash -s -- --host codex --only harness,ux-ui,claude-x-codex
```

또는 CLI로 직접 설치합니다:

```bash
codex plugin marketplace add https://github.com/zeriong/because-i-needed.git
codex plugin add harness@because-i-needed
codex plugin add ux-ui@because-i-needed
codex plugin add claude-x-codex@because-i-needed
```

새 Codex 세션에서 `$harness:build`, `$ux-ui:build`, `$ux-ui:build-mobile`, `$claude-x-codex:run`을 호출합니다. 자동 오케스트레이션은 `$claude-x-codex:mode on`, 컨텍스트 점검은 `$claude-x-codex:audit`입니다. 자동 라우팅과 UI 커밋 게이트를 사용하기 전에 `/hooks`에서 설치된 훅을 검토하고 신뢰해야 합니다.

설치 스크립트의 기본 대상은 Claude Code이며, `--host codex`로 Codex를 선택합니다. Codex는 사용자 범위로 설치하므로 `--scope`를 생략하거나 `--scope user`를 사용하세요. project/local 범위는 거부합니다. 스킬·스크립트·작업 절차를 공유하고 플러그인별 Codex 명세를 함께 제공합니다. Codex에서는 자체 질문 도구와 독립 에이전트를 사용합니다. 하네스는 `.codex/hooks.json`, `.codex/hooks/`, `.codex/scripts/review-gate.sh`, `.codex/scripts/latest-model.py`, `.agents/skills/`를 생성하며 기존 Claude 파일을 보존합니다. UI 실측에는 해당 브라우저·모바일 도구가 필요합니다. 자세한 내용은 각 플러그인의 Codex 절을 참고하세요.

각 플러그인의 Codex 절에서 설정 방법을 제공합니다. 작성자·검토자별 모델과 추론 강도를 지정할 수 있고, 설정하지 않은 역할은 현재 세션 제품군의 최신 모델로 실행됩니다. 하네스는 Claude·Codex·양쪽 구성을 생성할 수 있습니다. CXC는 기존 교차 벤더 모델 라우팅을 유지합니다. 브라우저·기기 요건과 훅 신뢰 설정은 여전히 필요합니다.

## 플러그인

### [harness](plugins/harness) · `v1.3.0`

**템플릿이 아니라 사실 기반 분석으로 프로젝트 맞춤 Claude Code·Codex 하네스를 만듭니다.** 레포의 실제 계층·관심사 분리를 직접 읽고, 모든 룰이 내 코드의 `file:line`을 인용하도록 도출한 뒤, `project-rules`, 결정론적 `review-gate.sh`, `UserPromptSubmit` 훅, `harness-engineering` 스킬을 생성합니다.

- **이럴 때** 하네스가 없는 프로젝트에서 Claude Code나 Codex 작업을 시작하거나, 구조가 크게 바뀌어 기존 셋업이 맞지 않을 때.
- **진입점:** `/harness:build` 또는 *"harness 만들어"*

[harness 한국어 README 보기 →](plugins/harness/README.ko.md)

### [ux-ui](plugins/ux-ui) · `v1.4.1`

**웹과 모바일 UI를 실제 렌더 실측으로 만듭니다.** 실제 스크린샷을 캡처하고(웹은 chrome-devtools, React Native / Flutter / iOS / Android는 모바일 MCP 또는 CLI 스냅샷 하네스), 아트 디렉터 에이전트가 그 실측 스냅샷을 비평하게 하며, 정확하고 우아해질 때까지 반복한 뒤, 스테이징된 diff 그대로 APPROVED 되기 전까지 UI의 `git commit`을 막습니다.

- **이럴 때** 컴포넌트·페이지·화면을 만들거나 고칠 때, 상상이 아니라 실제 렌더로 검증받고 싶을 때.
- **진입점:** `/ux-ui:build`(웹) · `/ux-ui:build-mobile`(모바일), 또는 UI를 만들어 달라고 요청
- **참고:** 설치하면 `PreToolUse` 커밋 게이트 훅(모든 `Bash` 호출 전에 실행되며 UI 커밋만 막음)과 MCP 서버 4개가 함께 등록됩니다.

[ux-ui 한국어 README 보기 →](plugins/ux-ui/README.ko.md)

### [claude-x-codex](plugins/claude-x-codex) · `v0.3.1`

**Claude × Codex 동료 오케스트레이션.** 메인 에이전트가 계획하고 모든 관문을 판단하며, 작업을 빠른 Claude 워커나 대량 처리용 Codex 워커에 보내고, 두 벤더가 서로의 작업을 리뷰합니다 — 메인 에이전트 자신의 계획도 포함됩니다. 반론은 한 번이고, 판정은 역할이 아니라 증거가 합니다. 감사 기능이 두 벤더가 같은 프로젝트 지침에서 출발하는지 확인합니다. 비공식 커뮤니티 플러그인입니다.

- **이럴 때** Claude Code와 Codex를 모두 쓰고, 기능의 모든 단계에서 다른 벤더의 리뷰를 받고 싶을 때.
- **진입점:** `/claude-x-codex:run`, 또는 `/claude-x-codex:mode on` 으로 켜 두면 구현 요청이 이 흐름을 거칩니다
- **참고:** 설치하면 `UserPromptSubmit` 훅이 등록됩니다(모든 프롬프트마다 실행되며, 모드가 꺼져 있으면 아무것도 출력하지 않음).

[claude-x-codex 한국어 README 보기 →](plugins/claude-x-codex/README.ko.md)

## 은퇴한 플러그인

### plan-smith — 2026-09-30 은퇴 (마지막 버전 1.8.0)

z-lab에서 plan-smith 1.6.0 파이프라인(Claude Code, 작업 1개)은 같은 모델이 계획과 구현을 맡을 때 순비용이었습니다. 계획만으로도 전체 기본 계획·구현 체인 토큰의 약 1.65배(Fable 5.1, 완료)와 최소 2.41배(Opus 5.5, 중단)를 사용했고, 기본 계획은 첫 시도에 이미 완성됐습니다. 각 수치는 모델별 단일 실행 결과입니다. 절감 효과는 근사 파이프라인에서만 측정했으며, 실제 파이프라인에서 더 약한 구현자의 영향과 계획 품질은 측정하지 않았습니다. [측정 결과](https://github.com/zeriong/z-lab/tree/main/plan-smith-lab/real-skill-tco-1.6.0)와 [은퇴 결정](https://github.com/zeriong/z-lab/tree/main/plan-smith-lab/analyze)을 참고하세요. 마지막 소스(1.8.0)는 이 레포의 git 이력에 남아 있고, 1.4.2 이하 버전은 [zeriong/plan-smith](https://github.com/zeriong/plan-smith)에 있습니다.

설치된 사본을 제거하려면:

- Claude Code: `claude plugin uninstall plan-smith@bin` (project 또는 local 범위로 설치했다면 `--scope project` 또는 `--scope local`을 추가하세요.) <!-- legacy-id -->
- Codex: `codex plugin remove plan-smith@bin` <!-- legacy-id -->

## 설치

설치 스크립트가 플러그인 목록을 보여 주고, 고른 것만 설치합니다:

```bash
curl -fsSL https://raw.githubusercontent.com/zeriong/because-i-needed/main/install.sh | bash
```

↑/↓(또는 j/k)로 이동, space로 선택 전환, `a` 로 전체, enter로 설치, `q` 로 종료 — 처음에는 전부 선택되어 있습니다. 옵션: `--all`, `--only a,b`, `--list`, `--dry-run`, `--scope user|project|local`. 파이프로 실행할 때는 `bash -s --` 뒤에 붙입니다(예: `… | bash -s -- --only harness`). 내부적으로 아래와 같은 `claude plugin` 명령을 실행합니다.

또는 마켓플레이스를 직접 추가하고, 원하는 플러그인을 설치합니다:

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install harness@because-i-needed
claude plugin install ux-ui@because-i-needed
claude plugin install claude-x-codex@because-i-needed
```

또는 Claude Code에서: `/plugin` → Marketplaces → Add Marketplace → `https://github.com/zeriong/because-i-needed.git` 입력 후 목록에서 설치.

또는 `~/.claude/settings.json`에 직접 연결:

```json
{
  "extraKnownMarketplaces": {
    "because-i-needed": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": {
    "harness@because-i-needed": true,
    "ux-ui@because-i-needed": true,
    "claude-x-codex@because-i-needed": true
  }
}
```

### 예전에 `bin`으로 설치했다면

마켓플레이스 이름이 `bin`에서 `because-i-needed`로 바뀌었습니다. 플러그인 이름과 명령은 그대로입니다. 제거한 뒤 위와 같이 다시 설치하세요:

```bash
# Claude Code — 마켓플레이스를 제거하면 그 플러그인도 함께 제거됩니다
claude plugin marketplace remove bin
# Codex — 설치한 플러그인을 먼저 제거하세요. 그러지 않으면 예전 사본이 계속 로드됩니다
codex plugin remove harness@bin
codex plugin remove ux-ui@bin
codex plugin remove claude-x-codex@bin
codex plugin marketplace remove bin
```

예전 ID(`<plugin>@bin`)에 묶인 설정은 옮겨지지 않습니다.

## 네이밍

모든 명령은 **대상 : 동작** 으로 읽힙니다 — `/<플러그인>:<스킬>`.

- **플러그인 = 대상** — 무엇을 다루는가(`harness`, `ux-ui`).
- **스킬 = 동사** — 하나의 공통 어휘에서 고르며, 같은 동사는 모든 플러그인에서 같은 뜻입니다.
- 플러그인은 따로 둡니다. 필요한 것만 설치할 수 있고, 한 플러그인의 훅이나 MCP 서버가 다른 플러그인에 딸려 오지 않습니다.

| 동사 | 의미 |
|---|---|
| `build` | 프로젝트에 산출물(하네스, UI 등)을 만든다 |
| `forge` | 대화 맥락을 정제해 문서(계획 등)를 만든다 |
| `run` | 작업을 실행한다 |
| `mode` | 동작을 켜고 끈다 |
| `audit` | 읽기 전용으로 점검한다 |
| `review` | 결과물을 검토한다 |

현재 `forge`와 `review`를 사용하는 플러그인은 없습니다.

## 레포 구조

```
because-i-needed/
├── .claude-plugin/marketplace.json   # 플러그인 3개 등록
├── install.sh                        # 대화형 설치 스크립트 (--host claude|codex)
└── plugins/
    ├── harness/                      # 스킬
    ├── ux-ui/                        # 스킬 2 + 에이전트 2 + 커밋 게이트 훅 + MCP 4
    └── claude-x-codex/               # 스킬 3 + 프롬프트 훅 + 스크립트 3
```

각 플러그인 폴더는 자기완결적입니다: README, 매니페스트, 배포되는 모든 파일이 `plugins/<이름>/` 아래에 있습니다.

## 언어 정책

- 이 레포의 모든 README — 이 문서와 각 플러그인의 README — 는 **5개 언어**로 제공합니다: `README.md`(영어, 원본), `README.ko.md`(한국어), `README.ja.md`(日本語), `README.zh-CN.md`(简体中文), `README.zh-TW.md`(繁體中文).
- README를 고치면 같은 커밋에서 5개를 모두 갱신합니다. 새 플러그인은 첫 커밋부터 5개 언어를 모두 갖춥니다.
- 번역하는 파일은 README뿐입니다. 그 밖의 모든 파일 — `CLAUDE.md`, `SKILL.md`, `references/*.md`, `agents/*.md`, `CHANGELOG.md`, 훅 메시지 — 은 영어로 씁니다. 사용자가 입력하는 말과 맞아야 하는 트리거 문구는 그 언어 그대로 둡니다.

## 라이선스

MIT. [LICENSE](LICENSE) 참조.
