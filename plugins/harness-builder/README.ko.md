<p align="center">
  <strong>harness-builder</strong>
</p>

<p align="center">
  <strong>템플릿이 아니라, 프로젝트를 실제로 분석해서 만드는 Claude Code 하네스.</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-1.0.0-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a>
</p>

<p align="center">
  <a href="#설치">설치</a> &bull;
  <a href="#무엇을-하는가">무엇을 하는가</a> &bull;
  <a href="#8-phase-워크플로우">워크플로우</a> &bull;
  <a href="#fact-check-루프">Fact-check 루프</a> &bull;
  <a href="#faq">FAQ</a>
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

대부분의 "Claude Code 하네스" 플러그인은 정해진 `.claude/` 뼈대를 찍어내고 끝납니다. 그렇게 강제하는 룰은 *플러그인 저자가* 생각한 룰이지, *내 프로젝트가 실제로 필요로 하는* 룰이 아닙니다.

**harness-builder는 그 순서를 뒤집습니다.** 먼저 프로젝트를 직접 읽고, 그 안에서 룰을 도출한 다음에야 그 *도출된 룰*을 강제하는 하네스를 깝니다. 결과물은 내 repo에 맞춰 재단된 `.claude/` 디렉토리이고, 모든 룰이 내 코드의 `file:line`에 추적 가능합니다.

## 핵심 특징

- **Fact 기반 룰 도출** — 모든 룰은 실제 코드 분석 결과(verdict)에서 나옵니다. `file:line` 인용이 없는 주장은 즉시 폐기됩니다.
- **Gate 우선 강제** — 결정론적으로 검사 가능한 룰은 `review-gate.sh`의 exit code 게이트가 됩니다. 정성적 판단이 필요한 룰은 advisory로 분류되어 매 프롬프트마다 Claude에게 주입됩니다.
- **사이드이펙트 인지 회귀** — 빌드 중 단 한 줄이라도 패치가 적용되면 Phase 1으로 회귀합니다. 한 줄 변경이 이전 verdict들을 무효화할 수 있다는 가정입니다.
- **2-reviewer 교차 검증** — done 선언 전에 Opus 1개 + Sonnet 1개를 병렬로 fresh-spawn하고, 6가지 품질 기준에 대한 JSON 리포트를 메인이 종합합니다.
- **Worse/Better case 인덱싱** — 모든 룰은 `docs/conventions/<rule>.md`로 함께 출력됩니다. 실제 repo의 문제 코드와 개선 형태, 그리고 grep 가능한 키워드 인덱스가 포함됩니다.
- **YAGNI 기본** — 위반 0건 + 사용자 언급 0인 룰은 도입되지 않습니다. 5개 룰로 충분한 프로젝트는 5개 룰 하네스가 정답이지, 실패가 아닙니다.

## 사용해야 할 때

- `.claude/` 셋업이 없는 프로젝트에서 Claude Code 작업을 시작할 때
- 프로젝트 구조가 크게 변경되어 기존 `.claude/`를 다시 빌드해야 할 때
- 추상적인 컨벤션이 아니라 내 repo의 실제 코드에 묶인 룰을 원할 때

**건너뛰어도 될 때:**

- 단일 파일 유틸리티나 1회성 스크립트 — 하네스가 오버킬
- 이미 잘 다듬어진 `.claude/`가 있는 repo
- 계층 구조가 불분명한 repo (fact-check 루프가 잡을 구조가 필요함)

## 설치

### Claude Code 플러그인 마켓플레이스로 설치

1. Claude Code에서 `/plugin` 실행
2. Marketplaces → Add Marketplace
3. URL 입력: `https://github.com/zeriong/because-i-needed.git`
4. `harness-builder` 설치

