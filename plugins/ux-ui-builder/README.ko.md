<p align="center">
  <strong>ux-ui-builder</strong>
</p>

<p align="center">
  <strong>스튜디오가 UI를 출시하듯 웹과 모바일 UI를 만든다 — 실제 렌더를 실측하고, 아트 디렉터가 비평하고, 커밋에서 강제한다.</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-1.1.0-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a>
</p>

<p align="center">
  <a href="#설치">설치</a> &bull;
  <a href="#무엇을-하는가">무엇을 하는가</a> &bull;
  <a href="#루프">루프</a> &bull;
  <a href="#모바일-측정-백엔드">모바일 백엔드</a> &bull;
  <a href="#커밋-게이트">커밋 게이트</a> &bull;
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

에이전트는 상상으로 UI를 만들면 반드시 틀린다 — 보이지 않는 overflow, 사라진 focus ring, 처리되지 않은 empty 상태, 라벨에 새어 나온 raw UUID. 이런 것들은 **실제 렌더를 보기 전까지** 드러나지 않는다.

**ux-ui-builder는 루프에서 상상을 제거한다.** 모든 UI 변경은 실제 렌더에서 실측되고 — 웹은 chrome-devtools로 브라우저 페이지를, 모바일은 실제 기기/시뮬레이터를 — 아트 디렉터 에이전트가 그 *실측* 스냅샷을 기준으로 비평하며, 정확하고 우아해질 때까지 반복된 뒤 하드 게이트로 막힌다: 아트 디렉터가 **정확히 스테이징된 diff에 대해** APPROVED 하지 않은 UI는 커밋할 수 없다.

## 특징

- **실측만, 상상 금지** — 스킬이 번들된 **chrome-devtools MCP**를 몰아 실제 렌더를 캡처한다: default / hover / focus / loading / empty / error / long-content 를 mobile / tablet / desktop 에 걸쳐, DOM·a11y 스냅샷과 콘솔·네트워크 신호, Lighthouse 감사까지.
- **모바일도** *(1.1 신규)* — 두 번째 스킬 `ux-ui-builder-mobile`이 앱의 스택(React Native / Expo / Flutter / 네이티브 iOS / 네이티브 Android / 모바일 웹)을 감지하고, 부팅된 기기·시뮬레이터에서 **실제 픽셀**을 돌려주는 측정 백엔드를 골라 device × orientation × state 매트릭스를 캡처한다. 스택을 스크린샷할 MCP가 없으면 번들된 **CLI 스냅샷 하네스**(`simctl` / `adb`)가 대신한다.
- **아트 디렉터 하드 게이트** — `ux-ui-art-director` 에이전트(Opus)는 실측 아티팩트만 비평한다. 모바일은 `ux-ui-mobile-art-director`가 플랫폼 관례(Apple HIG / Material) 기준으로 판정한다. critical/major 결함이 하나라도 있으면 `CHANGES_REQUIRED`. 필요한 상태는 직접 재측정할 수 있지만(모바일 디렉터는 MCP가 되는 스택에서만 — CLI 하네스 전용 스택에서는 캡처를 요구한다), 코드는 수정하지 않는다(리뷰어/구현자 분리).
- **diff에 묶인 승인** — 승인은 스테이징된 UI diff의 sha256에 바인딩된다. UI를 다시 수정하면 해시가 바뀌어 게이트가 다시 막는다. "한 번 승인받고 계속 수정"은 구조적으로 불가능하며, 낡거나 위조된 승인이 없다.
- **자율 반복** — build → measure → critique → fix → re-measure 를 최대 3회, 사용자 추가 지시 없이 수행. 첫 커밋부터 우아한 프론트엔드. (모바일 루프는 시작할 때 측정 백엔드 확인을 위해 한 번만 멈춘다.)
- **Zero-config** — 브라우저·모바일 MCP를 스스로 번들하고 정확성·우아함 기준을 자체적으로 지녀, 설정이 전혀 없는 프로젝트에서도 동작한다. 호스트 프로젝트가 디자인 규칙을 정의했다면 그쪽이 우선한다.
- **보수적 blast radius** — 게이트는 진짜 UI 파일 유형에만 발동한다: 웹(`.tsx .jsx .vue .svelte .astro .css .scss .sass .less .html`)과 모바일(`.swift .kt .dart .storyboard .xib`, Android `res/layout*/**/*.xml`). 순수 `.ts`/`.js`/`.java`와 레이아웃이 아닌 `.xml`은 제외되어 백엔드 전용 커밋은 절대 막지 않는다.

