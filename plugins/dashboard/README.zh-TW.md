<p align="center"><strong>dashboard</strong></p>

<p align="center">僅適用於 <strong>Claude Code</strong> 和 <strong>Codex CLI</strong>。</p>

<p align="center"><strong>用一行看到你開啟的每個 because-i-needed 模式，以及每個值的來源。</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.1.0-blue" alt="版本"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="授權：MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code 外掛"></a></p>

<p align="center"><a href="#顯示內容">顯示內容</a> &bull; <a href="#claude-code">Claude Code</a> &bull; <a href="#codex">Codex</a> &bull; <a href="#外掛如何加入">外掛如何加入</a> &bull; <a href="#限制與狀態">限制與狀態</a> &bull; <a href="#安裝">安裝</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub><a href="../../README.zh-TW.md">because-i-needed</a> 的一部分</sub></p>

---

because-i-needed 的外掛有一些會持續保持設定的開關——peer-coding 的協作編排模式、free-hands 的目標、budget 的門檻——設定在專案或使用者層級。dashboard 會把它們全部顯示出來，讓開關不會在你不知情的情況下開著。

## 顯示內容

```
because-i-needed │ budget 80% · 5h now 20% │ free-hands active 0/40 · 1 open (project) · owner lab-sess │ peer-coding on (project)
```

- 每個已啟用的 because-i-needed 外掛所宣告的開關各佔一項：它的值、由哪個層級決定時顯示 `(project)` 或 `(env)`，以及一項細節，例如最近一次測得的用量額度或目標所屬的工作階段。
- 沒有任何已啟用的外掛宣告開關時，不顯示任何內容。
- `/dashboard:audit`（Claude Code）或 `$dashboard:audit`（Codex）會印出同一行，並針對每個開關印出專案層級與全域層級所設定的值。它不會變更任何東西。

## Claude Code

這一行位於提示上方。它會在工作階段開始時、每個回合之後以及用量額度變動時更新。dashboard 會找出 Claude Code 已安裝並啟用的 because-i-needed 外掛。

## Codex

Codex 沒有給外掛繪製的位置，所以在 Codex 上，dashboard 就是 `$dashboard:audit` 命令。若要隨時看到用量額度，請在 `~/.codex/config.toml` 中（或用 `/statusline`）開啟 Codex 自己的狀態列項目：

```toml
[tui]
status_line = ["model-with-reasoning", "weekly-limit"]
```

它顯示的是 7 天額度**剩下**多少（例如 `weekly 28% left`），而不是已使用多少。未知的項目 ID 會被丟棄並顯示警告。

## 外掛如何加入

外掛在其根目錄的 `dashboard.json` 中宣告自己的開關。每個具有 `mode` 技能的 because-i-needed 外掛都必須宣告，其他外掛可以自行選擇（本儲存庫的 Rule 11）：

```json
{ "entries": [ { "label": "peer-coding", "status": ["bash", "scripts/mode.sh", "status", "--json"] } ] }
```

`status` 命令是唯讀的，在專案目錄中執行，並印出一個 JSON 物件：`value`、`source`（`env`、`project`、`global` 或 `default`）、`project` 與 `global`（各層級的值，或 `null`），以及選用的 `detail`。命令失敗、執行超過兩秒或印出其他內容時，會顯示為 `error`。之後新增的外掛不需要 dashboard 發佈新版本就會出現。

以 `claude --plugin-dir` 從資料夾載入的外掛不在 Claude Code 的安裝紀錄中；若要顯示它們，請把它們的資料夾列在 `BECAUSE_I_NEEDED_PLUGIN_DIRS`（分隔方式與 `PATH` 相同）。

## 限制與狀態

每個案例各測量一次，環境為 Claude Code 2.1.299 與 Codex 0.162.1（[z-lab `dashboard-lab/run-0.1.0`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab/run-0.1.0)；Codex 狀態列見 [`codex-status-line-0.162.1`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab/codex-status-line-0.162.1)）：

- 在 Claude Code 上，上方那一行顯示了 budget、free-hands 和 peer-coding，`/dashboard:audit` 印出了各個層級；沒有宣告開關的外掛時就沒有那一行（D01–D03）。
- 在 Codex 上，`$dashboard:audit` 從已安裝的外掛印出了相同的項目，其中 budget 項目帶有 7 天額度；沒有宣告開關的外掛時，它會如此說明（D04–D05）。
- Codex 的 `weekly-limit` 項目顯示了 `weekly 28% left`（C02）。

未測量：透過 Claude Code 市集安裝的外掛（受測的那一行讀取的是 `--plugin-dir` 資料夾；安裝紀錄有單元測試）；工作階段中途開關變更後那一行是否更新；桌面與 IDE 介面。

繪製那一行的 Claude Code 外掛 hooks 模組 API 標示為搶先體驗，各版本之間可能變動。

## 安裝

先新增市集，再安裝外掛：

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install dashboard@because-i-needed
```

Codex 請參閱[市集說明](../../README.zh-TW.md#codex)。`python3` 必須在 `PATH` 中。

## 授權

MIT。請參閱 [LICENSE](../../LICENSE)。