### 또는 CLI로

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install harness-builder@because-i-needed
```

### 또는 `~/.claude/settings.json`에 직접 추가

```json
{
  "extraKnownMarketplaces": {
    "because-i-needed": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": { "harness-builder@because-i-needed": true }
}
```

## Quick Start

```
cd your-project
# Claude Code에서:
/harness-builder:harness-builder
```

자연어로 요청해도 됩니다 — 트리거 키워드(한/영): `harness 만들어`, `build harness`, `harness 셋업`, `프로젝트 룰 추출`, `review gate 깔아줘`, `harness-builder`.

스킬이 수행하는 일:

1. 4가지 질문 (패키지 매니저, 모노레포 형태, lint/typecheck 명령, 강제하고 싶은 룰)
2. 코드베이스를 직접 읽고 layer마다 fact-check 루프 실행
3. 룰 도출 → gate 스크립트 생성 → hook 배선 → skill 작성 → conventions docs 인덱싱
4. 일부러 위반을 만든 sample diff로 동작 검증
5. 2-reviewer 패널로 최종 점검

전체 실행은 보통 여러 turn에 걸쳐 진행됩니다 — 스킬이 그 점을 정직하게 안내합니다. `/loop`로 감싸는 것도 지원하지만 필수는 아닙니다.

## 무엇을 하는가

프로젝트 루트에 다음을 생성:

```
.claude/
├── settings.json                    # UserPromptSubmit hook 배선
├── hooks/inject-context.sh          # 매 프롬프트마다 project-rules + harness-engineering 주입
├── scripts/review-gate.sh           # 결정론적 게이트 — exit 0 / 1 / 2
└── skills/
    ├── project-rules/SKILL.md       # 내 코드에서 도출된 룰 (Phase 1–2 결과)
    └── harness-engineering/SKILL.md # 이후 모든 task에 적용되는 11-phase 워크플로우

docs/conventions/
├── <rule-1>.md                      # worse case + better case (내 repo 실제 코드) + 키워드 인덱스
├── <rule-2>.md
└── ...
```

빌드 후, 프로젝트 내 모든 user prompt가 자동으로 `project-rules` + harness phase를 로드합니다. 프론트엔드 코드? 도출된 layer-separation 룰이 발사됩니다. 300줄 컴포넌트 편집? 도출된 file-length cap이 블록합니다. 룰은 플러그인 것이 아니라 *내 프로젝트* 것입니다.

플러그인 자체는 스킬 하나만 담고 있습니다: [`skills/harness-builder/SKILL.md`](skills/harness-builder/SKILL.md) — 아래의 8-phase 빌드.

## 8-Phase 워크플로우

| Phase | 책임 | Fact-check 루프 필수 |
|-------|------|---------------------|
| 0 | **Intake** — 패키지 매니저, 모노레포 형태, 기존 스크립트, 사용자 권고 룰 | — |
| 1 | **Layer / Concern Reconnaissance** — 모든 claim에 `file:line` 인용 강제 | ✅ 절대 |
| 2 | **Convention Extraction** — Phase 1 verdict → 룰 도출 | ✅ |
| 3 | **`docs/conventions/<rule>.md`** — 실제 repo 코드 인용 기반 worse / better case | ✅ |
| 4 | **Gate script** (`review-gate.sh`) 생성 | — |
| 5 | **Hook 배선** (`UserPromptSubmit`) | — |
| 6 | **Skill 본문** (`project-rules` + `harness-engineering`) | — |
| 7 | **Self-verification** — sample diff로 게이트 통과 확인 | — |
| 8 | **Review gate** — Opus + Sonnet 1-shot review, 메인이 종합 후 패치 | — |

**Phase 8에서 패치가 1줄이라도 적용되면 Phase 1으로 회귀합니다.** 휴리스틱이 아니라 절대 법령입니다 — side-effect로 이전 verdict들이 무효화될 수 있다는 가정. 회귀 cap은 3이고, 그 안에 수렴 못 하면 진실된 실패 보고서를 출력하고 사용자 결정을 기다립니다.

## Fact-check 루프

스킬에서 가장 중요한 규칙입니다. Phase 1이 내 코드에 대해 하는 모든 주장은 다음을 통과해야 합니다:

```
주장:        "src/components/admin/audit-logs/page.tsx는 presentation만 가진다"
              ↓
자기 의심:    "정말 그런가? 검증하자."
              ↓
직접 읽기:    Read tool로 파일 직접 열기 — 추론/기억 금지
              ↓
스코프 sweep: 같은 디렉토리에 grep "useState|useEffect|fetch"
              ↓
사이드이펙트: grep -r로 import 그래프 조사
              ↓
SRP 테스트:   변화 이유가 정확히 하나인가?
              ↓
Verdict:      "presentation + data 혼재 — page.tsx:24-31에서 fetch() 호출"
              + file:line 인용
              ↓
다음 phase 진행
```

단계를 건너뛴 claim은 **폐기**되고 Phase 1이 재시작됩니다. 이 루프가 있어야만 도출된 룰을 신뢰할 수 있습니다 — 모델의 직관이 아니라 repo의 검증 가능한 사실에서 나오기 때문입니다.

## "퀄리티 높음"의 정의

스킬이 적용 후보로 검토하는 모든 패치는 6가지 축으로 self-grade(0–5점) 됩니다:

| 축 | 의미 |
|----|------|
| **SRP** | 모듈당 변화 이유 하나 |
| **주석 간결성** | 개조식, 핵심만, 2줄 이내 |
| **KISS** | 문제를 해결하는 가장 단순한 형태 |
| **DRY** | 모듈 간 중복 로직 없음 |
| **YAGNI** | 추측성 기능/룰 도입 금지 |
| **인지 용이성** | 사람이 노력 없이 읽힘 |

평균 3.5 미만 패치는 reject. reject가 잦으면 해당 phase가 회귀합니다.

## 하네스 우회

빌드 후 모든 user prompt가 주입 hook을 발사합니다. 특정 턴만 우회하고 싶다면:

- 프롬프트 앞에 `!` 접두 (예: `!그냥 답만 해줘`)
- 또는 등록된 우회 문구(한/영): `harness 빼고`, `without harness`, `skip harness`, `no harness`

우회 모드는 그 turn의 phase 강제만 비활성화하고 project-rules는 계속 보여줍니다.

## FAQ

**왜 그냥 `.claude/` 템플릿을 주지 않나요?**
템플릿은 *다른 사람의* 룰을 강제할 뿐입니다. 이 스킬의 핵심은 *내 프로젝트의* 룰을 — 실제 코드에서 도출해서 — 강제하는 것입니다. 내 코드의 200-LOC 컴포넌트는 남의 코드의 200-LOC 컴포넌트와 같은 의미가 아닙니다. cap은 내 것에서 와야 합니다.

**린터 / ESLint와 뭐가 다른가요?**
린터는 문법과 알려진 안티패턴을 잡습니다. 이 스킬은 린터가 잘 모델링하지 못하는 구조적 관심사(layer 분리, SRP, 파일 길이, 네이밍)를 잡고, 각 룰을 내 repo의 `file:line`과 연결해 위반에 맥락을 줍니다. 대체재가 아니라 상호 보완재입니다.

**왜 reviewer가 5개가 아니라 2개인가요?**
이 스킬의 기반이 된 setup-guide는 2 Opus + 3 Sonnet 5-agent 패널을 씁니다. 빌드 마지막의 1회성 review에는 over-engineering이에요 — 3~5번 agent의 한계 효용이 latency 비용을 정당화하지 못합니다. Opus 1개 + Sonnet 1개로 모델 다양성 이득의 대부분을 1/5 비용에 캡쳐합니다.

**Phase 1이 내 프로젝트가 이미 완벽하게 layered 되어있다고 판정하면?**
그러면 layer-separation 룰은 도입되지 않습니다. YAGNI가 적용됩니다 — 위반 0 + 사용자 언급 0인 룰은 도입 금지. 내 유일한 관심사가 네이밍이라면 룰이 1개인 하네스를 받습니다.

**빌드 후 생성된 `.claude/`를 수정해도 되나요?**
네. 출력물은 내 것입니다. 스킬은 생성 파일을 추적하지 않고 재동기화하지 않습니다. `/harness-builder:harness-builder`를 재실행하면 merge는 직접 처리해야 합니다.

**프론트엔드가 아닌 프로젝트에서도 동작하나요?**
Phase 1의 layer 신호는 프론트엔드 repo (`*.tsx`, `use-*.ts`, `api/*`) 기준으로 튜닝되어 있습니다. Go 서비스나 Python 백엔드라면 다른 layer-identification 신호가 필요한데, 그게 Phase 0의 free-text 질문이 존재하는 이유입니다. 스킬의 *워크플로우*는 프로젝트 비종속이고, Phase 1의 휴리스틱만 튜닝된 상태입니다.

## 요구사항

- `git`, `jq`, `bash 4+`
- 대상 프로젝트가 git work tree
- 플러그인을 지원하는 Claude Code

## 라이선스

MIT. [LICENSE](../../LICENSE) 참조.

## Acknowledgments

8-phase 워크플로우는 저자가 작성한 비공개 하네스 setup-guide와 research-foundation에서 파생되었습니다. Fact-check 루프 패턴은 CRITIC (Gou et al. 2023) 및 Anthropic Multi-Agent Research System 엔지니어링 블로그의 영향을 받았습니다. 회귀 cap (= 3)은 Reflexion (Shinn et al. 2023)에서 가져왔습니다.
