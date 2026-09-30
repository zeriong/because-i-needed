<p align="center">
  <strong>because-i-needed</strong>
</p>

<p align="center">
  <strong>因為需要才自己做的 Claude Code 外掛——規劃、專案 harness，以及實測驅動的 UI。</strong>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin%20Marketplace-orange" alt="Claude Code Plugin Marketplace"></a>
</p>

<p align="center">
  <a href="README.md">English</a> &bull;
  <a href="README.ko.md">한국어</a> &bull;
  <a href="README.ja.md">日本語</a> &bull;
  <a href="README.zh-CN.md">简体中文</a> &bull;
  <a href="README.zh-TW.md">繁體中文</a>
</p>

---

本儲存庫是一個 Claude Code **外掛市集**，收錄四個彼此獨立的外掛。只要安裝你需要的即可。

## 外掛

### [plan-smith](plugins/plan-smith) · `v1.7.0`

**用兩階段管線鍛造計畫。** 主代理會把整段對話提煉成上下文封包（目標、硬性限制、已否決的替代方案），並先向你確認；接著由乾淨上下文的 `plan-writer` 代理，運用推理框架庫與經過驗證的寫作風格撰寫計畫，再把計畫原封不動地轉交給你——沒有摘要造成的資訊流失，也沒有上下文汙染。

- **適用時機：** 需要為遷移、上線、build-out 擬定計畫時——凡是冗長又充滿雜訊的工作階段容易讓計畫變得混亂的任務都適用。
- **進入點：** `/plan-smith:forge <任務>`，或直接說 *「幫我寫一份……的計畫」*

[閱讀 plan-smith 繁體中文 README →](plugins/plan-smith/README.zh-TW.md)

### [harness](plugins/harness) · `v1.2.0`

**以事實分析而非範本，打造專屬於專案的 Claude Code 或 Codex harness。** 它會讀取儲存庫實際的分層與關注點分離，推導出每條都引用你程式碼中 `file:line` 的規則，並產生 `project-rules`、具確定性的 `review-gate.sh`、`UserPromptSubmit` hook，以及 `harness-engineering` 技能。

- **適用時機：** 在尚未設定 harness 的專案上開始使用 Claude Code 或 Codex，或專案結構變動大到舊設定已不再適用時。
- **進入點：** `/harness:build`，或 *「build harness」*

[閱讀 harness 繁體中文 README →](plugins/harness/README.zh-TW.md)

### [ux-ui](plugins/ux-ui) · `v1.2.0`

**以真實渲染的實測結果打造 Web 與行動 UI。** 它會擷取真實的螢幕截圖（Web 用 chrome-devtools；React Native / Flutter / iOS / Android 則用行動裝置 MCP 或 CLI 快照 harness），讓藝術總監代理評論這些實測快照，反覆迭代直到 UI 既正確又優雅，並在暫存的 diff 本身取得 APPROVED 之前，阻擋 UI 的 `git commit`。

- **適用時機：** 建立或修改任何元件、頁面或畫面，並希望在實際渲染上驗證、而不是憑想像時。
- **進入點：** `/ux-ui:build`（Web）· `/ux-ui:build-mobile`（行動裝置），或直接請它打造 UI
- **注意：** 安裝後會一併註冊 `PreToolUse` 提交閘門 hook（在每次 `Bash` 呼叫前執行，只阻擋 UI 提交）以及四個 MCP 伺服器。

[閱讀 ux-ui 繁體中文 README →](plugins/ux-ui/README.zh-TW.md)

### [claude-x-codex](plugins/claude-x-codex) · `v0.1.0`

**Claude × Codex 同儕編排。** 主代理負責規劃並做出每個關卡的決定，把工作分派給快速的 Claude 工作者或批次處理的 Codex 工作者，兩個廠商互相審查對方的工作——包括主代理自己的計畫。反駁只有一輪，裁定依據的是證據而不是角色。稽核功能確保兩個廠商從相同的專案指示出發。非官方社群外掛。

