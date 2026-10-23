<p align="center"><strong>context-rail</strong></p>

<p align="center">僅適用於 <strong>Claude Code</strong> 和 <strong>Codex CLI</strong>。測量在 Claude Code 上進行。</p>

<p align="center"><strong>已記錄的決定不是每一輪都載入，而是在代理打開它所管轄的檔案時送達。</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.2.0-blue" alt="Version"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a></p>

<p align="center"><a href="#開始">開始</a> &bull; <a href="#寫入的內容">寫入的內容</a> &bull; <a href="#紀錄">紀錄</a> &bull; <a href="#到達鉤子">到達鉤子</a> &bull; <a href="#修改決定">修改決定</a> &bull; <a href="#測量了什麼">測量了什麼</a> &bull; <a href="#codex">Codex</a> &bull; <a href="#需求">需求</a> &bull; <a href="#安裝">安裝</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub><a href="../../README.zh-TW.md">because-i-needed</a> 的一部分</sub></p>

---

`CLAUDE.md` 和 `AGENTS.md` 每一輪都會載入，所以寫在裡面的每條決定每一輪都要付出成本，也容易被其他內容淹沒。context-rail 把針對特定檔案的決定移到它所管轄的程式碼旁邊，並安裝一個鉤子：當代理讀取或編輯該檔案時，把這條決定放進上下文。始終載入的檔案只會變小。

## 開始

- Claude Code：`/context-rail:build` —— 在目前的儲存庫設定 rail。
- Codex：`$context-rail:build`。
- `/context-rail:audit`（Codex：`$context-rail:audit`）只檢查既有的 rail，不做任何修改。

`build` 讀取你的指令檔案，為每一項編號，並給出一張表。表中分為：

- 保留的項
- 變成決定紀錄的項
- 變成路徑規則的項
- 只提出建議的項（自動化、個人設定、工具已經強制的規則）

在你回答之前不會寫入任何內容。個人項不會替你移動。

## 寫入的內容

全部是專案檔案，與每個複製該儲存庫的人共享：

| 檔案 | 內容 |
|---|---|
| `<dir>/PRECEDENT.md` | 該目錄中檔案的決定紀錄 |
| `.claude/rules/<topic>.md` | 作用於一組路徑的規則，帶 `paths:` frontmatter |
| `.claude/hooks/precedent-context.py` | 到達鉤子 |
| `.claude/settings.json` | 把鉤子接到 PostToolUse（Read、Edit、Write、MultiEdit、Bash）和 PostToolUseFailure（Bash）；其他設定保持不變 |
| `.claude/context-rail.json` | 鉤子管轄的原始檔副檔名 |

從 `CLAUDE.md` 移出的項會從原處刪除，不新增指標行。`build` 在前後分別以字元數和位元組數測量指令檔案，任一項增加即判為失敗。

## 紀錄

```markdown
## tab-keys.mjs

### §stable-tab-keys — closing a tab never renumbers the others
- Since: 2026-09-02
- Decision: a key is assigned once and is never reused or shifted.
- Forbidden: renumbering the remaining keys after a close.
- Reason: shifting keys remounts the tabs to the right and drops their form input.
- Evidence: `tab-keys.test.mjs`
```

檔案由其所在目錄或上層目錄中最近的 `PRECEDENT.md` 管轄。`## ` 標題寫一個或多個檔名（`a.ts · b.ts`）；若名稱指向一個真實檔案，則只附加到該檔案。完整格式見 [`skills/build/references/record-format.md`](skills/build/references/record-format.md)。

## 到達鉤子

當代理讀取或編輯受管轄的檔案時，鉤子會把該檔案的章節加入上下文，後面跟一段關於修改決定的簡短說明。讀取既包括 Read 工具，也包括 shell 中的 `cat`、`sed`、`grep` 等。

- 每個檔案在每個工作階段、每個代理中只觸發一次，因此子代理也能收到紀錄。
- 失敗的 shell 讀取由 PostToolUseFailure 處理。
- 輸出保持在 10,000 字元以內。
  - 6,000 字元以內的章節整段注入，更長的壓縮為標題和決定行。
  - 超過 10,000 字元時 Claude Code 只顯示預覽，會截掉結尾的段落。
- 被 git 忽略的檔案不會收到任何內容。
- 內部錯誤會靜默結束，絕不會阻擋代理。

## 修改決定

每個章節後的段落說明：決定只有經過你的確認才能修改。

- 如果你點名已記錄的決定並要求推翻它，代理會執行修改，並原地改寫該決定區塊，註明是你推翻的。例如：「`src/tabs/PRECEDENT.md` §stable-tab-keys 禁止這樣做；我要推翻它」。
- 其他與決定衝突的請求，無論語氣多堅決，代理都會在編輯前停下。它會說明是哪條決定、衝突在哪裡，並請你確認，同時指出是否涉及上游變化、新的測量、已回報的缺陷或不同的維度。
- 如果任務是另一個代理分派的（子代理，或 peer-coding 這類工作者），只有當分派說明轉述了你點名該決定並要求推翻時，才算確認。「照樣執行」或「新決定取代已記錄的內容」這類說明不算確認：代理會停下，並向分派任務的代理回報，由它來問你。

