<p align="center"><strong>free-hands</strong></p>

<p align="center">僅適用於 <strong>Claude Code</strong> 和 <strong>Codex CLI</strong>。</p>

<p align="center"><strong>交給代理一個有限目標，它就會不提問、不停止地完成清單。</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.7.0-blue" alt="版本"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="授權：MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code 外掛"></a></p>

<p align="center"><a href="#開始">開始</a> &bull; <a href="#目標檔案">目標檔案</a> &bull; <a href="#預計完成時間">預計完成時間</a> &bull; <a href="#不提問">不提問</a> &bull; <a href="#hooks">Hooks</a> &bull; <a href="#討論面板">討論面板</a> &bull; <a href="#堆疊pr">堆疊 PR</a> &bull; <a href="#限制與狀態">限制與狀態</a> &bull; <a href="#codex">Codex</a> &bull; <a href="#需求">需求</a> &bull; <a href="#安裝">安裝</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub><a href="../../README.zh-TW.md">because-i-needed</a> 的一部分</sub></p>

---

free-hands 將目標固定為有限且可檢查的清單，接著不向你提問或停止，逐項完成所有未完成事項。遇到原本需要你決定的問題時，由五個唯讀角色組成的討論面板提供意見；主代理依據證據做決定，並記錄不同意見與復原方式。

## 開始

- Claude Code：`/free-hands:run <目標>`
- Codex：`$free-hands:run <目標>`
- 也可以在提示中寫入 **free-hands**。首次回覆會以你的語言詢問一次是否開始。回答「是」會帶著該目標啟動技能；回答「否」則會提出可能方向並結束此回合。解釋或引用名稱不算開始請求。在此工作階段中目標啟用期間再次說「free-hands」代表修正目前的執行方式，無須再次確認。

## 目標檔案

free-hands 在儲存庫根目錄保存 `.free-hands/goal.md`，並放置 `.free-hands/.gitignore`（`*`），如此不必碰觸 `.git` 就能忽略該資料夾。檔案記錄目標、有限清單、決定及恢復說明：

```markdown
status: active
max_iterations: 40
iterations: 0
owner: <session id>
## Goal
<一句話目標>
## Checklist
- [ ] <有明確完成條件的有限事項>
## Decisions
## Resume
<下一個工作階段需要的資訊>
```

標記：`- [ ]` 未完成，`- [x]` 已完成，`- [-] … — needs the user` 因硬性限制或其他阻礙而無法繼續。狀態為 `active`、`done`、`waiting` 或 `paused`。只有未完成的 `[ ]` 會讓提問與停止守衛生效；只要仍有 `[ ]` 項目，`done`/`waiting` 都不會結束這次執行。清單全部完成後記錄 `done`；只剩待使用者處理事項時記錄 `waiting`。達到 `max_iterations`（40）後，恢復備註會指示代理設為 `paused`、回報未完成事項並停止；此時可以再次提問。

