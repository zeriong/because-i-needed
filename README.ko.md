<p align="center">
  <strong>because-i-needed</strong>
</p>

<p align="center">
  <strong>필요해서 만든 Claude Code 플러그인 모음 — 플래닝, 프로젝트 하네스, 실측 기반 UI.</strong>
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

이 레포는 독립된 플러그인 3개를 담은 Claude Code **플러그인 마켓플레이스**입니다. 필요한 것만 골라 설치하면 됩니다.

## 플러그인

### [plan-smith](plugins/plan-smith) · `v1.4.2`

**2단 파이프라인으로 플랜을 벼립니다.** 메인 에이전트가 대화 전체를 컨텍스트 패킷(목표, 하드 제약, 기각된 대안)으로 증류해 사용자에게 확인받고, 깨끗한 컨텍스트의 `plan-writer` 에이전트가 추론 프레임 라이브러리와 검증된 집필 스타일로 플랜을 쓴 뒤, 그 플랜을 요약 없이 원문 그대로 전달합니다 — 요약 손실도, 컨텍스트 오염도 없습니다.

- **이럴 때** 마이그레이션, 런칭, build-out처럼 길고 잡음 많은 세션에서 플랜이 흐려지기 쉬운 작업의 계획이 필요할 때.
- **진입점:** `/plan-smith:plan-smith <태스크>` 또는 *"… 플랜 짜줘"*

[plan-smith 한국어 README 보기 →](plugins/plan-smith/README.ko.md)

### [harness-builder](plugins/harness-builder) · `v1.0.0`

**템플릿이 아니라 사실 기반 분석으로 프로젝트 맞춤 Claude Code 하네스를 만듭니다.** 레포의 실제 계층·관심사 분리를 직접 읽고, 모든 룰이 내 코드의 `file:line`을 인용하도록 도출한 뒤, `project-rules`, 결정론적 `review-gate.sh`, `UserPromptSubmit` 훅, `harness-engineering` 스킬을 생성합니다.

- **이럴 때** `.claude/` 셋업이 없는 프로젝트에서 Claude Code 작업을 시작하거나, 구조가 크게 바뀌어 기존 셋업이 맞지 않을 때.
- **진입점:** `/harness-builder:harness-builder` 또는 *"harness 만들어"*

[harness-builder 한국어 README 보기 →](plugins/harness-builder/README.ko.md)

### [ux-ui-builder](plugins/ux-ui-builder) · `v1.1.0`

**웹과 모바일 UI를 실제 렌더 실측으로 만듭니다.** 실제 스크린샷을 캡처하고(웹은 chrome-devtools, React Native / Flutter / iOS / Android는 모바일 MCP 또는 CLI 스냅샷 하네스), 아트 디렉터 에이전트가 그 실측 스냅샷을 비평하게 하며, 정확하고 우아해질 때까지 반복한 뒤, 스테이징된 diff 그대로 APPROVED 되기 전까지 UI의 `git commit`을 막습니다.

- **이럴 때** 컴포넌트·페이지·화면을 만들거나 고칠 때, 상상이 아니라 실제 렌더로 검증받고 싶을 때.
- **진입점:** `/ux-ui-builder:ux-ui-builder`(웹) · `/ux-ui-builder:ux-ui-builder-mobile`(모바일), 또는 UI를 만들어 달라고 요청
- **참고:** 설치하면 `PreToolUse` 커밋 게이트 훅(모든 `Bash` 호출 전에 실행되며 UI 커밋만 막음)과 MCP 서버 4개가 함께 등록됩니다.

[ux-ui-builder 한국어 README 보기 →](plugins/ux-ui-builder/README.ko.md)

## 설치

마켓플레이스를 한 번 추가하고, 원하는 플러그인을 설치합니다:

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install plan-smith@because-i-needed
claude plugin install harness-builder@because-i-needed
claude plugin install ux-ui-builder@because-i-needed
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
    "plan-smith@because-i-needed": true,
    "harness-builder@because-i-needed": true,
    "ux-ui-builder@because-i-needed": true
  }
}
```

## 레포 구조

```
because-i-needed/
├── .claude-plugin/marketplace.json   # 플러그인 3개 등록
└── plugins/
    ├── plan-smith/                   # 스킬 + plan-writer 에이전트 (+ CHANGELOG.md)
    ├── harness-builder/              # 스킬
    └── ux-ui-builder/                # 스킬 2 + 에이전트 2 + 커밋 게이트 훅 + MCP 4
```

각 플러그인 폴더는 자기완결적입니다: README, 매니페스트, 배포되는 모든 파일이 `plugins/<이름>/` 아래에 있습니다.

## 언어 정책

- 이 레포의 모든 README — 이 문서와 각 플러그인의 README — 는 **5개 언어**로 제공합니다: `README.md`(영어, 원본), `README.ko.md`(한국어), `README.ja.md`(日本語), `README.zh-CN.md`(简体中文), `README.zh-TW.md`(繁體中文).
- README를 고치면 같은 커밋에서 5개를 모두 갱신합니다. 새 플러그인은 첫 커밋부터 5개 언어를 모두 갖춥니다.
- Claude가 직접 읽는 파일 — `SKILL.md`, `references/*.md`, `agents/*.md` — 은 영어로 유지합니다.

## 라이선스

MIT. [LICENSE](LICENSE) 참조.
