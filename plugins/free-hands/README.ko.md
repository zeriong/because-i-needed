<p align="center"><strong>free-hands</strong></p>

<p align="center"><strong>Claude Code</strong>와 <strong>Codex CLI</strong>에서만 동작합니다.</p>

<p align="center"><strong>에이전트에게 유한한 목표를 주면 체크리스트를 질문하거나 멈추지 않고 처리합니다.</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.7.0-blue" alt="버전"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="라이선스: MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code 플러그인"></a></p>

<p align="center"><a href="#시작하기">시작하기</a> &bull; <a href="#목표-파일">목표 파일</a> &bull; <a href="#예상-완료-시각">예상 완료 시각</a> &bull; <a href="#묻지-않기">묻지 않기</a> &bull; <a href="#훅">훅</a> &bull; <a href="#패널">패널</a> &bull; <a href="#누적-pr">누적 PR</a> &bull; <a href="#한계와-상태">한계와 상태</a> &bull; <a href="#codex">Codex</a> &bull; <a href="#요구사항">요구사항</a> &bull; <a href="#설치">설치</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub><a href="../../README.ko.md">because-i-needed</a>의 일부</sub></p>

---

free-hands는 목표를 유한하고 확인 가능한 체크리스트로 고정한 뒤, 열린 항목을 사용자에게 묻거나 멈추지 않고 처리합니다. 사용자가 결정할 사안이 생기면 읽기 전용 패널의 다섯 역할이 의견을 내고, 메인 에이전트가 증거로 결정하고, 그 결정과 반대 의견, 되돌리는 방법을 기록합니다.

## 시작하기

- Claude Code: `/free-hands:run <목표>`
- Codex: `$free-hands:run <목표>`
- 프롬프트에 **free-hands**라는 단어를 넣어 시작할 수도 있습니다. 첫 응답으로 사용자 언어의 진입 질문 하나가 나옵니다. 예라고 답하면 해당 목표로 스킬을 시작하고, 아니요라고 답하면 가능한 방향을 제안하고 그 차례를 끝냅니다. 이름을 설명하거나 인용한 언급은 실행 요청으로 보지 않습니다. 이 세션에서 목표가 활성화된 동안 다시 “free-hands”라고 하면 확인을 묻지 않고 진행 방식을 바로잡습니다.

## 목표 파일

저장소 루트에 `.free-hands/goal.md`와 `.free-hands/.gitignore`(`*`)를 둬서 `.git`을 건드리지 않고 폴더를 Git에서 제외합니다. 목표, 유한한 체크리스트, 결정 기록과 재개 메모가 들어갑니다.

```markdown
status: active
max_iterations: 40
iterations: 0
owner: <session id>
## Goal
<한 문장 목표>
## Checklist
- [ ] <완료 여부를 확인할 수 있는 유한한 항목>
## Decisions
## Resume
<다음 세션에 필요한 내용>
```

표시는 `- [ ]` 미완료, `- [x]` 완료, `- [-] … — needs the user` 하드 리밋이나 다른 장애물로 진행할 수 없는 항목입니다. 상태는 `active`, `done`, `waiting`, `paused`입니다. 미완료 `[ ]` 항목만 질문·중단 가드를 작동시키며, 미완료 항목이 남아 있으면 `done`이나 `waiting`으로 실행이 끝나지 않습니다. 모두 완료되면 `done`, 사용자 처리가 필요한 항목만 남으면 `waiting`을 기록합니다. `max_iterations` 40회에 도달하면 복원 메모가 `paused` 설정, 미완료 항목 보고, 중단을 지시하며 질문이 다시 허용됩니다.

