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

本儲存庫是一個 Claude Code **外掛市集**，收錄三個彼此獨立的外掛。只要安裝你需要的即可。

## 外掛

### [plan-smith](plugins/plan-smith) · `v1.4.2`

**用兩階段管線鍛造計畫。** 主代理會把整段對話提煉成上下文封包（目標、硬性限制、已否決的替代方案），並先向你確認；接著由乾淨上下文的 `plan-writer` 代理，運用推理框架庫與經過驗證的寫作風格撰寫計畫，再把計畫原封不動地轉交給你——沒有摘要造成的資訊流失，也沒有上下文汙染。

- **適用時機：** 需要為遷移、上線、build-out 擬定計畫時——凡是冗長又充滿雜訊的工作階段容易讓計畫變得混亂的任務都適用。
- **進入點：** `/plan-smith:plan-smith <任務>`，或直接說 *「幫我寫一份……的計畫」*

[閱讀 plan-smith 繁體中文 README →](plugins/plan-smith/README.zh-TW.md)

### [harness-builder](plugins/harness-builder) · `v1.0.0`

**以事實分析而非範本，打造專屬於專案的 Claude Code harness。** 它會讀取儲存庫實際的分層與關注點分離，推導出每條都引用你程式碼中 `file:line` 的規則，並產生 `project-rules`、具確定性的 `review-gate.sh`、`UserPromptSubmit` hook，以及 `harness-engineering` 技能。

- **適用時機：** 在尚未設定 `.claude/` 的專案上開始使用 Claude Code，或專案結構變動大到舊設定已不再適用時。
- **進入點：** `/harness-builder:harness-builder`，或 *「build harness」*

[閱讀 harness-builder 繁體中文 README →](plugins/harness-builder/README.zh-TW.md)

### [ux-ui-builder](plugins/ux-ui-builder) · `v1.1.0`

**以真實渲染的實測結果打造 Web 與行動 UI。** 它會擷取真實的螢幕截圖（Web 用 chrome-devtools；React Native / Flutter / iOS / Android 則用行動裝置 MCP 或 CLI 快照 harness），讓藝術總監代理評論這些實測快照，反覆迭代直到 UI 既正確又優雅，並在暫存的 diff 本身取得 APPROVED 之前，阻擋 UI 的 `git commit`。

- **適用時機：** 建立或修改任何元件、頁面或畫面，並希望在實際渲染上驗證、而不是憑想像時。
- **進入點：** `/ux-ui-builder:ux-ui-builder`（Web）· `/ux-ui-builder:ux-ui-builder-mobile`（行動裝置），或直接請它打造 UI
- **注意：** 安裝後會一併註冊 `PreToolUse` 提交閘門 hook（在每次 `Bash` 呼叫前執行，只阻擋 UI 提交）以及四個 MCP 伺服器。

[閱讀 ux-ui-builder 繁體中文 README →](plugins/ux-ui-builder/README.zh-TW.md)

## 安裝

先新增一次市集，再安裝你想要的外掛：

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install plan-smith@because-i-needed
claude plugin install harness-builder@because-i-needed
claude plugin install ux-ui-builder@because-i-needed
```

或在 Claude Code 中：`/plugin` → Marketplaces → Add Marketplace → `https://github.com/zeriong/because-i-needed.git`，然後從清單中安裝。

或直接寫入 `~/.claude/settings.json`：

```json
{
  "extraKnownMarketplaces": {
    "because-i-needed": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": {
    "plan-smith@because-i-needed": true,
    "harness-builder@because-i-needed": true,
    "ux-ui-builder@because-i-needed": true
  }
}
```

## 儲存庫結構

```
because-i-needed/
├── .claude-plugin/marketplace.json   # 列出三個外掛
└── plugins/
    ├── plan-smith/                   # 技能 + plan-writer 代理（+ CHANGELOG.md）
    ├── harness-builder/              # 技能
    └── ux-ui-builder/                # 2 個技能 + 2 個代理 + 提交閘門 hook + 4 個 MCP
```

每個外掛資料夾都是自給自足的：它的 README、manifest，以及所有隨附的內容，都放在 `plugins/<name>/` 之下。

## 語言政策

- 本儲存庫中的每一份 README——包括本文件與各外掛的 README——都提供**五種語言**：`README.md`（英文，原始版本）、`README.ko.md`（한국어）、`README.ja.md`（日本語）、`README.zh-CN.md`（简体中文）、`README.zh-TW.md`（繁體中文）。
- 修改 README 時，要在同一個提交中同步更新全部五種語言。新外掛從第一個提交起就要具備五種語言。
- Claude 直接讀取的檔案——`SKILL.md`、`references/*.md`、`agents/*.md`——維持英文。

## 授權

MIT。詳見 [LICENSE](LICENSE)。
