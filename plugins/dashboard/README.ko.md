<p align="center"><strong>dashboard</strong></p>

<p align="center"><strong>Claude Code</strong>와 <strong>Codex CLI</strong>에서만 동작합니다.</p>

<p align="center"><strong>켜 둔 because-i-needed 모드와 각 값의 출처를 한 줄로 모두 확인합니다.</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.2.0-blue" alt="버전"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="라이선스: MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code 플러그인"></a></p>

<p align="center"><a href="#표시되는-내용">표시되는 내용</a> &bull; <a href="#claude-code">Claude Code</a> &bull; <a href="#codex">Codex</a> &bull; <a href="#플러그인이-참여하는-방법">플러그인이 참여하는 방법</a> &bull; <a href="#한계와-상태">한계와 상태</a> &bull; <a href="#설치">설치</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub><a href="../../README.ko.md">because-i-needed</a>의 일부</sub></p>

---

because-i-needed 플러그인에는 프로젝트나 사용자 수준에서 계속 유지되는 스위치가 있습니다 — peer-coding의 오케스트레이션 모드, free-hands 목표, budget 임계값 등입니다. dashboard는 이를 모두 보여 주므로, 모르는 사이에 스위치가 켜져 있는 일이 없습니다.

## 표시되는 내용

```
────────────────────────────────────────────────────────────────────────────────────────────────
💰budget: 80% · 5h now 24%   🙌free-hands: active 0/40 · 1 open (project) · owner lab-sess   🤝peer-coding: on (project)
```

- 흐린 구분선 아래에 활성화된 because-i-needed 플러그인이 선언한 스위치마다 `{icon}label: value` 항목 하나가 나옵니다. 그 값을 정한 수준이 프로젝트나 환경 변수일 때는 `(project)` 또는 `(env)`가, 마지막으로 측정한 사용량 창이나 목표의 소유 세션 같은 세부 정보가 함께 표시됩니다. 터미널이 좁으면 항목이 한 줄에 하나씩 줄바꿈됩니다.
- 활성화된 플러그인 중 스위치를 선언한 것이 없으면 아무것도 표시하지 않습니다.
- `/dashboard:audit`(Claude Code) 또는 `$dashboard:audit`(Codex)는 같은 줄을 출력하고, 스위치마다 프로젝트 수준과 전역 수준에 설정된 값을 보여 줍니다. 아무것도 바꾸지 않습니다.

## Claude Code

이 줄은 프롬프트 위에 표시됩니다. 세션이 시작될 때, 매 차례 뒤, 사용량 창이 움직일 때 갱신됩니다. dashboard는 Claude Code에 설치되어 활성화된 because-i-needed 플러그인을 찾아냅니다.

## Codex

Codex는 플러그인이 그릴 자리를 주지 않으므로, Codex에서 dashboard는 `$dashboard:audit` 명령입니다. 사용량 창을 계속 보려면 `~/.codex/config.toml`(또는 `/statusline`)에서 Codex 자체의 상태 줄 항목을 켜세요.

```toml
[tui]
status_line = ["model-with-reasoning", "weekly-limit"]
```

이 항목은 사용한 양이 아니라 7일 창에서 **남은** 양을 보여 줍니다(예: `weekly 28% left`). 알 수 없는 항목 id는 경고와 함께 무시됩니다.

## 플러그인이 참여하는 방법

플러그인은 루트의 `dashboard.json`에 스위치를 선언합니다. `mode` 스킬이 있는 because-i-needed 플러그인은 반드시 선언해야 하고, 그 밖의 플러그인은 선택입니다(이 레포의 Rule 11).

```json
{ "entries": [ { "label": "peer-coding", "icon": "🤝", "status": ["bash", "scripts/mode.sh", "status", "--json"] } ] }
```

`icon`은 이름 앞에 붙는 이모지 하나입니다(없으면 `🔹`). `status` 명령은 읽기 전용이며 프로젝트 디렉터리에서 실행되고 JSON 객체 하나를 출력합니다. 필드는 `value`, `source`(`env`, `project`, `global`, `default` 중 하나), `project`와 `global`(각 수준의 값, 없으면 `null`), 그리고 선택 사항인 `detail`입니다. 실패하거나, 2초를 넘기거나, 다른 것을 출력하는 명령은 `error`로 표시됩니다. 나중에 추가된 플러그인은 dashboard 릴리스 없이도 나타납니다.

`claude --plugin-dir`로 폴더에서 로드한 플러그인은 Claude Code의 설치 기록에 없습니다. 이를 표시하려면 해당 폴더를 `BECAUSE_I_NEEDED_PLUGIN_DIRS`에 나열하세요(`PATH`와 같은 방식으로 구분).

## 한계와 상태

Claude Code 2.1.299와 Codex 0.162.1에서 사례별 1회씩 측정했습니다([z-lab `dashboard-lab/run-0.1.0`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab/run-0.1.0). Codex 상태 줄은 [`codex-status-line-0.162.1`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab/codex-status-line-0.162.1)에 있습니다).

- Claude Code에서는 위쪽 줄에 budget, free-hands, peer-coding이 표시됐고 `/dashboard:audit`이 각 수준을 출력했습니다. 선언한 플러그인이 없으면 줄이 없었습니다(D01–D03).
- Codex에서는 `$dashboard:audit`이 설치된 플러그인에서 같은 항목을 출력했고, budget 항목에는 7일 창이 나왔습니다. 선언한 플러그인이 없으면 그렇다고 알렸습니다(D04–D05).
- Codex의 `weekly-limit` 항목은 `weekly 28% left`를 보여 줬습니다(C02).
- 0.2.0부터([`run-0.2.0`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab/run-0.2.0), Claude Code 2.1.300): 200칸에서는 구분선과 `{icon}label: value` 항목이 한 줄에 나왔고, 80칸에서는 항목이 잘리지 않고 한 줄에 하나씩 줄바꿈됐습니다. Codex의 audit도 같은 항목을 출력했습니다(D06–D08).

측정하지 않은 항목: tmux 이외의 터미널, 굵게·흐리게 표시되는 스타일; Claude Code 마켓플레이스로 설치한 플러그인(측정한 줄은 `--plugin-dir` 폴더를 읽었고, 설치 기록은 단위 테스트만 수행); 세션 도중 스위치가 바뀐 뒤의 줄 갱신; 데스크톱과 IDE 화면.

줄을 그리는 Claude Code의 플러그인 훅 모듈 API는 얼리 액세스로 표시되어 있으며 릴리스 사이에 바뀔 수 있습니다.

## 설치

먼저 마켓플레이스를 추가한 뒤 플러그인을 설치합니다.

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install dashboard@because-i-needed
```

Codex는 [마켓플레이스 안내](../../README.ko.md#codex)를 참고하세요. `python3`가 `PATH`에 있어야 합니다.

## 라이선스

MIT. [LICENSE](../../LICENSE)를 참고하세요.