`owner:`는 목표가 속한 세션입니다. 에이전트가 실행을 시작하거나 재개할 때 훅 메모가 알려 준 세션 id를 적습니다. [훅](#훅)을 참고하세요.

## 예상 완료 시각

목표를 진행하는 에이전트는 예상 시간을 쓰지도, 보지도 않습니다. 체크리스트에 예상 시간이 없는 항목이 생기면, 목표를 가진 세션의 훅이 별도의 짧은 예측기를 백그라운드에서 띄웁니다. 예측기는 Haiku로 도는 헤드리스 Claude Code 세션입니다. 안전 모드라 훅·플러그인 훅·CLAUDE.md가 없고, 읽기 전용 도구만 쓰며, 세션도 저장하지 않습니다. 필요한 코드를 읽은 뒤 항목마다 분과 범주(`docs`, `fix`, `feature`, `refactor`, `test`, `research`, `ops`)를 `.free-hands/estimates.jsonl`에 한 줄씩 쓰고 종료합니다. 훅은 바로 반환하고 아무것도 출력하지 않으므로, 이 과정은 에이전트의 맥락에 전혀 들어가지 않습니다. 예측기를 끄려면 `FREE_HANDS_ESTIMATOR=off`로 설정합니다. 예측기 실행은 매번 사용자 계정의 별도 Claude Code 세션이며(측정한 실행에서 1회 0.002–0.003 USD의 사용량), [budget](../budget) 플러그인은 이 세션을 보지 못합니다.

그 뒤로 목표를 가진 세션의 훅이 항목마다 시간을 잽니다.

- `.free-hands/eta.json`의 작업 시간 시계. 끝난 차례 뒤, 새 세션 전, 사용자가 프롬프트를 입력하기 전, 목표가 일시정지된 동안의 시간은 세지 않고, 20분이 넘는 공백은 도구 호출이 그만큼 실행됐다고 보고한 만큼만 셉니다.
- 끝난 항목마다 `.free-hands/timings.jsonl`에 한 줄: 항목, 잰 시간, 모델, effort. 예상 시간은 `estimates.jsonl`에서 합쳐 오며, 항목이 끝난 뒤에 도착해도 합쳐집니다. 이 파일이 그 프로젝트의 기록입니다. 프로젝트 폴더에 남고, Git은 무시하며, 새 목표를 시작해도 유지됩니다.

[dashboard](../dashboard)는 완료 예상 시각을 `ETA 15:40`처럼 시각으로, 남은 시간을 상세에 `~25m left`로 보여 줍니다. 시각 뒤의 `+`는 아직 예상 시간이 없는 미완료 항목이 있다는 뜻입니다. dashboard 0.3.0부터는 항목이 체크되거나 예상 시간이 도착하면 차례 도중에도 줄이 바뀝니다.

완료 예상 시각은 미완료 항목마다 예상 시간 × 작업하는 모델 계열의 계수 × 그 프로젝트의 계수를 더한 값입니다.

- **모델 계수**: z-lab에서 측정했습니다. Haiku의 예상은 실제 작업보다 훨씬 길었습니다. 항목에 실제로 걸린 시간은 Haiku 예상의 Sonnet 0.040, Opus 0.070, Fable 0.074였고, 이 값을 계수로 제공합니다([`eta-haiku-calibrate-0.6.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-haiku-calibrate-0.6.0), effort xhigh로 측정한 목표 실행 26개). 측정한 계수가 없는 작업 모델(Haiku, Codex의 모델)은 그 평균 0.061을 씁니다. 이것은 측정이 아니라 선택입니다. 0.5.0이 쓴 목표처럼 항목에 에이전트 자신의 `(~6m fix)`가 남아 있으면, 그 예상에는 0.5.0의 계수를 그대로 씁니다.
- **프로젝트 계수**: 이 프로젝트의 항목이 모델 계수의 예측보다 얼마나 더 걸리거나 덜 걸렸는지입니다. `timings.jsonl`의 최근 60줄에서 배우며, 기록이 적을 때는 1 쪽으로 당겨집니다. 새 프로젝트는 1에서 시작합니다.

진행 중인 항목이 예측을 넘기면 목표의 나머지도 적게 잡혔을 가능성이 큽니다. 이때 완료 예상 시각은 그 항목에 경과 시간의 절반을 더 잡고, 뒤 항목들은 초과 배율의 제곱근만큼 늘려 잡으며(예측의 2배 → ×1.41), 항목이 진행되는 동안 계속 바뀝니다. 측정한 실행으로 재생해 보니, 항목이 예측의 2배를 넘긴 시점의 남은 시간 오차가 절반으로 줄었습니다. 실제 프로젝트에서 0.79 → 0.28배수, 실험에서 1.03 → 0.59배수였습니다([`eta-live-replay-0.7.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-live-replay-0.7.0), V01). 모델 계수는 작은 실험 과제(항목당 1–3분)로 맞춘 값이라, 실제의 큰 항목에서는 프로젝트 기록과 초과 반영이 따라잡기 전까지 목표 시작 시의 완료 예상 시각이 몇 배 이르게 나올 수 있습니다([`eta-local-replay-0.7.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-local-replay-0.7.0), L03). 큰 과제로 다시 보정할 계획입니다.

## 묻지 않기

목표가 활성 상태인 동안 스킬은 사용자에게 묻지 않습니다. 프로젝트와 다른 스킬의 질문 규칙, peer-coding 같은 워크플로의 승인 게이트도 이 규칙으로 덮어씁니다. 에이전트는 묻지 않고 브랜치를 푸시하고 PR을 생성합니다. 실패한 테스트·게이트·훅·리뷰는 수정하거나 사용자 처리가 필요하다고 `- [-]`로 표시하며, 통과한 것으로 바꾸지 않습니다. 다른 플러그인의 훅은 계속 동작합니다.

단 하나의 예외는 [budget](../budget) 플러그인의 사용량 질문입니다. 사용량 임계값에 도달해 budget이 호출을 멈추면 에이전트는 그 지시를 따릅니다. Claude Code에서는 대화상자로, Codex에서는 질문과 함께 차례를 끝내는 방식입니다. 임계값을 넘겨 쓸지는 패널이 아니라 사용자가 결정합니다.

## 훅

훅마다 동작 조건이 다릅니다.

- 아래의 가드와 복원 메모는 `owner:`에 적힌 세션과 그 세션이 띄운 서브에이전트에서만 동작합니다. 같은 저장소의 다른 세션(두 번째 터미널, 다른 도구가 띄운 `claude -p` 등)에는 복원 메모, 질문·중단 가드, 카운터, 셸 가드가 모두 적용되지 않습니다. 그 세션의 프롬프트에 “free-hands”가 있으면 진입 메모가 어느 세션이 실행을 소유하는지 알려 줍니다. 그 세션에서 `/free-hands:run`(Codex: `$free-hands:run`)을 실행하면 실행이 그 세션으로 넘어갑니다. 0.2.0이 만든 목표처럼 `owner:`가 없는 목표는 훅이 처음 마주친 세션의 것이 됩니다.
- `## Checklist` 아래에 있으면서 코드 블록 밖에 있는 `- [ ]` 줄만 미완료 항목으로 셉니다.
- [완료 예상 시각](#예상-완료-시각)의 시계(모든 도구의 `PostToolUse`와 프롬프트·세션·중단 훅)는 가드처럼 목표를 가진 세션과 그 서브에이전트에서만 돕니다. 패널 자식은 시계에 기록하지 않습니다. 마지막 항목을 체크하면서 실행을 끝내는 편집도 기록합니다. 같은 훅이 예측기를 띄우며, Claude Code에서만, 1분에 최대 한 번입니다.
- 셸 가드(`Bash`의 `PreToolUse`)는 목표가 `active`이거나, 미완료 항목이 남은 `done`/`waiting`일 때 동작합니다. `[ ]` 항목이 더 이상 없거나 `max_iterations`에 도달해도 마찬가지입니다. [한계와 상태](#한계와-상태)에 설명된 하드 리밋 명령을 거부합니다.
- 질문·중단 가드는 목표에 미완료 `[ ]` 항목이 있고 `max_iterations` 미만이며, 상태가 `active`이거나 미완료 항목이 남은 `done`/`waiting`일 때 동작합니다. 질문 가드는 질문 도구를 거부합니다. 한도에서는 질문이 허용됩니다. Stop 훅은 중단을 막기 전에 반복 횟수를 디스크에 기록하며 최대 40회까지 이어갑니다. 세션에서 budget의 사용량 질문이 열려 있는 동안에는 두 가드 모두 동작하지 않습니다.
- 복원 메모(`UserPromptSubmit`, 압축 후를 포함한 `SessionStart`)는 목표가 `active`(미완료 `[ ]` 항목이 없어도)인 동안 또는 미완료 항목이 남은 `done`/`waiting` 상태에서 전달됩니다.
- 진입 메모는 활성 상태의 올바른 목표가 없고 프롬프트에 “free-hands”가 있을 때 전달됩니다. 백그라운드 작업 알림은 프롬프트로 취급하지 않습니다. 프롬프트 안에 인용된 알림은 무시하고 나머지 프롬프트는 읽습니다.

잘못된 훅 입력은 아무 효과도 내지 않습니다. 목표 파일이 잘못됐거나 읽을 수 없으면 복원·질문·중단 동작은 활성화되지 않습니다. 프롬프트에 “free-hands”가 있으면 프롬프트 훅은 활성 목표가 없는 경우의 진입 경로를 따라 진입 질문을 낼 수 있습니다. 쓰기 실패와 잠금 시간 초과도 효과가 없어 도구 호출이나 중단이 진행됩니다. `eta.json`이나 `timings.jsonl`이 깨져 있으면 기록과 완료 예상 시각이 없을 뿐, 가드의 판단은 바뀌지 않습니다.

## 패널

다섯 역할은 1라운드에서 같은 브리프를 독립적으로 검토하며, 메인 에이전트는 집계 전에 디스패치한 모든 역할의 응답을 기다립니다. 2라운드는 1라운드 의견이 갈릴 때만 진행합니다. 누락되거나 유효하지 않은 답변은 한 번 재시도하며, 유효 답변이 세 개 미만이면 **panel degraded**로 표시하고 메인 에이전트가 단독 결정합니다. 최신 모델을 확인할 수 없는 역할은 대체 모델 없이 건너뛰고 누락으로 셉니다. Claude Code에서 `ANTHROPIC_DEFAULT_<FAMILY>_MODEL` 리디렉션이 있으면 해당 family의 역할을 사용할 수 없습니다. 메인 에이전트는 핵심 주장을 확인하고 표결이 아닌 증거로 결정합니다. 저장소나 실행에서 확인한 사실, 출처가 있는 근거, 추론 순으로 판단하며 각 의견, 반대 의견, 결정과 되돌리는 방법을 기록합니다.

| 역할 | 중점 | Claude 모델 계열 |
|---|---|---|
| `quick-thinker` | 빠른 제일 원칙 판단 | `sonnet` |
| `deep-thinker` | 결과, 예외 상황, 2차 영향 | `opus` |
| `evidence-hunter` | 문서와 소스 근거 | `sonnet` |
| `trend-tracker` | 날짜가 있는 최신 변화 | `sonnet` |
| `devils-advocate` | 선두 선택지에 대한 가장 강한 반론 | `opus` |

각 역할은 해당 계열에서 사용 가능한 최신 모델을 사용합니다. Claude Code의 Agent 도구는 실제 실행 모델 ID를 보여 주지 않으므로 resolver가 반환한 family alias와 “id not visible”을 기록합니다. Codex에서는 자식 실행에서 보고한 모델을 기록합니다.

## 누적 PR

첫 PR은 저장소의 integration 브랜치를 대상으로 합니다. 모든 PR 제목 끝에 실행 내에서 증가하는 번호 ` (n)`을 붙이고, 이후 PR은 이전 브랜치를 기반으로 합니다. 사용자는 누적 순서대로 PR을 병합합니다. 앞선 PR이 병합되면 에이전트는 필요한 경우 다음 PR의 대상을 integration 브랜치로 바꾸고, 뒤의 각 브랜치에 `origin/<integration>`을 병합해 푸시합니다. 막힌 batch를 건너뛰지 않으므로 누적 순서가 병합 순서입니다.

## 한계와 상태

패널이 단일 에이전트보다 더 나은 결정을 내린다는 주장은 **측정되지 않은 가설**입니다. Claude Code 2.1.286–2.1.287 및 Codex 0.159.3–0.160.0에서 사례별 1회씩 측정한 내용 ([z-lab `free-hands-lab`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab): `run-0.1.0`, `run-0.1.0-r2`):

- 훅은 세션 시작 시, 모든 프롬프트마다, 압축 후에 복원 메모를 주입합니다 (F01, F04, G02). Claude Code에서는 항목이 남아 있을 때 중단 가드가 차단하고 카운터를 디스크에 기록합니다 (F02). Codex에서는 훅 이벤트를 출력하지 않으므로 한 번 차단된 것만 확인했습니다 (F04).
- 진입 질문과 예·아니요 답변, 설명을 위한 언급은 양쪽 호스트에서 설명대로 동작합니다. 단, 한국어 프롬프트에도 Codex는 영어로 질문했고, “아니요”에 방향을 제시하는 대신 간단히 확인하는 답변을 했습니다 (F06).
- 중단 요청은 `paused`로 끝나며, 사용자 처리가 필요한 항목은 `[-]`와 `waiting`으로 끝납니다 (G01, G03).
- `FREE_HANDS_ROLE`로 시작한 패널 자식은 부모의 목표를 건드리지 않습니다 (F05).
- 다섯 역할은 양쪽 호스트에서 각 계열의 최신 모델로 실행되어 유효한 응답을 반환하며, Claude 메인은 다섯 응답 모두를 기다립니다 (F08, F09, G04).

측정하지 않은 항목: `AskUserQuestion` 거부(headless Claude Code에는 해당 도구가 없음)와 Codex의 `request_user_input` 거부(에이전트가 호출하지 않음); 런타임의 `max_iterations`에서의 해제 및 카운터 쓰기 실패(단위 테스트만 수행); 2라운드(모든 패널이 동의함); 역할의 쓰기 시도 차단(시도한 역할 없음); 대화형 `/hooks` 신뢰; 누적 PR. 네 번의 실행에서 에이전트가 직접 `iterations`를 다시 썼으므로(F04, G03), 에이전트가 카운터를 그대로 둘 때만 한도가 유지됩니다.

스킬과 복원 메모는 에이전트에게 다음 하드 리밋을 둡니다.

- PR을 병합하거나 기본 브랜치에 무엇이든 병합하지 않습니다.
- 저장소 밖 파일, 데이터, 원격 브랜치, 데이터베이스를 되돌릴 수 없게 삭제하지 않습니다.
- 배포, 공개, 외부 전송(릴리스·패키지 공개·이메일·메시지 포함)을 하지 않습니다.

해당 항목은 사유와 함께 `- [-]`로 표시하고 다른 작업을 계속합니다. 이미 푸시한 브랜치의 강제 푸시는 한 줄로 알린 뒤 허용됩니다. 브랜치 푸시, 이슈와 PR 생성, 이에 대한 댓글 작성은 허용됩니다.

0.2.0부터는 목표가 활성 상태일 때 셸 훅도 이를 위반하는 일반 명령을 거부합니다. `gh pr merge`; 기본 브랜치를 업데이트하는 푸시와 병합(목표 파일의 `default_branch:`, 없으면 푸시 원격의 HEAD, 그것도 없으면 `main`과 `master`); `gh api`를 통한 병합과 릴리스 생성; 원격 삭제(`git push --delete`, `:ref`, `--prune`, `--mirror`, `gh repo delete`, `gh release delete`); 그리고 `npm`/`pnpm`/`yarn publish`, `cargo publish`, `twine upload`, `gem push`, `docker push`, `docker buildx build --push`, `gh release create`, `vercel` 배포, `netlify deploy`, `fly deploy`, `firebase deploy`, `terraform apply`, `kubectl apply`, `helm install`/`upgrade`, `sendmail`, `mail`, `mutt`입니다. `--help`/`-h`는 `sendmail`·`mail`·`mutt`과 `terraform`을 제외한 목록의 모든 CLI에서 통과합니다. `sendmail`·`mail`·`mutt`은 항상 거부되고, `terraform`의 도움말 플래그는 `-help`입니다. `--dry-run`은 `git push`, `npm`/`pnpm`/`yarn publish`, `cargo publish`, `kubectl`, `helm`에서 통과합니다. 두 호스트에서 훅은 실행 전에 `gh pr merge 1`, `npm publish`, `git push origin HEAD:main`을 거부했고, 거부 결과는 에이전트에 전달됐습니다([z-lab `run-0.2.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/run-0.2.0), P01–P04).

이 훅은 협조적인 에이전트가 사용하는 일반 명령에 대한 보완 장치이며, 의도적인 우회를 막는 방어 수단은 아닙니다. 규칙상 우회는 금지됩니다. `rm`, 데이터베이스 명령, heredoc 본문, 스크립트(`npm run deploy`), 대화형 세션에 입력한 명령, 다른 CLI 및 HTTP 호출(`curl`)은 읽지 않습니다.

0.3.0부터 목표는 한 세션에 속합니다. Claude Code 2.1.296과 Codex 0.162.1에서 사례마다 한 번씩 측정했습니다([z-lab `run-0.3.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/run-0.3.0)). 0.2.0에서는 같은 저장소의 두 번째 세션이 실행 중인 목표를 넘겨받아 그 작업을 했습니다(O01). 0.3.0에서는 그 세션이 목표에 관여하지 않았고, 목표 파일은 바이트 단위까지 그대로였습니다(O02). 소유 세션과 그 서브에이전트에서는 `gh pr merge 1`이 여전히 거부됐고, 다른 세션에서는 실행됐습니다(O03–O05). 스킬은 실행을 시작할 때 훅 메모의 id로 `owner:`를 적었고, 다른 세션의 실행을 넘겨받을 때 그 값을 바꿨습니다(O06). 두 호스트 모두 모든 훅 이벤트에 세션 id를 보내며, 재개와 압축 뒤에도 같은 id를 유지합니다([`session-id-0.3.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/session-id-0.3.0), S01–S03). 측정하지 않은 것: 두 세션이 동시에 실행되는 경우.

0.4.0부터 [budget](../budget) 질문이 통과하고, 목표가 [dashboard](../dashboard)에 표시됩니다. Claude Code 2.1.299와 Codex 0.162.1에서 측정했습니다([z-lab `budget-lab`](https://github.com/zeriong/z-lab/tree/main/budget-lab), [`dashboard-lab`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab)). 목표를 실행하는 중에도 budget의 대화상자가 표시됐는데, 0.3.0에서는 이것이 막혔습니다. Codex에서는 게이트가 걸린 차례가 곧바로 끝났고, 0.3.0의 중단 가드는 세 번 더 이어가게 했습니다(budget-lab R04, R07, R12; codex-gate B03). `guard.py status`는 두 호스트 모두에서 dashboard에 `active 0/40 · 1 open`을 전달했습니다(dashboard-lab D01, D04).

0.5.0부터 목표에 완료 예상 시각이 표시됩니다. Claude Code 2.1.325에서 Sonnet·Opus·Fable(effort xhigh)로, 크기가 다른 세 프로젝트에서 측정했습니다([z-lab `eta-calibrate-0.5.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-calibrate-0.5.0), [`eta-validate-r2-0.5.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-validate-r2-0.5.0)). 모든 실행에서 훅이 잰 시간은 독립 기록과 0.1분 이내로 일치했습니다(E01). 계수를 맞출 때 쓰지 않은 목표에서 모델 계수는 중앙 오차를 3.2배수에서 0.6배수(약 1.5배)로 줄였습니다. 원래 예상은 약 9배 길었습니다(W01). 체크리스트를 쓸 때 표시된 남은 시간은 실제로 걸린 시간의 중앙값 기준 1.42배 이내였고, 13개 목표 중 12개가 2배 이내였습니다(W04). 프로젝트 계수는 이 실행들에서 Sonnet에는 도움이 됐고 Opus에는 손해였습니다(W03). 그래서 그 효과는 주장하지 않습니다. dashboard 줄은 항목이 끝날 때마다 차례 도중에 바뀌었습니다([`dashboard-lab/run-0.3.0`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab/run-0.3.0), D09). 측정하지 않은 것: Codex, Haiku, 다른 effort 수준, 기록이 더 긴 프로젝트.

0.6.0부터 예상 시간은 그 격리된 예측기가 냅니다. Claude Code 2.1.325에서 Sonnet으로 헤드리스 free-hands 실행 2회와 대화형 세션 1회로 측정했습니다([z-lab `eta-isolated-run-r2-0.6.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-isolated-run-r2-0.6.0)). 작업하는 에이전트의 스트림에는 예상 시간에 관한 내용이 전혀 나타나지 않았고, free-hands 훅의 출력에도 없었습니다(J01). 예측기는 체크리스트가 쓰이고 약 6초 뒤에 답했으며, 오류를 남기지 않았고 세션도 저장하지 않았습니다(J02). 줄은 프롬프트 2초 뒤에 `ETA`를 보였고 항목이 끝날 때마다 바뀌었습니다(J04). 예측기 1회 실행 비용은 0.002–0.003 USD였습니다. 계수를 맞출 때 쓰지 않은 목표에서 Haiku × 계수는 항목 기준 0.68배수, 목표 기준 0.66배수(중앙값) 이내였고, 0.5.0의 에이전트 자기 예상은 0.62와 0.51이었습니다. 예상 시간을 에이전트의 맥락 밖으로 빼는 데 정확도가 조금 듭니다([`eta-haiku-calibrate-0.6.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-haiku-calibrate-0.6.0), H04, H05). 항목을 체크하면서 문구를 고쳐 쓰는 에이전트는 위치로 짝지어 같은 항목으로 봅니다. 이 수정은 기록된 실행을 재생해 확인했고, 새 실행으로는 확인하지 않았습니다(J05).

“pause”, “stop” 또는 **“일시정지”**라고 말하면 일시정지합니다. 목표에 `paused`를 기록하고 명령을 다시 실행하면 재개합니다.

기원: 프로젝트 내부 스킬을 이식했습니다.

## Codex

자동 적용에 앞서 `/hooks`에서 플러그인 훅을 신뢰하세요. 질문 훅 matcher에는 `request_user_input`이 포함되어 있지만, 거부되는지는 아직 관찰되지 않았습니다. Codex 기본 모드에는 질문 도구가 없으므로 계속 작업 규칙은 Stop 훅이 담당합니다. 훅을 신뢰하거나 활성화하지 않아도 스킬의 규칙은 따르지만 훅 동작은 꺼져 있을 수 있습니다. Codex에서도 훅이 항목 시간을 재지만 예측기는 띄우지 않습니다. 훅은 `CLAUDECODE=1`이고 부모 프로세스가 `CLAUDE_PID`일 때만 예측기를 띄우는데, Claude Code 안에서 시작한 Codex 세션은 이 값들을 물려받아도 부모 프로세스가 맞지 않습니다. 그래서 0.5.0이 인라인 예상 시간과 함께 쓴 목표가 아니면 완료 예상 시각이 표시되지 않습니다. 있는 내용은 `$dashboard:audit`로 볼 수 있습니다(Codex에는 실시간 줄이 없습니다). Codex에서는 측정하지 않았습니다.

패널은 역할마다 `codex exec -s read-only` 자식 하나를 실행합니다(native subagent는 모델은 지정할 수 있지만 읽기 전용 제어가 없어 사용하지 않습니다 — F10). 자식은 역할에 관계없이 웹을 검색할 수 있으며, `evidence-hunter`와 `trend-tracker`에는 `--search`를 추가합니다 (F09). 자식에는 네트워크가 필요합니다. 샌드박스의 메인 에이전트에서는 `panel.py run`을 승인된 권한 상승으로 샌드박스 밖에서 실행하거나, 세션이 네트워크를 허용해야 합니다. 그렇지 않으면 모든 자식이 실패하고, 실행은 메인 에이전트가 단독 결정한 뒤 **panel degraded**로 기록하며 계속됩니다 (G06).

## 요구사항

- 훅 실행을 위한 `python3` 및 `PATH` 등록.
- 저장소 루트를 찾기 위한 `git`.
- 누적 PR 단계용 `gh`.
- Codex 패널 경로용 Codex CLI(`codex`).

## 설치

먼저 마켓플레이스를 추가한 뒤 플러그인을 설치합니다.

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install free-hands@because-i-needed
```

Codex는 [마켓플레이스 안내](../../README.ko.md#codex)를 참고하세요.

## 라이선스

MIT. [LICENSE](../../LICENSE)를 참고하세요.
