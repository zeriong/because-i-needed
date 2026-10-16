<p align="center"><strong>budget</strong></p>

<p align="center">僅適用於 <strong>Claude Code</strong> 和 <strong>Codex CLI</strong>。</p>

<p align="center"><strong>指定用量額度的一個比例；達到時，每個執行中的工作階段都會停下來，詢問是否繼續。</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.1.1-blue" alt="版本"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="授權：MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code 外掛"></a></p>

<p align="center"><a href="#開始">開始</a> &bull; <a href="#運作方式">運作方式</a> &bull; <a href="#設定與狀態">設定與狀態</a> &bull; <a href="#限制與狀態">限制與狀態</a> &bull; <a href="#需求">需求</a> &bull; <a href="#安裝">安裝</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub><a href="../../README.zh-TW.md">because-i-needed</a> 的一部分</sub></p>

---

budget 會監看你的帳號回報的用量額度，並讓每個工作階段都停在你選定的比例。額度達到該比例時，每個執行中的工作階段的下一次工具呼叫（包括其子代理的呼叫）都會等待一個問題：**"지정한 n%에 도달했습니다, 작업을 이어서 진행하시겠어요?"**（你已達到設定的 n%，要繼續工作嗎？）。回答 예 繼續，回答 아니오 停止。[dashboard](../dashboard) 外掛會顯示你設定的門檻。

## 開始

- Claude Code：`/budget:mode 80` · Codex：`$budget:mode 80` — 在 80% 時停下並詢問。
- `/budget:mode off` 關閉；`/budget:mode status` 顯示門檻與最近一次測得的額度。
- 門檻是你的使用者帳號的單一設定，由 Claude Code 與 Codex 共用。

## 運作方式

**Claude Code** 測量**五小時**額度。Claude Code 會在每個回合之後，以及額度每變動一個整數百分點時，向外掛回報。當額度達到或超過門檻時，budget 會攔住下一次工具呼叫，並在 Claude Code 自己的提問對話框中詢問（標籤 `budget`，選項 예 與 아니오）。

- 예：該呼叫繼續執行，在額度重置之前不會再次詢問該工作階段。
- 아니오：該呼叫被拒絕，回合停止。
- 一個問題會回答它開啟期間到來的所有呼叫，因此平行的子代理只會被問一次。
- 沒有人可回答的執行（`claude -p`）與被關閉的對話框都視為 아니오。

**Codex** 測量 **7 天**額度，這是 Codex 唯一回報的額度。budget 會讀取帳號近期工作階段紀錄（`~/.codex/sessions`）中最新的數值，因此新的工作階段從第一次呼叫起就會被攔住。Codex 沒有外掛可以開啟的對話框，所以 budget 會拒絕該呼叫，並告訴代理以同一個問題結束它的回合。回答 예（也可以是 `네`、`yes`、`y`、`계속`、`continue`）繼續；任何其他回答都會讓工作階段維持停止。請先在 `/hooks` 中信任該外掛的 hook。

**搭配 [free-hands](../free-hands)：** free-hands 在目標進行期間從不提問，唯一的例外就是這個問題。當 budget 的問題在某個工作階段中開啟時，free-hands 0.4.0 會讓它通過，且不會讓回合繼續。

## 設定與狀態

- `~/.config/because-i-needed/budget.json`（設定了 `$XDG_CONFIG_HOME` 時位於其下）：`{"percent": 80}`。`/budget:mode` 會寫入它；`off` 會移除它。
- `~/.config/because-i-needed/budget/`：工作階段的問題開啟期間有 `pending/<session>.json`，針對某個額度回答 예 之後有 `acks/<session>.json`，以及 `usage.json`，記錄宿主最近回報的額度（dashboard 會顯示它）。
- 新的額度視窗會再次詢問。重置時間只差幾秒視為同一個額度視窗，因為 Codex 回報的重置時間在兩次讀取之間會有一秒的偏移。

## 限制與狀態

每個案例各測量一次，環境為 Claude Code 2.1.299 與 Codex 0.162.1（[z-lab `budget-lab`](https://github.com/zeriong/z-lab/tree/main/budget-lab)：`run-0.1.0`、`run-0.1.0-r2`；其依據的事實位於 `codex-gate-0.1.0`、`codex-gate-0.1.0-r2` 和 z-lab `plugin-platform-lab/mod-interactive-2.1.299`）：

- Claude Code 顯示了對話框；예 讓呼叫執行，아니오 讓回合停止（"Interrupted"）。低於門檻時沒有任何動作。兩個平行的子代理只被問了一次。回答 예 之後，後續呼叫沒有再被詢問就執行了（R01–R05、R10）。
- Codex 以該問題結束回合，且沒有執行任何東西。예 解除了該工作階段的鎖定，後續呼叫沒有再被詢問就執行了；低於門檻時沒有任何動作（R06、R09、R11）。
- 在 free-hands 執行目標時，Claude Code 上顯示了該問題。在 Codex 上，被攔住的回合立刻結束；在 free-hands 0.3.0 下，停止守衛讓它又繼續了三次（R04、R07、R12；codex-gate B03）。

未測量：回合已在執行時才越過門檻（回合可能在 Claude Code 下一次回報之前就超過門檻）；多個互動式工作階段同時執行；在門檻處執行的 `claude -p`；Codex 的五小時額度（受測帳號未回報）；透過 `/hooks` 信任而非略過的 Codex hook。

budget 所使用的 Claude Code 外掛 hooks 模組 API 標示為搶先體驗，各版本之間可能變動。

## 需求

- 支援外掛 hooks 模組的 Claude Code（於 2.1.299 上測量）或 Codex CLI（於 0.162.1 上測量）。
- `PATH` 中要有 `python3`，供 Codex hook 與 `/budget:mode` 使用。

## 安裝

先新增市集，再安裝外掛：

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install budget@because-i-needed
```

Codex 請參閱[市集說明](../../README.zh-TW.md#codex)。

## 授權

MIT。請參閱 [LICENSE](../../LICENSE)。
