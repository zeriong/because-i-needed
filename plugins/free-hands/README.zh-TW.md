<p align="center"><strong>free-hands</strong></p>

<p align="center"><strong>交給代理一個有限目標，它就會不提問、不停止地完成清單。</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.1.0-blue" alt="版本"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="授權：MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code 外掛"></a></p>

<p align="center"><a href="#開始">開始</a> &bull; <a href="#目標檔案">目標檔案</a> &bull; <a href="#不提問">不提問</a> &bull; <a href="#hooks">Hooks</a> &bull; <a href="#討論面板">討論面板</a> &bull; <a href="#堆疊pr">堆疊 PR</a> &bull; <a href="#限制與狀態">限制與狀態</a> &bull; <a href="#codex">Codex</a> &bull; <a href="#需求">需求</a> &bull; <a href="#安裝">安裝</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub><a href="../../README.zh-TW.md">because-i-needed</a> 的一部分</sub></p>

---

free-hands 將目標固定為有限且可檢查的清單，接著不向你提問或停止，逐項完成所有未完成事項。遇到原本需要你決定的問題時，由五個唯讀角色組成的討論面板提供意見；主代理依據證據做決定，並記錄不同意見與復原方式。

## 開始

- Claude Code：`/free-hands:run <目標>`
- Codex：`$free-hands:run <目標>`
- 也可以在提示中寫入 **free-hands**。首次回覆會以你的語言詢問一次是否開始。回答「是」會帶著該目標啟動技能；回答「否」則會提出可能方向並結束此回合。解釋或引用名稱不算開始請求。目標啟用期間再次說「free-hands」代表修正目前的執行方式，無須再次確認。

## 目標檔案

free-hands 在儲存庫根目錄保存 `.free-hands/goal.md`，並放置 `.free-hands/.gitignore`（`*`），如此不必碰觸 `.git` 就能忽略該資料夾。檔案記錄目標、有限清單、決定及恢復說明：

```markdown
status: active
max_iterations: 40
iterations: 0
## Goal
<一句話目標>
## Checklist
- [ ] <有明確完成條件的有限事項>
## Decisions
## Resume
<下一個工作階段需要的資訊>
```

標記：`- [ ]` 未完成，`- [x]` 已完成，`- [-] … — needs the user` 因硬性限制或其他阻礙而無法繼續。狀態為 `active`、`done`、`waiting` 或 `paused`。只有未完成的 `[ ]` 會讓提問與停止守衛生效；只要仍有 `[ ]` 項目，`done`/`waiting` 都不會結束這次執行。清單全部完成後記錄 `done`；只剩待使用者處理事項時記錄 `waiting`。達到 `max_iterations`（40）後，恢復備註會指示代理設為 `paused`、回報未完成事項並停止；此時可以再次提問。

## 不提問

目標啟用期間，技能不會向使用者提問。此規則會覆蓋專案與其他技能中的提問要求，也會覆蓋 claude-x-codex 等工作流程的核准閘門。代理會不經詢問推送分支並建立 PR。失敗的測試、閘門、hook 或審查會修正，或標記為 `- [-]`、需要使用者處理；不會改成通過。其他外掛的 hook 仍會執行。

## Hooks

各 hook 的執行條件不同：

- 只有位於 `## Checklist` 下方、且在程式碼區塊外的 `- [ ]` 行才會計為未完成項目。
- 目標有未完成 `[ ]`、迭代數低於 `max_iterations`，且狀態為 `active`，或為仍有未完成項目的 `done`/`waiting` 時，提問與停止守衛會執行。提問守衛會拒絕提問工具。達到上限後可以提問。Stop hook 會先將計數寫入磁碟再阻止停止，最多延續40次。
- 目標為 `active` 時會送出恢復備註（`UserPromptSubmit`、包括壓縮後的 `SessionStart`），即使沒有未完成項目也會送出；仍有未完成項目的 `done`/`waiting` 狀態也會送出。
- 沒有有效且啟用中的目標，但提示中出現「free-hands」時，會送出開始備註。背景工作通知不視為提示；提示中引用的通知會被忽略，並讀取提示的其餘部分。

Hook 輸入錯誤時不會產生效果。目標檔案格式錯誤或無法讀取時，不會啟用恢復、提問或停止行為；若提示中含有「free-hands」，提示 hook 會依照沒有啟用中目標的入口路徑處理，並可能送出開始問題。寫入失敗和鎖定逾時也不會產生效果，因此 hook 故障時工具呼叫或停止可以繼續。

## 討論面板

第一輪由五個角色獨立閱讀同一份簡報，主代理會在彙整前等待每個已派發角色的回覆。只有第一輪意見不一致時才進行第二輪。缺少或無效的回覆會重試一次；有效回覆少於三份時標記為 **panel degraded**，由主代理自行決定。無法確認最新模型的角色會略過並計為缺席，不會改用其他模型。Claude Code 若有 `ANTHROPIC_DEFAULT_<FAMILY>_MODEL` 重新導向，該 family 的角色就無法使用。主代理會核實關鍵主張，依據證據而非票數決定：實際檢查過的事實優先，其次是有來源的證據，再其次是推論。記錄每個角色的意見、異議、決定及復原方式。