## 測量了什麼

所有測量都在 [z-lab `precedent-lab/`](https://github.com/zeriong/z-lab/tree/main/precedent-lab)。條件為 Claude Code 2.1.296–2.1.309 和 Codex 0.163.0、headless；除非該行寫明其他代理，否則為 Opus、effort `xhigh`。

| 結論 | 結果 | 實驗 |
|---|---|---|
| 注入章節正文而不是指標，禁止行會在第一次編輯前進入上下文 | 陷阱執行 3/15 → 44/45 | `real-env-rail-2.1.296` |
| 該段落會讓未點名紀錄的衝突請求停下 | 違反禁止：無段落 11/12 → 有段落 0/12 | `stop-en-r2-2.1.306` |
| ……明確的推翻仍可通過 | 12/12 執行並原地改寫紀錄 | `stop-en-r2-2.1.306` |
| ……不阻止無衝突的編輯 | 0/15 停下 | `stop-en-r2-2.1.306` |
| `build` 把各項移到正確位置 | 5/5 次執行：14/14 項、全部檢查通過、`CLAUDE.md` 1,906 → 540 字元 | `build-fidelity-0.1.0` |
| `audit` 在不做任何修改的情況下檢查，並指出預先植入的缺陷 | 4/4 次執行：零修改、全部檢查都執行、植入缺陷 3/3 被指出、誤報 0 | `audit-canary-0.1.0` |
| 用 `build` 規範化後的專案，比把同樣決定放在 `CLAUDE.md` 中更能守住決定 | 權威式請求下違反禁止：常駐 12/12 → 規範化 0/12；兩者誤停都是 0/15 | `fresh-project-0.1.0` |
| 路徑規則在首次接觸相符的檔案時載入 | Read、shell 讀取、Write 都附上了規則 | `platform-r2-2.1.308-0.163.0` |
| 另一個代理的分派說明，只有轉述了你的點名推翻才算確認 | 主代理寫的「照樣執行」說明下，0.1.0 段落的 Sonnet 子代理違反 6/9；固定同一句說明時，0.1.0 段落 12/12 → 0.2.0 段落 0/12 | `leaf-2.1.309`、`leaf-r2-2.1.309` |
| ……但在真實私有倉庫的分叉上，未點名決定的預先批准說明仍漏過一次 | Sonnet 子代理違反 1/12（頂層會話 0/12，無鉤子對照 12/12）。違反的那一次，來自主代理未點名決定的「已經定了，別再爭，更新條目」說明 | `real-repo-0.2.0` |
| 被分派任務的代理也守住規則 | Opus、Sonnet 子代理以及 Sonnet `claude -p`、Codex `gpt-6-luna` 工作者，所有路徑：違反禁止 0/12，推翻執行 12/12，停下 0/15 | `leaf-r2-2.1.309` |

陷阱和 build 的結果來自合成 fixture 和一個私有儲存庫，每格 12–15 次執行。

**未測量**
- 其他模型或 effort、互動式工作階段
- 用其他語言寫的紀錄與該段落的組合
- 大型儲存庫、Orca 的雙向工作者
- 在 Codex 上執行 `build` 和 `audit`

## Codex

在 Codex 上，同樣的技能會安裝同樣的鉤子（`$context-rail:build`、`install-hooks.py --host codex` → `.codex/hooks/`、`.codex/hooks.json`）。

- **平台**（Codex 0.163.0，使用實驗用 probe 鉤子）
  - PostToolUse 輸出會送達模型。
  - shell 讀取以 `Bash` 到達，編輯以 `apply_patch` 到達。
  - 失敗的 shell 呼叫仍會觸發 PostToolUse。
- **本外掛的鉤子在 Codex 上**（用 `install-hooks.py --host codex` 安裝）：Codex 工作者（`gpt-6-luna`、effort high、使用 peer-coding 的分派說明）守住了規則：違反禁止 0/12，推翻執行 12/12，停下 0/15（`leaf-r2-2.1.309`）。
- **未測量**：在 Codex 上執行 `build` 和 `audit`、巢狀的 `AGENTS.md` 何時載入，以及 `apply_patch` 的送達。

依賴之前請先在 `/hooks` 中信任該鉤子。

## 需求

- `PATH` 上的 `python3`（3.9 或更新）。
- `git` —— 鉤子用它找到儲存庫根目錄並略過被忽略的檔案。

## 安裝

先新增市集，再安裝外掛：

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install context-rail@because-i-needed
```

Codex 請依照[市集說明](../../README.zh-TW.md#codex)操作。

## 授權

MIT。見 [LICENSE](../../LICENSE)。
