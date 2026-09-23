# ux-ui-builder — 개발 규칙

루트 `CLAUDE.md`의 공통 규칙이 전부 적용된다. 여기에는 ux-ui-builder에만 해당하는 것을 쓴다.
이 플러그인은 원본 레포에 개발 규칙 파일이 없었다. 아래는 전부 2026-09-23 기준 코드에서 확인한 사실에서 도출했다.

구성: 스킬 2개(`skills/ux-ui-builder` 웹, `skills/ux-ui-builder-mobile` 모바일), 에이전트 2개(`agents/ux-ui-art-director.md`,
`agents/ux-ui-mobile-art-director.md`, 둘 다 `model: opus`), 훅 `hooks/hooks.json`(PreToolUse → 커밋 게이트),
스크립트 2개(`scripts/ui-commit-gate.sh`, `scripts/mobile-snapshot.sh`), `plugin.json`에 MCP 서버 4개
(`chrome-devtools`, `mobile-mcp`, `ios-simulator`, `flutter`).

---

## 제1조 — 플러그인명과 MCP 서버 키는 도구 이름의 일부다

에이전트의 `tools:` 와 SKILL.md는 MCP 도구를 `mcp__plugin_ux-ui-builder_<서버키>` 로 참조한다
(`agents/*.md` frontmatter, `skills/ux-ui-builder/SKILL.md` Bootstrap 단계). 이 이름은 **플러그인명 + `plugin.json`의 `mcpServers` 키**로 만들어진다.

- 플러그인명이나 서버 키를 바꾸면 에이전트 `tools:` 와 SKILL.md 참조를 같은 커밋에서 바꾼다.
  안 바꾸면 아트 디렉터가 측정 도구를 쓸 수 없게 된다.
- 확인: `grep -rn 'mcp__plugin_' plugins/ux-ui-builder`
- 플러그인명은 README 10개의 `/ux-ui-builder:ux-ui-builder`·`/ux-ui-builder:ux-ui-builder-mobile` 에도 박혀 있다.

## 제2조 — 한 사실의 사본들은 같은 커밋에서 맞춘다

| 사실 | 원본 | 사본 |
|---|---|---|
| UI 파일 유형 | `scripts/ui-commit-gate.sh` 의 `DEFAULT_GLOBS` | README 5개(Features·Commit gate·FAQ), `skills/ux-ui-builder-mobile/SKILL.md` Roles |
| 모바일 측정 백엔드 매트릭스 | `skills/ux-ui-builder-mobile/references/backend-detection.md` §2 표 | README 5개 "Mobile measurement backends" 표 |
| 승인 아티팩트 JSON 형식 | `ui-commit-gate.sh approve` 가 쓰는 JSON | `skills/ux-ui-builder/references/review-rubric.md`, `skills/ux-ui-builder-mobile/references/mobile-review-rubric.md` |
| 스크립트 경로·서브커맨드 | `scripts/*.sh` | `hooks/hooks.json`, 두 SKILL.md, `backend-detection.md` (`${CLAUDE_PLUGIN_ROOT}/scripts/...`) |
| 번들 MCP 목록 | `plugin.json` `mcpServers` | 에이전트 `tools:`, README 5개(Installation·Requirements) |
| 아트 디렉터 모델 | `agents/*.md` 의 `model:` | README 5개("Opus") |

## 제3조 — 커밋 게이트 불변식

`ui-commit-gate.sh` 는 설치한 사용자의 **모든 Bash 호출 직전에** 실행된다. 그래서:

- `git commit` 이 아니면 즉시 `exit 0` 하는 fast path를 유지한다.
- **fail-open**: 입력 파싱 실패, 명령 없음, git 저장소 아님 → 허용(`exit 0`). 사용자 셸을 막지 않는다(스크립트 주석에 명시된 의도).
- 차단은 `exit 2` + stderr 메시지다. stderr가 에이전트에게 차단 사유로 전달된다.
- 기본 확장자는 보수적으로 둔다: 순수 `.ts`/`.js`/`.java`, 레이아웃이 아닌 `.xml` 은 넣지 않는다(백엔드 전용 커밋 차단 방지).
- JSON 파서 폴백(`jq` → `python3` → `node`)을 유지한다. `jq` 없는 환경이 있다.
- 스크립트는 실행 권한(git mode `100755`)을 유지한다. 새 스크립트는 `chmod +x` 후 커밋한다.

## 제4조 — 게이트를 고치면 소스 스크립트를 직접 돌려 확인한다

세션에서 동작하는 훅은 **설치본 캐시의 스크립트**다. 소스를 고쳐도 현재 세션의 훅은 바뀌지 않으므로, 소스를 직접 실행한다.
저장소 루트에서 (2026-09-23 검증):

```bash
G="$PWD/plugins/ux-ui-builder/scripts/ui-commit-gate.sh"
t=$(mktemp -d) && git -C "$t" init -q && echo '<p/>' > "$t/a.html" && git -C "$t" add a.html
c='{"tool_input":{"command":"git commit -m x"}}'
echo "$c" | CLAUDE_PROJECT_DIR="$t" bash "$G" 2>/dev/null; echo "exit=$?"          # 2 — 승인 없는 UI 커밋 차단
echo '{"tool_input":{"command":"ls"}}' | CLAUDE_PROJECT_DIR="$t" bash "$G"; echo "exit=$?"  # 0 — fast path
(cd "$t" && bash "$G" approve demo >/dev/null)
echo "$c" | CLAUDE_PROJECT_DIR="$t" bash "$G"; echo "exit=$?"                     # 0 — 같은 diff 승인 후 통과
rm -rf "$t"
```

확장자를 바꿨다면 그 확장자 파일로 한 번 더 돌린다.

## 제5조 — 알려진 결함 (2026-09-23 확인, 미수정)

- 차단 메시지(`ui-commit-gate.sh` hook 모드)가 웹 스킬 `ux-ui-builder` 와 chrome-devtools만 안내한다.
  모바일 파일(`.swift` `.kt` `.dart` `.storyboard` `.xib`, `res/layout`)이 막혀도 `ux-ui-builder-mobile` 을 안내하지 않는다.
  메시지 변경은 설치한 사용자에게 보이는 동작 변경이므로 버전을 올린다(루트 제2조).
