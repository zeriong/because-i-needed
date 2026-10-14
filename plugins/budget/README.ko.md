<p align="center"><strong>budget</strong></p>

<p align="center"><strong>Claude Code</strong>와 <strong>Codex CLI</strong>에서만 동작합니다.</p>

<p align="center"><strong>사용량 창의 비율을 정해 두면, 그 비율에 도달했을 때 실행 중인 모든 세션이 멈추고 계속할지 묻습니다.</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.1.0-blue" alt="버전"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="라이선스: MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code 플러그인"></a></p>

<p align="center"><a href="#시작하기">시작하기</a> &bull; <a href="#동작-방식">동작 방식</a> &bull; <a href="#설정과-상태">설정과 상태</a> &bull; <a href="#한계와-상태">한계와 상태</a> &bull; <a href="#요구사항">요구사항</a> &bull; <a href="#설치">설치</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub><a href="../../README.ko.md">because-i-needed</a>의 일부</sub></p>

---

budget은 계정이 보고하는 사용량 창을 지켜보다가, 사용자가 정한 비율에서 모든 세션을 붙잡아 둡니다. 창이 그 비율에 도달하면 실행 중인 각 세션의 다음 도구 호출(서브에이전트의 호출 포함)이 질문 하나를 기다립니다. **"지정한 n%에 도달했습니다, 작업을 이어서 진행하시겠어요?"** 계속하려면 예, 멈추려면 아니오로 답합니다. [dashboard](../dashboard) 플러그인은 설정한 임계값을 보여 줍니다.

## 시작하기

- Claude Code: `/budget:mode 80` · Codex: `$budget:mode 80` — 80%에서 멈추고 묻습니다.
- `/budget:mode off`는 기능을 끄고, `/budget:mode status`는 임계값과 마지막으로 측정한 창을 보여 줍니다.
- 임계값은 사용자 계정 하나에 대한 설정이며 Claude Code와 Codex가 공유합니다.

## 동작 방식

**Claude Code**는 **5시간** 창을 측정합니다. Claude Code는 매 차례 뒤와 창이 1포인트 단위로 움직일 때마다 플러그인에 이를 알립니다. 창이 임계값 이상이면 budget은 다음 도구 호출을 붙잡고 Claude Code의 자체 질문 대화상자에서 묻습니다(chip `budget`, 선택지 예와 아니오).

- 예: 호출이 계속 진행되며, 창이 초기화될 때까지 그 세션에는 다시 묻지 않습니다.
- 아니오: 호출이 거부되고 차례가 멈춥니다.
- 질문 하나가 열려 있는 동안 도착하는 모든 호출에 그 답이 적용되므로, 병렬 서브에이전트에도 한 번만 묻습니다.
- 답할 사람이 없는 실행(`claude -p`)과 닫힌 대화상자는 아니오로 처리합니다.

**Codex**는 **7일** 창을 측정하며, Codex가 보고하는 창은 이것뿐입니다. budget은 계정의 최근 세션 로그(`~/.codex/sessions`)에서 가장 최신 수치를 읽으므로 새 세션도 첫 호출부터 붙잡힙니다. Codex에는 플러그인이 열 수 있는 대화상자가 없으므로, budget은 호출을 거부하고 에이전트에게 같은 질문으로 차례를 끝내라고 알립니다. 계속하려면 예(`네`, `yes`, `y`, `계속`, `continue`도 가능)로 답하세요. 다른 답은 세션을 계속 멈춘 상태로 둡니다. 먼저 `/hooks`에서 플러그인 훅을 신뢰하세요.

**[free-hands](../free-hands)와 함께 쓸 때:** free-hands는 목표를 실행하는 동안 절대 묻지 않지만 이 질문만은 예외입니다. 세션에서 budget의 질문이 열려 있는 동안 free-hands 0.4.0은 이를 통과시키고 차례를 이어가지 않습니다.

## 설정과 상태

- `~/.config/because-i-needed/budget.json`(`$XDG_CONFIG_HOME`이 설정돼 있으면 그 아래): `{"percent": 80}`. `/budget:mode`가 쓰고 `off`가 지웁니다.
- `~/.config/because-i-needed/budget/`: 세션의 질문이 열려 있는 동안 `pending/<session>.json`, 한 창에 대해 예를 답한 뒤 `acks/<session>.json`, 호스트가 마지막으로 보고한 창을 담은 `usage.json`(dashboard가 보여 줍니다).
- 새 창이 시작되면 다시 묻습니다. 초기화 시각이 몇 초 움직이는 정도는 같은 창으로 봅니다. Codex가 보고하는 초기화 시각이 읽을 때마다 1초씩 달라지기 때문입니다.

## 한계와 상태

Claude Code 2.1.299와 Codex 0.162.1에서 사례별 1회씩 측정했습니다([z-lab `budget-lab`](https://github.com/zeriong/z-lab/tree/main/budget-lab): `run-0.1.0`, `run-0.1.0-r2`. 그 근거가 되는 사실은 `codex-gate-0.1.0`, `codex-gate-0.1.0-r2`, z-lab `plugin-platform-lab/mod-interactive-2.1.299`에 있습니다).

- Claude Code는 대화상자를 보여 줬고, 예는 호출을 실행시켰으며, 아니오는 차례를 멈췄습니다("Interrupted"). 임계값 미만에서는 아무 일도 없었습니다. 병렬 서브에이전트 두 개에는 한 번만 물었습니다. 예를 답한 뒤의 호출은 다시 묻지 않고 실행됐습니다(R01–R05, R10).
- Codex는 질문과 함께 차례를 끝냈고 아무것도 실행하지 않았습니다. 예가 세션의 잠금을 풀었고 이후 호출은 다시 묻지 않고 실행됐습니다. 임계값 미만에서는 아무 일도 없었습니다(R06, R09, R11).
- free-hands가 목표를 실행하는 중에도 Claude Code에서는 질문이 표시됐습니다. Codex에서는 게이트가 걸린 차례가 곧바로 끝났고, free-hands 0.3.0에서는 중단 가드가 세 번 더 이어가게 했습니다(R04, R07, R12; codex-gate B03).

측정하지 않은 항목: 차례가 이미 실행 중일 때 임계값을 넘는 경우(Claude Code의 다음 보고 전에 차례가 임계값을 넘어갈 수 있음); 여러 대화형 세션의 동시 실행; 임계값에서의 `claude -p` 실행; Codex의 5시간 창(측정한 계정에서는 보고되지 않음); 우회하지 않고 `/hooks`로 신뢰한 Codex 훅.

budget이 사용하는 Claude Code의 플러그인 훅 모듈 API는 얼리 액세스로 표시되어 있으며 릴리스 사이에 바뀔 수 있습니다.

## 요구사항

- 플러그인 훅 모듈을 지원하는 Claude Code(2.1.299에서 측정) 또는 Codex CLI(0.162.1에서 측정).
- Codex 훅과 `/budget:mode`를 위한 `PATH`의 `python3`.

## 설치

먼저 마켓플레이스를 추가한 뒤 플러그인을 설치합니다.

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install budget@because-i-needed
```

Codex는 [마켓플레이스 안내](../../README.ko.md#codex)를 참고하세요.

## 라이선스

MIT. [LICENSE](../../LICENSE)를 참고하세요.
