<p align="center">
  <strong>peer-coding</strong>
</p>

<p align="center">僅適用於 <strong>Claude Code</strong> 和 <strong>Codex CLI</strong>。</p>

<p align="center">
  <strong>Claude × Codex 同儕編排——兩個代理以同儕身分互相規劃、實作與審查彼此的工作。</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-1.2.0-blue" alt="Version"></a>
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

Claude × Codex 同儕編排。基礎不同的兩個代理會以不同的方式出錯，所以它們互相審查對方的工作——主代理自己的計畫也不例外。兩者意見分歧時，由測試而不是角色來裁定。

peer-coding 是非官方的社群外掛，並非由 Anthropic 或 OpenAI 製作、認可或提供支援。

## Codex

需要 Codex CLI 0.158.0 或更高版本。安裝後請啟動新工作階段。Claude 使用 `/plugin:skill`，Codex 使用 `$plugin:skill`。共用技能和資源均包含在此外掛內。依賴自動行為前，請在 `/hooks` 中審核並信任隨附的掛鉤。

```bash
codex plugin marketplace add https://github.com/zeriong/because-i-needed.git
codex plugin add peer-coding@because-i-needed
```

使用 `$peer-coding:run`、`$peer-coding:mode on|off|status|clear`、`$peer-coding:mode <setting> <value>` 和 `$peer-coding:audit`。兩個宿主的模式操作都需要使用者明確要求。Codex 可以擔任主代理，既有 Codex 配接器保持跨廠商評審。稽核包含 `.codex/hooks.json` 及未提交的 `.codex/`、`.agents/` 上下文。自動模式需要信任 UserPromptSubmit 掛鉤，明確呼叫 run 不依賴它。Codex 為主代理時，跨廠商工作需要 Claude CLI；缺少時使用既有單廠商備用路徑。

### Codex 設定

