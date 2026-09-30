<p align="center">
  <strong>claude-x-codex</strong>
</p>

<p align="center">
  <strong>Claude × Codex 同儕編排——兩個代理以同儕身分互相規劃、實作與審查彼此的工作。</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.2.0-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a>
</p>

<p align="center">
  <a href="#安裝">安裝</a> &bull;
  <a href="#命令">命令</a> &bull;
  <a href="#運作方式">運作方式</a> &bull;
  <a href="#設定">設定</a> &bull;
  <a href="#平台">平台</a>
</p>

<p align="center">
  <a href="README.md">English</a> &bull;
  <a href="README.ko.md">한국어</a> &bull;
  <a href="README.ja.md">日本語</a> &bull;
  <a href="README.zh-CN.md">简体中文</a> &bull;
  <a href="README.zh-TW.md">繁體中文</a>
</p>

<p align="center">
  <sub><a href="../../README.zh-TW.md">because-i-needed</a> 的外掛</sub>
</p>

---

**C**laude **×** **C**odex 同儕編排。基礎不同的兩個代理會以不同的方式出錯，所以它們互相審查對方的工作——主代理自己的計畫也不例外。兩者意見分歧時，由測試而不是角色來裁定。

claude-x-codex 是非官方的社群外掛，並非由 Anthropic 或 OpenAI 製作、認可或提供支援。

## Codex

需要 Codex CLI 0.158.0 或更高版本。安裝後請啟動新工作階段。Claude 使用 `/plugin:skill`，Codex 使用 `$plugin:skill`。共用技能和資源均包含在此外掛內。依賴自動行為前，請在 `/hooks` 中審核並信任隨附的掛鉤。

```bash
codex plugin marketplace add https://github.com/zeriong/because-i-needed.git
codex plugin add claude-x-codex@bin
```

使用 `$claude-x-codex:run`、`$claude-x-codex:mode on|off|status|clear` 和 `$claude-x-codex:audit`。兩個宿主的模式操作都需要使用者明確要求。Codex 可以擔任主代理，既有 Codex 配接器保持跨廠商評審。稽核包含 `.codex/hooks.json` 及未提交的 `.codex/`、`.agents/` 上下文。自動模式需要信任 UserPromptSubmit 掛鉤，明確呼叫 run 不依賴它。Codex 為主代理時，跨廠商工作需要 Claude CLI；缺少時使用既有單廠商備用路徑。

### Codex 設定

兩端使用相同的 `CXC_*` 設定、模式範圍及跨供應商審查規則。連結的 Git worktree 中也會在本機排除模式檔案。稽核不修改設定，並回報 `AGENTS.override.md` 的優先順序及無效的掛鉤宣告。

各宿主的路由使用設定的 CXC 評審模型與推理強度，括號內僅為預設值。只提及檔名或 fallback 設定不會被判定為指令一致，而會標為 CHECK，要求核對實際生效內容。

## 命令

| 命令 | 作用 |
|---|---|
| `/claude-x-codex:run` | 編排一項任務：主代理負責規劃並做出每個關卡的決定，把工作分派到 `claude-fast` / `codex-bulk` / `main` 通道，並讓每個廠商審查另一個廠商的工作 |
| `/claude-x-codex:mode on\|off\|status\|clear [--global]` | 開啟或關閉自動編排的一行開關。僅限使用者操作，模型無法切換 |
| `/claude-x-codex:audit` | 以唯讀方式檢查兩個廠商是否從相同的專案脈絡出發；只提出修正建議，不做任何變更 |

`on`、`off` 會寫入本專案的旗標（`.claude-x-codex/mode`，已排除在 git 之外）；`--global` 會寫入對所有專案生效的預設值（`~/.config/claude-x-codex/mode`）；`clear` 會刪除專案旗標；`CXC_MODE=on|off` 在單一 shell 中優先於兩者。模式關閉時，`run` 只在你明確要求時才啟動。

## 安裝

### 透過 Claude Code 外掛市集

1. 在 Claude Code 中執行 `/plugin`。
2. Marketplaces → Add Marketplace。
3. 輸入 URL：`https://github.com/zeriong/because-i-needed.git`（或本儲存庫的本機路徑）。
4. 安裝 `claude-x-codex`。