`owner:` 是目標所屬的工作階段。代理在開始或恢復執行時，依 hook 備註提供的工作階段 ID 寫入此欄位；請參閱 [Hooks](#hooks)。

## 預計完成時間

推進目標的代理既不寫估計，也看不到估計。清單中出現沒有估計的項目時，擁有目標的工作階段的 hook 會在背景啟動一個獨立的、短暫的估算器：一個使用 Haiku 的無介面 Claude Code 工作階段，處於安全模式（沒有 hooks、外掛 hooks 與 CLAUDE.md），只用唯讀工具，也不保存工作階段。它讀取所需的程式碼，為每個項目在 `.free-hands/estimates.jsonl` 中寫一行分鐘數與類別（`docs`、`fix`、`feature`、`refactor`、`test`、`research`、`ops`），然後結束。hook 會立即返回且不輸出任何內容，因此這一切都不會進入代理的上下文。設定 `FREE_HANDS_ESTIMATOR=off` 可關閉估算器。估算器每次執行都是你帳戶上的一個獨立 Claude Code 工作階段（在實測執行中每次約 0.002–0.003 USD 的用量），[budget](../budget) 外掛看不到它。

此後，擁有目標的工作階段的 hook 會為每一項計時：

- `.free-hands/eta.json` 中的工作時間時鐘。回合結束後、新工作階段開始前、你輸入提示之前以及目標暫停期間的時間不計；超過 20 分鐘的空檔，只計入工具呼叫回報自己執行的那部分。
- 每完成一項，在 `.free-hands/timings.jsonl` 中寫一行：項目、實測分鐘數、模型與 effort；估計從 `estimates.jsonl` 合併而來，即使在項目完成之後才到達也會合併。這是專案自己的紀錄：留在專案資料夾中，被 Git 忽略，開始新目標時也會保留。

[dashboard](../dashboard) 以時刻顯示預計完成時間，如 `ETA 15:40`，並在詳情中顯示剩餘分鐘數（`~25m left`）；時刻後的 `+` 表示還有未完成項目沒有估計。自 dashboard 0.3.0 起，項目被勾選或估計到達時，這一行在回合之中也會更新。

預計完成時間是對每個未完成項目求「估計 × 執行工作的模型系列係數 × 本專案係數」之和：

- **模型係數**：在 z-lab 中實測。Haiku 的估計遠長於實際工作：項目實際用時是 Haiku 估計的 Sonnet 0.040、Opus 0.070、Fable 0.074，隨外掛提供的就是這些係數（[`eta-haiku-calibrate-0.6.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-haiku-calibrate-0.6.0)，以 effort xhigh 測得的 26 次目標執行）。沒有實測係數的工作模型（Haiku、Codex 的模型）使用它們的平均值 0.061——這是選擇，不是測量。像 0.5.0 寫下的目標那樣，項目中仍附有代理自己的 `(~6m fix)` 時，這些估計繼續使用 0.5.0 的係數。
- **專案係數**：本專案的項目比模型係數預測的多用或少用了多少時間，從 `timings.jsonl` 最新的 60 行學得；紀錄較少時向 1 收攏。新專案從 1 開始。

當進行中的項目超出了預測，目標的其餘部分很可能也被低估了：此時預計完成時間為該項目再計入一半的已用時間，把後續項目按超出倍數的平方根放大（預測的 2 倍 → ×1.41），並在項目進行中持續變化。以已測量的執行重播，項目超過預測 2 倍時，剩餘時間的誤差減半：真實專案中 0.79 → 0.28 個倍數，實驗中 1.03 → 0.59（[`eta-live-replay-0.7.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-live-replay-0.7.0)，V01）。模型係數是用小型實驗任務（每項 1–3 分鐘）擬合的；在真實的大項目上，在專案紀錄與超出修正趕上之前，目標開始時顯示的預計完成時間仍可能早好幾倍（[`eta-local-replay-0.7.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-local-replay-0.7.0)，L03）。用更大的實驗任務重新測量後，係數維持不變：任務變大時，Haiku 的估計並沒有偏差更大（[`eta-large-calibrate-0.7.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-large-calibrate-0.7.0)，K02、K03）。

## 不提問

目標啟用期間，技能不會向使用者提問。此規則會覆蓋專案與其他技能中的提問要求，也會覆蓋 peer-coding 等工作流程的核准閘門。代理會不經詢問推送分支並建立 PR。失敗的測試、閘門、hook 或審查會修正，或標記為 `- [-]`、需要使用者處理；不會改成通過。其他外掛的 hook 仍會執行。

唯一的例外是 [budget](../budget) 外掛的用量問題：當 budget 因你的用量門檻已達到而攔下某次呼叫時，代理會照它的要求去做——在 Claude Code 的對話框中，或在 Codex 上以該問題結束回合。超出你的門檻繼續花費，是你的決定，不是討論面板的決定。

## Hooks

各 hook 的執行條件不同：

- 下列守衛與恢復備註只在 `owner:` 指定的工作階段及其啟動的子代理中生效。同一儲存庫中的其他工作階段（第二個終端機，或其他工具啟動的 `claude -p`）不會收到恢復備註，也不受提問與停止守衛、計數器及 Shell 守衛約束；當其提示中出現「free-hands」時，開始備註會說明哪個工作階段擁有這次執行。在該工作階段執行 `/free-hands:run`（Codex：`$free-hands:run`）會把執行移到該工作階段。沒有 `owner:` 的目標（例如由 0.2.0 寫入的目標）歸 hook 最先遇到的工作階段所有。
- 只有位於 `## Checklist` 下方、且在程式碼區塊外的 `- [ ]` 行才會計為未完成項目。
- [預計完成時間](#預計完成時間)的時鐘（所有工具的 `PostToolUse`，以及提示、工作階段與停止 hook）與守衛一樣，只在擁有目標的工作階段及其子代理中執行；討論面板的子程序不會寫入時鐘。勾選最後一項並結束執行的那次編輯也會被記錄。同樣的 hook 會啟動估算器，僅在 Claude Code 中，每分鐘最多一次。
- Shell 守衛（`Bash` 的 `PreToolUse`）會在目標為 `active`，或仍有未完成項目的 `done`/`waiting` 時執行。即使沒有剩餘的 `[ ]` 項目或已達 `max_iterations`，也會執行。它會拒絕[限制與狀態](#限制與狀態)所述的硬性限制命令。
- 目標有未完成 `[ ]`、迭代數低於 `max_iterations`，且狀態為 `active`，或為仍有未完成項目的 `done`/`waiting` 時，提問與停止守衛會執行。提問守衛會拒絕提問工具。達到上限後可以提問。Stop hook 會先將計數寫入磁碟再阻止停止，最多延續40次。budget 的用量問題在該工作階段中開啟期間，這兩個守衛都不會生效。
- 目標為 `active` 時會送出恢復備註（`UserPromptSubmit`、包括壓縮後的 `SessionStart`），即使沒有未完成項目也會送出；仍有未完成項目的 `done`/`waiting` 狀態也會送出。
- 沒有有效且啟用中的目標，但提示中出現「free-hands」時，會送出開始備註。背景工作通知不視為提示；提示中引用的通知會被忽略，並讀取提示的其餘部分。

Hook 輸入錯誤時不會產生效果。目標檔案格式錯誤或無法讀取時，不會啟用恢復、提問或停止行為；若提示中含有「free-hands」，提示 hook 會依照沒有啟用中目標的入口路徑處理，並可能送出開始問題。寫入失敗和鎖定逾時也不會產生效果，因此 hook 故障時工具呼叫或停止可以繼續。`eta.json` 或 `timings.jsonl` 損毀時，只是沒有紀錄與預計完成時間，不會改變守衛的判斷。

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

技能與恢復備註為代理設定以下硬性限制：

- 不合併 PR，也不將任何內容合併至預設分支。
- 不以不可逆的方式刪除儲存庫外的檔案、資料、遠端分支或資料庫。
- 不部署、發布或向外部傳送內容（例如版本發佈、套件發佈、電子郵件或訊息）。

這類事項會附上原因並標記為 `- [-]`，然後繼續其他工作。已推送分支允許在先以一行通知後強制推送。允許推送分支、建立 issue 和 PR，以及在其下留言。

自 0.2.0 起，目標啟用期間，shell hook 也會拒絕違反這些限制的常見命令：`gh pr merge`；會更新預設分支的推送與合併（使用目標檔案中的 `default_branch:`，否則使用推送遠端的 HEAD，再否則使用 `main` 和 `master`）；透過 `gh api` 合併及建立發行版本；遠端刪除（`git push --delete`、`:ref`、`--prune`、`--mirror`、`gh repo delete`、`gh release delete`）；以及 `npm`/`pnpm`/`yarn publish`、`cargo publish`、`twine upload`、`gem push`、`docker push`、`docker buildx build --push`、`gh release create`、`vercel` 部署、`netlify deploy`、`fly deploy`、`firebase deploy`、`terraform apply`、`kubectl apply`、`helm install`/`upgrade`、`sendmail`、`mail` 和 `mutt`。除 `sendmail`、`mail`、`mutt` 和 `terraform` 外，`--help`/`-h` 對清單中的所有 CLI 都會通過；`sendmail`、`mail` 和 `mutt` 一律拒絕，`terraform` 的說明旗標是 `-help`；`--dry-run` 對 `git push`、`npm`/`pnpm`/`yarn publish`、`cargo publish`、`kubectl` 和 `helm` 會通過。在兩個宿主上，hook 都於執行前拒絕了 `gh pr merge 1`、`npm publish` 和 `git push origin HEAD:main`，且代理收到了拒絕結果（[z-lab `run-0.2.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/run-0.2.0)，P01–P04）。

此 hook 是協作型代理執行一般命令時的後備防護，不是用來防範蓄意規避——規則禁止規避。它不會讀取 `rm`、資料庫命令、heredoc 內容、腳本（`npm run deploy`）、互動工作階段中輸入的命令，或其他 CLI 與 HTTP 呼叫（`curl`）。

自 0.3.0 起，目標只屬於一個工作階段。在 Claude Code 2.1.296 與 Codex 0.162.1 上每個案例各測量一次（[z-lab `run-0.3.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/run-0.3.0)）：在 0.2.0 下，同一儲存庫中的第二個工作階段接手了執行中的目標並進行其中的工作（O01）；在 0.3.0 下，該工作階段沒有介入目標，目標檔案逐位元組保持不變（O02）；在所屬工作階段及其子代理中，`gh pr merge 1` 仍遭拒絕，而在其他工作階段中會執行（O03–O05）；技能在開始執行時依 hook 備註中的 ID 寫入 `owner:`，接手其他工作階段的執行時替換該值（O06）。兩個主機都會在每個 hook 事件中送出工作階段 ID，並在恢復與壓縮後保持相同的 ID（[`session-id-0.3.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/session-id-0.3.0)，S01–S03）。未測量：兩個工作階段同時執行的情況。

自 0.4.0 起，[budget](../budget) 的問題可以通過，目標也會顯示在 [dashboard](../dashboard) 上。在 Claude Code 2.1.299 與 Codex 0.162.1 上（[z-lab `budget-lab`](https://github.com/zeriong/z-lab/tree/main/budget-lab)、[`dashboard-lab`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab)）：目標執行時，budget 的對話框顯示了出來，而 0.3.0 會將其阻擋；在 Codex 上，被攔住的回合立刻結束，而 0.3.0 的停止守衛讓它又繼續了三次（budget-lab R04、R07、R12；codex-gate B03）。`guard.py status` 在兩個宿主上都給了 dashboard `active 0/40 · 1 open`（dashboard-lab D01、D04）。

自 0.5.0 起，目標會顯示預計完成時間。在 Claude Code 2.1.325 上以 Sonnet、Opus 與 Fable（effort xhigh）在三個規模不同的專案中測量（[z-lab `eta-calibrate-0.5.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-calibrate-0.5.0)、[`eta-validate-r2-0.5.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-validate-r2-0.5.0)）：每次執行中，hook 測得的時間與獨立紀錄相差都在 0.1 分鐘以內（E01）。在擬合係數時未使用的目標上，模型係數把中位誤差從 3.2 個倍數降到 0.6（約 1.5 倍）——原始估計約長了 9 倍（W01）。寫下清單時顯示的剩餘時間，按中位數在實際用時的 1.42 倍以內，13 個目標中有 12 個在 2 倍以內（W04）。在這些執行中，專案係數對 Sonnet 有幫助、對 Opus 有害（W03），因此不宣稱它帶來改進。每完成一項，dashboard 的這一行都在回合之中更新（[`dashboard-lab/run-0.3.0`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab/run-0.3.0)，D09）。未測量：Codex、Haiku、其他 effort 等級、紀錄更長的專案。

自 0.6.0 起，估計由那個隔離的估算器給出。在 Claude Code 2.1.325 上以 Sonnet 進行兩次無介面 free-hands 執行與一次互動工作階段測量（[z-lab `eta-isolated-run-r2-0.6.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-isolated-run-r2-0.6.0)）：執行工作的代理的輸出流中完全沒有出現與估計相關的內容，free-hands hook 的輸出中也沒有（J01）；估算器在清單寫下約 6 秒後作答，沒有留下錯誤，也沒有保存工作階段（J02）；這一行在提示後 2 秒顯示 `ETA`，並隨每完成一項而改變（J04）。估算器每次執行花費 0.002–0.003 USD。在擬合係數時未使用的目標上，Haiku × 係數的中位誤差按項目為 0.68 個倍數、按目標為 0.66，而 0.5.0 中代理自己的估計為 0.62 與 0.51——把估計移出代理的上下文會損失一點精度（[`eta-haiku-calibrate-0.6.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-haiku-calibrate-0.6.0)，H04、H05）。一邊勾選一邊改寫項目文字的代理，會依位置對應為同一項目；這一修正透過重播已記錄的執行確認，沒有用新的執行確認（J05）。

若要暫停，請說 **「pause」**、**「stop」** 或 **「일시정지」**。目標會記錄為 `paused`；再次執行命令即可恢復。

來源：由專案本機技能移植而來。

## Codex

依賴自動執行前，請在 `/hooks` 信任外掛 hooks。提問 hook 的 matcher 包含 `request_user_input`；尚未觀察到拒絕。Codex 預設模式沒有提問工具，因此由 Stop hook 負責延續工作。若未信任或啟用 hooks，技能仍依照書面規則繼續，但 hook 效果可能未生效。在 Codex 上 hooks 仍會為項目計時，但不會啟動估算器——hook 只在 `CLAUDECODE=1` 且父程序為 `CLAUDE_PID` 時啟動它，從 Claude Code 內部啟動的 Codex 工作階段即使繼承了這些值，父程序也對不上——因此除非目標由 0.5.0 寫下並附有內嵌估計，否則不會顯示預計完成時間；可以用 `$dashboard:audit` 查看現有內容（Codex 沒有即時顯示行）。未在 Codex 上測量。

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