| 角色 | 關注重點 | Claude 模型系列 |
|---|---|---|
| `quick-thinker` | 快速的第一原理判斷 | `sonnet` |
| `deep-thinker` | 後果、邊界情況與二階影響 | `opus` |
| `evidence-hunter` | 文件與原始碼證據 | `sonnet` |
| `trend-tracker` | 附日期的近期變化 | `sonnet` |
| `devils-advocate` | 對領先選項提出最有力的反對意見 | `opus` |

各角色使用其模型系列中目前可用的最新模型。Claude Code 的 Agent 工具不會顯示實際執行的模型 ID，因此應記錄resolver 回傳的 family alias，並註明「id not visible」。Codex 則記錄子程序執行時回報的模型。

## 堆疊PR

第一個 PR 以儲存庫的 integration 分支為目標。每個 PR 的標題結尾都加上執行中遞增的編號 ` (n)`，後續 PR 都以先前分支為基礎。使用者依堆疊順序合併 PR。前一個 PR 合併後，代理會在需要時將下一個 PR 的目標分支改為 integration，接著把 `origin/<integration>` 合併至其後的每個分支並推送。受阻批次不會跳過，因此堆疊順序就是合併順序。

## 限制與狀態

「面板比單一代理做出更好的決定」目前是**尚未測量的假設**。在 Claude Code 2.1.286–2.1.287 與 Codex 0.159.3–0.160.0 上，每個案例測量一次的內容（[z-lab `free-hands-lab`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab)：`run-0.1.0`、`run-0.1.0-r2`）：

- hook 會在工作階段開始、每則提示及壓縮後注入恢復備註（F01、F04、G02）。在 Claude Code 上，有未完成項目時停止守衛會阻止停止並將計數寫入磁碟（F02）；Codex 不會印出 hook 事件，因此僅有一次阻止停止的情況獲得證實（F04）。
- 開始問題、「是」與「否」的回答，以及解釋性提及，在兩個宿主上的行為均符合描述；但對韓文提示，Codex 以英文提問，並在使用者回答「否」後只簡單回應，沒有提供方向建議（F06）。
- 停止要求以 `paused` 結束；需要使用者處理的項目以 `[-]` 和 `waiting` 結束（G01、G03）。
- 以 `FREE_HANDS_ROLE` 啟動的面板子程序不會動到父程序的目標（F05）。
- 五個角色在兩個宿主上都使用各自系列的最新模型並回傳有效回覆；Claude 主代理會等待五個角色全部完成（F08、F09、G04）。

未測量：拒絕 `AskUserQuestion`（無頭模式的 Claude Code 沒有此工具）及拒絕 Codex 的 `request_user_input`（代理未呼叫）；執行時在 `max_iterations` 的解除和計數器寫入失敗（僅有單元測試）；第二輪（所有面板成員意見一致）；阻止角色寫入嘗試（沒有角色嘗試）；互動式 `/hooks` 信任；堆疊 PR。代理在四次執行中自行重寫了 `iterations`（F04、G03），因此只有代理不動計數器時上限才有效。

以下是技能與恢復備註交代給代理的規則。沒有 hook 會攔截這些命令：

- 不合併 PR，也不將任何內容合併至預設分支。
- 不以不可逆的方式刪除儲存庫外的檔案、資料、遠端分支或資料庫。
- 不部署、發布或向外部傳送內容（例如版本發佈、套件發佈、電子郵件或訊息）。

這類事項會附上原因並標記為 `- [-]`，然後繼續其他工作。已推送分支允許在先以一行通知後強制推送。

若要暫停，請說 **「pause」**、**「stop」** 或 **「일시정지」**。目標會記錄為 `paused`；再次執行命令即可恢復。

來源：由專案本機技能移植而來。

## Codex

依賴自動執行前，請在 `/hooks` 信任外掛 hooks。提問 hook 的 matcher 包含 `request_user_input`；尚未觀察到拒絕。Codex 預設模式沒有提問工具，因此由 Stop hook 負責延續工作。若未信任或啟用 hooks，技能仍依照書面規則繼續，但 hook 效果可能未生效。

面板為每個角色啟動一個 `codex exec -s read-only` 子程序（native subagent 可指定模型，但沒有唯讀控制，因此不使用 — F10）。不論角色為何，子程序都能搜尋網頁；為 `evidence-hunter` 和 `trend-tracker` 加上 `--search`（F09）。子程序需要網路。從沙箱中的主代理執行時，`panel.py run` 必須透過核准的權限提升在沙箱外執行，或由工作階段允許網路。否則所有子程序都會失敗，這次執行會由主代理自行決定並記錄為 **panel degraded**，然後繼續（G06）。

## 需求

- Hook 需要 `python3`，且必須位於 `PATH`。
- 需要 `git` 來尋找儲存庫根目錄。
- 堆疊 PR 流程需要 `gh`。
- Codex 面板流程需要 Codex CLI（`codex`）。

## 安裝

先新增市集，再安裝外掛：

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install free-hands@because-i-needed
```

Codex 請參閱[市集說明](../../README.zh-TW.md#codex)。

## 授權

MIT。請參閱 [LICENSE](../../LICENSE)。