## 설치

### Claude Code 플러그인 마켓플레이스 경유

1. Claude Code에서 `/plugin` 실행.
2. Marketplaces → Add Marketplace.
3. URL 입력: `https://github.com/zeriong/because-i-needed.git` (또는 이 repo의 로컬 경로).
4. `ux-ui-builder` 설치.

### 또는 CLI로

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git   # 또는 로컬 경로
claude plugin install ux-ui-builder@because-i-needed
```

### 또는 `~/.claude/settings.json`에 직접 연결

```json
{
  "extraKnownMarketplaces": {
    "because-i-needed": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": { "ux-ui-builder@because-i-needed": true }
}
```

설치하면 모든 것이 자동 등록된다: MCP 서버 4개(`chrome-devtools`, `mobile-mcp`, `ios-simulator`, `flutter`), 커밋 게이트 훅, `ux-ui-art-director`·`ux-ui-mobile-art-director` 에이전트, `ux-ui-builder`·`ux-ui-builder-mobile` 스킬.

## 요구 사항

- **웹**: **Node.js**(번들된 `chrome-devtools-mcp`가 `npx`로 실행됨), 로컬 **Chrome**, UI를 만들 프로젝트의 실행 가능한 **개발 서버**.
- **모바일**: 스택별 플랫폼 SDK — Xcode + 시뮬레이터(iOS, macOS 전용), Android SDK + 에뮬레이터, 또는 Flutter SDK — 및 부팅된 기기/시뮬레이터에서 실행 중인 앱. 모바일 MCP(`@mobilenext/mobile-mcp`, `ios-simulator-mcp`, `dart mcp-server`)는 해당 도구가 설치된 환경에서만 기동하며, `mobile-snapshot.sh` 하네스는 `simctl`/`adb`만 있으면 된다.
- **git** 워크트리, 그리고 `shasum`/`sha256sum`(macOS/Linux 기본 제공).

## 빠른 시작

```
cd your-project
# Claude Code에서 UI를 만들면 된다. 화면을 구현/변경할 때:
/ux-ui-builder:ux-ui-builder          # 웹
/ux-ui-builder:ux-ui-builder-mobile   # 모바일 (RN / Flutter / iOS / Android / 모바일 웹)
```

컴포넌트·페이지·화면·폼·시트·리스트·레이아웃을 만들거나 고치거나 다시 디자인해 달라고 하면 두 스킬 모두 알아서 트리거된다.

웹 스킬은 다음을 수행한다:

1. 브라우저 MCP와 개발 서버 자가 점검(필요 시 서버 기동).
2. 이 feature만을 위한 디자인 의도 수립(템플릿 기본값 회피).
3. UI 구현.
4. state × breakpoint 매트릭스에 걸쳐 실제 렌더 실측.
5. 실측물을 아트 디렉터에게 넘겨 비평.
6. `APPROVED`가 나올 때까지 수정·재측정(cap = 3).
7. 커밋을 여는 승인 아티팩트 기록.

모바일 스킬도 같은 루프를 돌지만, 1단계에서 먼저 스택을 감지하고 하네스 `doctor`를 실행한 뒤 측정 백엔드를 사용자에게 확인받으며(유일한 대화형 정지), 4단계에서는 부팅된 대상에서 device × orientation × state 매트릭스를 실측한다.

승인이 없는 UI를 커밋하려 하면 게이트가 막고 루프를 돌리라고 알려준다.

## 무엇을 하는가

```
your-project/
└── .ux-ui/
    ├── measure/<feature>/        # 스크린샷, snapshots.md, signals.md, context.md
    └── approvals/<diff-hash>.json # 커밋 게이트가 확인하는 APPROVED 아티팩트
```

플러그인 자체 구성:

```
plugins/ux-ui-builder/
├── .claude-plugin/plugin.json          # 매니페스트 + 번들 MCP(chrome-devtools, mobile-mcp, ios-simulator, flutter)
├── hooks/hooks.json                    # PreToolUse → 커밋 게이트
├── scripts/
│   ├── ui-commit-gate.sh               # 게이트: hash | approve <feature> [dir] | hook-block (웹 + 모바일 유형)
│   └── mobile-snapshot.sh              # CLI 스냅샷 하네스: doctor | capture <ios|android> <dir> <label>
├── agents/
│   ├── ux-ui-art-director.md           # 웹 아트 디렉터(실측 + 비평, Opus)
│   └── ux-ui-mobile-art-director.md    # 모바일 아트 디렉터(HIG / Material 관례, Opus)
└── skills/
    ├── ux-ui-builder/                  # 웹: measure → critique → iterate → gate
    │   ├── SKILL.md
    │   └── references/
    │       ├── design-principles.md    # 정확성 + 우아함 기준(자립형)
    │       ├── measurement-protocol.md # 정확한 chrome-devtools 캡처 절차
    │       └── review-rubric.md        # verdict 형식 + APPROVED 아티팩트 계약
    └── ux-ui-builder-mobile/           # 모바일: detect → measure → critique → iterate → gate
        ├── SKILL.md
        └── references/
            ├── backend-detection.md          # 스택 감지 + 실제 픽셀 백엔드 선택
            ├── mobile-design-principles.md   # HIG / Material, safe area, 탭 타깃, 제스처, 키보드, 다크 모드
            ├── mobile-measurement-protocol.md # 백엔드별 캡처(device × orientation × state)
            └── mobile-review-rubric.md       # verdict 형식 + APPROVED 아티팩트 계약
```

## 루프

| 단계 | 책임 |
|------|------|
| 0 | **Bootstrap** — 브라우저 MCP + 개발 서버 확인; feature slug 선택. *모바일:* 스택 감지, `mobile-snapshot.sh doctor` 실행, 백엔드를 사용자와 확정, 부팅된 대상에서 앱 실행 확인 |
| 1 | **Plan** — *이* feature를 위한 압축된 디자인 의도; AI 기본값 회피(모바일: 플랫폼 관례 안에서) |
| 2 | **Build** — 기존 컴포넌트/토큰 재사용하여 구현 |
| 3 | **Measure** — 실제 state × breakpoint 매트릭스 + 감사 캡처(모바일: device × orientation × state) — 필수 |
| 4 | **Critique** — 실측물로 `ux-ui-art-director`(웹) 또는 `ux-ui-mobile-art-director`(모바일) 스폰(하드 게이트) |
| 5 | **Iterate** — 수정 적용, 3단계로 복귀, 재심(cap = 3) |
| 6 | **Record approval** — APPROVED 시에만; 이 정확한 diff에 대해 커밋 해제 |

실측은 선택이 아니고 위조도 불가하다. **스크린샷 없음 → 리뷰 없음 → 커밋 없음.**

## 모바일 측정 백엔드

모든 모바일 스택에는 실제 픽셀로 가는 경로가 있다. 스킬은 스크린샷과 a11y/view 트리를 모두 주는 MCP를 먼저, 그다음 스크린샷만 주는 MCP를, 마지막으로 CLI 하네스를 고른다:

| 감지된 스택 | 우선 백엔드 | 스크린샷 | A11y / 구조 |
|-------------|-------------|----------|-------------|
| 모바일 웹 | `chrome-devtools` MCP(번들) | `take_screenshot` + `emulate`/`resize_page` | `take_snapshot` |
| Flutter | `flutter` MCP(`dart mcp-server`) | 스크린샷 도구 | 위젯 트리 + 핫 리로드 |
| 네이티브 iOS | `ios-simulator` MCP(idb, macOS 전용) | `screenshot` / `ui_view` | `ui_describe_all` |
| React Native | **CLI 스냅샷 하네스**(기본; `mobile-mcp`는 대안으로 제시) | `mobile-snapshot.sh capture …` | `adb uiautomator dump`(Android); 픽셀만(iOS) |
| 네이티브 Android / 크로스플랫폼 | `mobile-mcp` MCP | `mobile_take_screenshot` | `mobile_list_elements_on_screen` |
| 어떤 스택이든, 동작하는 MCP 없음 | **CLI 스냅샷 하네스** | `mobile-snapshot.sh capture …` | `adb uiautomator dump`(Android); 픽셀만(iOS) |

전체 규칙과 동점 처리: [`backend-detection.md`](skills/ux-ui-builder-mobile/references/backend-detection.md).

## 커밋 게이트

`PreToolUse` 훅이 모든 `Bash` 호출 전에 `ui-commit-gate.sh`를 실행한다:

1. `git commit`이 아니면 통과(fast path).
2. 스테이징된 UI 파일이 없으면 통과.
3. UI 커밋이면 스테이징된 UI diff의 sha256을 계산하고
   `.ux-ui/approvals/<hash>.json`에서 `verdict: APPROVED`를 찾는다.
4. 있으면 통과. 없으면 **exit 2**로 커밋을 막고 루프를 돌리라고 안내.

승인이 diff 해시에 묶여 있으므로 이후 UI 수정은 무효화된다 — 게이트는 위조 불가하고 절대 낡지 않는다. 웹과 모바일 UI는 같은 게이트를 공유한다.

무엇을 UI로 볼지는 `UX_UI_GLOBS` 환경변수로 재정의한다. 아티팩트는 `.ux-ui/` 아래에 있으니 커밋하고 싶지 않으면 `.gitignore`에 추가한다.

## FAQ

**모델이 스스로 찍은 스크린샷을 눈대중하게 두면 안 되나?**
"한 번 찍었다"는 규율이 아니다. 이 플러그인은 전체 state × breakpoint 매트릭스, a11y 스냅샷, 콘솔·네트워크·Lighthouse 신호를 *강제*한 뒤, 독립된 아트 디렉터 에이전트가 그 아티팩트를 승인할 때까지 커밋을 막는다. 분위기가 아니라 강제다.

**브라우저 자동화를 커스텀 MCP로 다시 만드나?**
아니다. 브라우저 자동화는 이미 `chrome-devtools-mcp`로 존재하며, 이 플러그인이 그것을 번들한다(모바일 MCP도 마찬가지). 부가가치는 *오케스트레이션과 강제* — measure → critique → iterate → gate — 이고, 이는 스킬 + 에이전트 + 훅에 있다. MCP 서버는 Claude Code 서브에이전트를 스폰하거나 리뷰 루프를 몰 수 없기 때문이다.

**왜 메인 모델이 아니라 아트 디렉터인가?**
분리 때문이다. 구현 에이전트는 자기 작업에 애착이 있다. 실측물만 보고, 코드를 수정하지 못하는 새 에이전트가, 구현자가 합리화해 넘긴 것을 잡아낸다. 스튜디오에 리뷰 단계가 있는 이유와 같다.

**백엔드 커밋도 막히나?**
아니다. 게이트는 UI 파일 유형에만 발동하고 순수 `.ts`/`.js`/`.java`와 레이아웃이 아닌 `.xml`은 의도적으로 제외한다. 백엔드 전용 커밋은 그대로 통과한다.

**한 번 승인받고 계속 수정할 수 있나?**
아니다 — 그게 핵심이다. 승인은 스테이징된 UI diff 해시에 묶인다. UI를 한 줄만 바꿔도 해시가 어긋나므로, 루프를 다시 돌리기 전까지 게이트가 다시 막는다.

**내 모바일 스택을 스크린샷할 수 있는 MCP가 없다면?**
CLI 스냅샷 하네스(`mobile-snapshot.sh`)가 `simctl`/`adb`로 시뮬레이터·에뮬레이터에서 실제 PNG를 바로 캡처하고, 아트 디렉터는 그것을 리뷰한다. 상상한 상태를 리뷰하는 일만은 절대 없다.

**개발 서버, Chrome, 부팅된 기기에 접근 못 하면?**
상상 상태 리뷰로 폴백하지 않고 멈춰서 알려준다. 깨진 환경은 설계상 하드 스톱이다.

## 라이선스

MIT. [LICENSE](../../LICENSE) 참조.

## 감사의 말

measure-then-critique 규율은 `frontend-design` 스킬(미학 방향)과 `chrome-devtools-mcp` 플러그인(브라우저 실측)에 기반한다. 하드 게이트와 diff-바인딩 승인 패턴은 저자의 harness-engineering 작업의 review-gate 설계를 따른다.