- **適用時機：** 同時使用 Claude Code 與 Codex，並希望功能的每個階段都經過另一個廠商審查時。
- **進入點：** `/claude-x-codex:run`，或以 `/claude-x-codex:mode on` 開啟後，實作類請求都會走這個流程
- **注意：** 安裝後會註冊一個 `UserPromptSubmit` hook（在每則提示時執行，模式關閉時不輸出任何內容）。

[閱讀 claude-x-codex 繁體中文 README →](plugins/claude-x-codex/README.zh-TW.md)

## 安裝

安裝腳本會列出外掛，並只安裝你選取的：

```bash
curl -fsSL https://raw.githubusercontent.com/zeriong/because-i-needed/main/install.sh | bash
```

↑/↓（或 j/k）移動，空白鍵切換選取，`a` 全選，Enter 安裝，`q` 離開——一開始全部都是選取狀態。選項：`--all`、`--only a,b`、`--list`、`--dry-run`、`--scope user|project|local`；透過管線執行時，把它們放在 `bash -s --` 之後（例如 `… | bash -s -- --only harness`）。它執行的就是下面這些 `claude plugin` 命令。

或者自行新增市集，再安裝你想要的外掛：

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install plan-smith@bin
claude plugin install harness@bin
claude plugin install ux-ui@bin
claude plugin install claude-x-codex@bin
```

或在 Claude Code 中：`/plugin` → Marketplaces → Add Marketplace → `https://github.com/zeriong/because-i-needed.git`，然後從清單中安裝。

或直接寫入 `~/.claude/settings.json`：

```json
{
  "extraKnownMarketplaces": {
    "bin": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": {
    "plan-smith@bin": true,
    "harness@bin": true,
    "ux-ui@bin": true,
    "claude-x-codex@bin": true
  }
}
```

## 命名規則

每個命令都讀作 **對象 : 動作** —— `/<外掛>:<技能>`。

- **外掛 = 對象** —— 它處理什麼（`harness`、`ux-ui`）。`plan-smith` 保留既有的名稱。
- **技能 = 動詞** —— 從同一套共用詞彙中選取，同一個動詞在所有外掛中含義相同。
- 外掛維持獨立：你只安裝需要的外掛，一個外掛的 hook 或 MCP 伺服器不會跟著另一個外掛一起裝上。

| 動詞 | 含義 |
|---|---|
| `build` | 在專案中產生產出物（harness、UI 等） |
| `forge` | 把對話脈絡提煉成文件（如計畫） |
| `run` | 執行任務 |
| `mode` | 開啟或關閉某種行為 |
| `audit` | 唯讀檢查 |
| `review` | 審查結果 |

`review` 保留給後續的外掛。

## 儲存庫結構

```
because-i-needed/
├── .claude-plugin/marketplace.json   # 列出四個外掛
├── install.sh                        # 互動式安裝腳本（執行 claude plugin install）
└── plugins/
    ├── plan-smith/                   # 技能 + plan-writer 代理 + 拆分檢查器（+ CHANGELOG.md）
    ├── harness/                      # 技能
    ├── ux-ui/                        # 2 個技能 + 2 個代理 + 提交閘門 hook + 4 個 MCP
    └── claude-x-codex/               # 3 個技能 + 提示 hook + 3 個腳本
```

每個外掛資料夾都是自給自足的：它的 README、manifest，以及所有隨附的內容，都放在 `plugins/<name>/` 之下。

## 語言政策

- 本儲存庫中的每一份 README——包括本文件與各外掛的 README——都提供**五種語言**：`README.md`（英文，原始版本）、`README.ko.md`（한국어）、`README.ja.md`（日本語）、`README.zh-CN.md`（简体中文）、`README.zh-TW.md`（繁體中文）。
- 修改 README 時，要在同一個提交中同步更新全部五種語言。新外掛從第一個提交起就要具備五種語言。
- 只有 README 需要翻譯。其他所有檔案——`CLAUDE.md`、`SKILL.md`、`references/*.md`、`agents/*.md`、`CHANGELOG.md`、hook 訊息——都以英文撰寫。必須與使用者輸入相符的觸發詞保留原語言。

## 授權

MIT。詳見 [LICENSE](LICENSE)。