### 或透過 CLI

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git   # 或本機路徑
claude plugin install claude-x-codex@bin
```

### 或直接寫入 `~/.claude/settings.json`

```json
{
  "extraKnownMarketplaces": {
    "bin": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": { "claude-x-codex@bin": true }
}
```

- **注意：** 安裝後會註冊一個 `UserPromptSubmit` hook。它會在每則提示時執行，模式關閉時不輸出任何內容；模式開啟時，會加入一段四行的提示（每則提示約 100 個輸入 token），把實作類工作轉交給 `run`。

## 需求

- **Claude Code**（或作為主代理的 Codex）、一個 **git** 儲存庫，以及 bash 3.2+。
- **選用——Codex CLI**（`codex`）。沒有它時，`run` 會切換到 single-vendor 模式，把所有審查交給同一廠商的另一個審查者實例，並告知你這一點。
- **選用——Orca**（已啟用編排）。有了它，工作者可以在任務進行中提問，關卡會等待你的決定；沒有它時，工作者以子代理或 CLI 呼叫的方式單向執行。
- 稽核的 hook 表需要 `python3`；當 Codex 作為主代理執行 Claude 審查者時需要 `jq`。
- 已在 Claude Code 2.1.283、Codex CLI 0.157.1 與 Orca 1.4.215 上驗證。

## 運作方式

- **通道**——工作者以 effort `high` 執行。`claude-fast`（Claude Sonnet：UI、互動、程式碼品味、Claude 端的工具）、`codex-bulk`（Codex `gpt-6-luna`：結果已完全確定的工作，例如針對既有契約的測試、型別與機械式遷移）、`main`（主代理：緊密耦合的工作，或規格仍在摸索中的工作）。
- **跨廠商審查**——審查者一定與作者屬於不同廠商，主代理自己的計畫與分流決定也交給另一個廠商審查。Claude 以 Opus、Codex 以 `gpt-6-sol` 審查，兩者的 effort 都是 `xhigh`——在兩個 CLI 中都是僅次於 `max` 的等級。即使是認證、付款、資料遷移等高風險階段，在追加頂級模型（`gpt-6-astra` 或 `max` 的 Opus）審查之前也會先詢問你，絕不自行升級。審查者以唯讀方式執行，回傳由兩個 CLI 以 schema 強制約束的 JSON。
- **一輪反駁**——被駁回的 blocking 或 major 意見會連同理由退回給審查者一次。審查者要麼認同，要麼以新證據反駁；仍未解決時，會連同雙方論點以 DISPUTED 交給你決定。
- **證據說了算**——出現分歧時，握有測試、重現或追蹤的一方勝出。沒有證據時由你決定。
- **脈絡橋接**——稽核會找出兩個廠商讀取不同指示檔的位置、只約束一個廠商的 hook，以及工作者的 worktree 中會缺少的未提交脈絡。`run` 發出的 Codex 呼叫透過 Codex 的後備設定讀取 `CLAUDE.md`，不需修改儲存庫；互動式 Codex 工作階段（Orca 工作者，或作為主代理的 Codex）需要在你的 Codex 設定中加入同樣的設定。任何需要修改你的設定或儲存庫的調整都會在計畫核准時提出。
- **狀態寫入磁碟**——`.claude-x-codex/`（已排除在 git 之外）保存計畫、決定與審查，因此一次執行在脈絡壓縮後仍可恢復。

與 [plan-smith](../plan-smith) 一起安裝時，規劃步驟會使用 `/plan-smith:forge`——只要有專用的規劃技能，`run` 就會把規劃交給它。

## 設定

`run` 會從環境變數讀取以下值，未設定時使用預設值：

| 變數 | 預設值 |
|---|---|
| `CXC_WORKER_MODEL` | `gpt-6-luna` |
| `CXC_REVIEW_MODEL` | `gpt-6-sol` |
| `CXC_FINAL_MODEL` | `gpt-6-astra` |
| `CXC_CLAUDE_WORKER` | `sonnet` |
| `CXC_CLAUDE_REVIEWER` | `opus` |
| `CXC_REVIEW_EFFORT` | `xhigh` |
| `CXC_WORKER_EFFORT` | `high` |
| `CXC_MAX_CYCLES` | `3` |
| `CXC_PARALLEL` | `3` |

CXC = **C**laude **×** **C**odex——你在 shell 中設定的變數的前綴。

## 平台

腳本是只使用 POSIX 工具的 bash（相容 macOS 的 bash 3.2 與 BSD 工具）。

| 平台 | 狀態 |
|---|---|
| Linux | 支援 |
| macOS | 支援 |
| Windows + WSL | 支援（行為與 Linux 相同） |
| Windows + Git Bash | 應可運作；路徑遵循 Git Bash（`~` = `/c/Users/<you>`） |
| 僅 Windows PowerShell / cmd | 不支援——請安裝 Git for Windows 或使用 WSL |

在 Windows 上，腳本必須維持 LF 換行。外掛的 `.gitattributes` 會強制這一點；若你不透過 git 複製檔案，請把換行字元轉換為 LF。

## 授權

MIT。請參閱 [LICENSE](../../LICENSE)。