兩端使用相同的模型設定、模式範圍及跨供應商審查規則。Codex 沒有外掛設定選單，因此使用 `$peer-coding:mode <setting> <value>` 設定模型與推理強度（見[設定](#設定)）；在 Claude Code 的 `/config` 中選擇的值也適用於此。 連結的 Git worktree 中也會在本機排除模式檔案。稽核不修改設定，並回報 `AGENTS.override.md` 的優先順序及無效的掛鉤宣告。

各宿主的路由使用設定的 審查模型與推理強度，括號內僅為預設值。只提及檔名或 fallback 設定不會被判定為指令一致，而會標為 CHECK，要求核對實際生效內容。

## 命令

| 命令 | 作用 |
|---|---|
| `/peer-coding:run` | 編排一項任務：主代理負責規劃並做出每個關卡的決定，把工作分派到 `claude-fast` / `codex-bulk` / `main` 通道，並讓每個廠商審查另一個廠商的工作 |
| `/peer-coding:mode on\|off\|status\|clear [--global]` | 開啟或關閉自動編排的一行開關。僅限使用者操作，模型無法切換 |
| `/peer-coding:mode <setting> <value>\|unset [--global]` | 選擇工作者通道或審查者的模型系列或推理強度（[設定](#設定)）；`status` 列出全部六項 |
| `/peer-coding:audit` | 以唯讀方式檢查兩個廠商是否從相同的專案脈絡出發；只提出修正建議，不做任何變更 |

`on`、`off` 會寫入本專案的旗標（`.claude-x-codex/mode`，已排除在 git 之外）；`--global` 會寫入對所有專案生效的預設值（`~/.config/claude-x-codex/mode`）；`clear` 會刪除專案旗標；`CXC_MODE=on|off` 在單一 shell 中優先於兩者。模式關閉時，`run` 只在你明確要求時才啟動。[dashboard](../dashboard) 外掛會顯示目前生效的模式及其來源，以及工作者和審查者的模型與推理強度（`mode.sh status --json` 和 `settings.py status --json`，在 `dashboard.json` 中宣告）。

## 安裝

### 透過 Claude Code 外掛市集

1. 在 Claude Code 中執行 `/plugin`。
2. Marketplaces → Add Marketplace。
3. 輸入 URL：`https://github.com/zeriong/because-i-needed.git`（或本儲存庫的本機路徑）。
4. 安裝 `peer-coding`。

### 或透過 CLI

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git   # 或本機路徑
claude plugin install peer-coding@because-i-needed
```

### 或直接寫入 `~/.claude/settings.json`

```json
{
  "extraKnownMarketplaces": {
    "because-i-needed": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": { "peer-coding@because-i-needed": true }
}
```

- **注意：** 安裝後會註冊一個 `UserPromptSubmit` hook。它會在每則提示時執行，模式關閉時不輸出任何內容；模式開啟時，會加入一段四行的提示（每則提示約 100 個輸入 token），把實作類工作轉交給 `run`。

## 需求

- **Claude Code**（或作為主代理的 Codex）、一個 **git** 儲存庫，以及 bash 3.2+。
- **選用——Codex CLI**（`codex`）。沒有它時，`run` 會切換到 single-vendor 模式，把所有審查交給同一廠商的另一個審查者實例，並告知你這一點。
- **選用——Orca**（已啟用編排）。有了它，工作者可以在任務進行中提問，關卡會等待你的決定；沒有它時，工作者以子代理或 CLI 呼叫的方式單向執行。
- 模型設定、最新模型解析器和稽核的 hook 表需要 `python3`；當 Codex 作為主代理執行 Claude 審查者時需要 `jq`。
- 已在 Claude Code 2.1.283、Codex CLI 0.157.1 與 Orca 1.4.215 上驗證；模型設定和 `/config` 選擇項也在 Claude Code 2.1.314 和 Codex CLI 0.166.0 上驗證。

## 運作方式

- **通道**——工作者以工作者 effort（預設為 `high`）執行。`claude-fast`（預設使用 Claude 最新 Sonnet：UI、互動、程式碼品味、Claude 端的工具）、`codex-bulk`（預設使用 Codex 最新 `terra`：結果已完全確定的工作，例如針對既有契約的測試、型別與機械式遷移）、`main`（主代理：緊密耦合的工作，或規格仍在摸索中的工作）。
- **跨廠商審查**——審查者一定與作者屬於不同廠商，主代理自己的計畫與分流決定也交給另一個廠商審查。預設情況下 Claude 以最新 Opus、Codex 以最新 `sol` 審查，兩者的 effort 都是 `xhigh`——在兩個 CLI 中都是僅次於 `max` 的等級。每一項都可設定（[設定](#設定)），例如將 Codex 審查者設為 `astra`，模型與推理強度就會按設定執行。對於認證、付款、資料遷移等高風險階段，`run` 在追加頂級模型（Codex 最新 `astra` 或 `max` 的 Claude 最新 Opus）審查前會詢問你；如果審查者設定已經是該值，就不會提議，也絕不自行超出你的設定升級。審查者以唯讀方式執行，回傳由兩個 CLI 以 schema 強制約束的 JSON。
- **一輪反駁**——被駁回的 blocking 或 major 意見會連同理由退回給審查者一次。審查者要麼認同，要麼以新證據反駁；仍未解決時，會連同雙方論點以 DISPUTED 交給你決定。
- **證據說了算**——出現分歧時，握有測試、重現或追蹤的一方勝出。沒有證據時由你決定。
- **脈絡橋接**——稽核會找出兩個廠商讀取不同指示檔的位置、只約束一個廠商的 hook，以及工作者的 worktree 中會缺少的未提交脈絡。`run` 發出的 Codex 呼叫透過 Codex 的後備設定讀取 `CLAUDE.md`，不需修改儲存庫；互動式 Codex 工作階段（Orca 工作者，或作為主代理的 Codex）需要在你的 Codex 設定中加入同樣的設定。任何需要修改你的設定或儲存庫的調整都會在計畫核准時提出。
- **狀態寫入磁碟**——`.claude-x-codex/`（已排除在 git 之外）保存計畫、決定與審查，因此一次執行在脈絡壓縮後仍可恢復。

有專用規劃技能時，`run` 會將規劃交給該技能。

## 設定

六項設定用於選擇模型與推理強度。每項都像模式一樣持久保存，按以下順序使用第一個符合的值：

1. 僅用於單一 shell 的 `CXC_*` 變數
2. 本專案——由 `/peer-coding:mode <setting> <value>` 寫入的 `.claude-x-codex/settings`（已排除在 git 之外）
3. **Claude Code 的 `/config`**——六項均可在此選擇（輸入 `peer-coding` 尋找）；選擇值是所有專案的預設值
4. 全域檔案——由 `/peer-coding:mode <setting> <value> --global` 寫入的 `~/.config/claude-x-codex/settings`（Codex 沒有外掛設定選單，使用此方式）
5. 預設值

| 設定 | 變數 | 預設值 | 選擇對象 |
|---|---|---|---|
| `codex-worker` | `CXC_WORKER_MODEL` | `terra` | `codex-bulk` 通道的模型 |
| `codex-reviewer` | `CXC_REVIEW_MODEL` | `sol` | Codex 審查者的模型 |
| `claude-worker` | `CXC_CLAUDE_WORKER` | `sonnet` | `claude-fast` 通道的模型 |
| `claude-reviewer` | `CXC_CLAUDE_REVIEWER` | `opus` | Claude 審查者的模型 |
| `worker-effort` | `CXC_WORKER_EFFORT` | `high` | 兩個廠商的工作者 |
| `review-effort` | `CXC_REVIEW_EFFORT` | `xhigh` | 兩個廠商的審查者 |

```text
/peer-coding:mode codex-reviewer astra          # 本專案
/peer-coding:mode worker-effort xhigh --global  # 所有專案
/peer-coding:mode codex-reviewer unset          # 回到下一層級
/peer-coding:mode status                        # 模式和全部六項及各自來源
```

Codex 系列：`terra`, `luna`, `sol`, `astra`；Claude 系列：`sonnet`, `opus`, `haiku`, `fable`；effort：`low`, `medium`, `high`, `xhigh`, `max`。`/config` 只提供這些選項；命令也接受清單外的系列並給出提示。當更高層級覆蓋剛設定的值時，命令會指出該層級。僅為一個工作階段傳入的設定（`--settings`、受管理設定）不會被讀取。1.2.0 之前 Codex 工作者的預設值是 `luna`；使用 `/peer-coding:mode codex-worker luna --global` 可保留它。

以下仍只能透過環境變數設定：

| 變數 | 預設值 |
|---|---|
| `CXC_FINAL_MODEL` | `astra` |
| `CXC_MAX_CYCLES` | `3` |
| `CXC_PARALLEL` | `3` |

模型設定代表一個系列，並一律執行已安裝 CLI 提供的該系列最新版本。像 `gpt-6-sol` 這類版本值也會提升至該系列最新版本；若無法判定最新版本，通道會說明原因並停止。

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
