<p align="center">
  <strong>ux-ui-builder</strong>
</p>

<p align="center">
  <strong>像設計工作室交付作品那樣打造 Web 與行動 UI——以真實渲染實測、由藝術總監評論、在提交時把關。</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-1.1.0-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a>
</p>

<p align="center">
  <a href="#安裝">安裝</a> &bull;
  <a href="#它能做什麼">它能做什麼</a> &bull;
  <a href="#迴圈">迴圈</a> &bull;
  <a href="#行動裝置量測後端">行動裝置後端</a> &bull;
  <a href="#提交閘門">提交閘門</a> &bull;
  <a href="#faq">FAQ</a>
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

代理憑想像實作 UI 時，成果往往很差——看不見的 overflow、消失的 focus ring、沒有處理的空狀態、洩漏到標籤上的原始 UUID。這些問題在你看到真實渲染之前，全都不會浮現。

**ux-ui-builder 把想像從迴圈中移除。** 每一次 UI 變更都會在實際渲染上實測——Web 透過 chrome-devtools 量測瀏覽器頁面，行動裝置則使用真實的裝置或模擬器——再由藝術總監代理依據*實測*快照進行評論，反覆迭代直到既正確又優雅，最後以硬性閘門把關：藝術總監尚未針對暫存中的這份 diff 本身給出 APPROVED 的 UI，你就無法提交。

## 功能特色

- **只看實測，絕不想像**——技能會操控隨附的 **chrome-devtools MCP** 擷取真實渲染：在 mobile / tablet / desktop 各尺寸下的 default / hover / focus / loading / empty / error / long-content 狀態，外加 DOM/a11y 快照、console + 網路訊號，以及 Lighthouse 稽核。
- **也支援行動裝置** *（1.1 新增）*——第二個技能 `ux-ui-builder-mobile` 會偵測 App 的技術堆疊（React Native / Expo / Flutter / 原生 iOS / 原生 Android / 行動網頁），選擇能從已啟動的裝置或模擬器回傳**真實像素**的量測後端，並擷取裝置 × 方向 × 狀態矩陣。若沒有任何 MCP 能為該技術堆疊擷取螢幕截圖，就由隨附的 **CLI 快照 harness**（`simctl` / `adb`）代勞。
- **藝術總監硬性閘門**——`ux-ui-art-director` 代理（Opus）只評論實測產出物；行動裝置則由 `ux-ui-mobile-art-director` 依平台慣例（Apple HIG / Material）判定。只要有任何 critical/major 缺陷 → `CHANGES_REQUIRED`。它們可以自行重新量測狀態（行動版總監僅限可用 MCP 的技術堆疊；在只能用 CLI harness 的技術堆疊上，則改為要求提供擷取結果），但不能修改程式碼（審查者／實作者分離）。
- **與 diff 綁定的核准**——核准會綁定到暫存 UI diff 的 sha256。只要再次修改 UI，雜湊值就會改變，閘門便會再次阻擋。「核准一次後繼續修改」在結構上不可能發生；不會有過期或偽造的核准。
- **自主迭代**——build → measure → critique → fix → re-measure，最多 3 輪，不需要使用者額外下指示。第一次提交就是優雅的前端。（行動版迴圈只會在一開始暫停一次，以確認量測後端。）
- **零設定**——自帶瀏覽器與行動裝置 MCP，也自帶正確性 + 優雅度的標準，因此即使專案什麼都沒設定也能運作。若宿主專案*確實*定義了設計規則，則以那些規則為準。
- **保守的 blast radius**——閘門只會針對真正的 UI 檔案類型觸發：Web（`.tsx .jsx .vue .svelte .astro .css .scss .sass .less .html`）與行動裝置（`.swift .kt .dart .storyboard .xib`、Android `res/layout*/**/*.xml`）。單純的 `.ts`/`.js`/`.java` 以及非版面配置的 `.xml` 都被排除在外，因此純後端的提交絕不會被阻擋。

## 安裝

### 透過 Claude Code 外掛市集

1. 在 Claude Code 中執行 `/plugin`。
2. Marketplaces → Add Marketplace。
3. 輸入 URL：`https://github.com/zeriong/because-i-needed.git`（或此儲存庫的本機路徑）。
4. 安裝 `ux-ui-builder`。

### 或透過 CLI

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git   # 或本機路徑
claude plugin install ux-ui-builder@because-i-needed
```

### 或直接寫入 `~/.claude/settings.json`

```json
{
  "extraKnownMarketplaces": {
    "because-i-needed": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": { "ux-ui-builder@because-i-needed": true }
}
```

安裝後會自動註冊所有內容：四個 MCP 伺服器（`chrome-devtools`、`mobile-mcp`、`ios-simulator`、`flutter`）、提交閘門 hook、`ux-ui-art-director` 與 `ux-ui-mobile-art-director` 代理，以及 `ux-ui-builder` 與 `ux-ui-builder-mobile` 技能。

## 需求

- **Web**：**Node.js**（隨附的 `chrome-devtools-mcp` 透過 `npx` 執行）、本機的 **Chrome**，以及你要打造 UI 的那個專案的可執行**開發伺服器**。
- **行動裝置**：對應你技術堆疊的平台 SDK——Xcode + 模擬器（iOS，僅限 macOS）、Android SDK + 模擬器，或 Flutter SDK——並讓 App 在已啟動的裝置／模擬器上執行。行動裝置 MCP（`@mobilenext/mobile-mcp`、`ios-simulator-mcp`、`dart mcp-server`）只會在已安裝對應工具的環境中啟動；`mobile-snapshot.sh` harness 只需要 `simctl`/`adb`。
- **git** 工作樹，以及 `shasum`/`sha256sum`（macOS/Linux 預設即內建）。

## 快速開始

```
cd your-project
# 在 Claude Code 中直接打造 UI 即可。實作或修改畫面時：
/ux-ui-builder:ux-ui-builder          # Web
/ux-ui-builder:ux-ui-builder-mobile   # 行動裝置（RN / Flutter / iOS / Android / 行動網頁）
```

當你要求建立、修正、重新設計元件、頁面、畫面、表單、sheet、清單或版面配置，或調整它們的樣式時，這兩個技能也都會自動觸發。

Web 技能會：

1. 自我檢查瀏覽器 MCP 與你的開發伺服器（必要時會啟動伺服器）。
2. 為這項功能規劃專屬的設計意圖（而不是套用範本的預設值）。
3. 打造 UI。
4. 依狀態 × 斷點矩陣量測真實渲染。
5. 把量測結果交給藝術總監評論。
6. 套用修正並重新量測，直到取得 `APPROVED`（上限 = 3）。
7. 記錄能解除提交封鎖的核准。

行動版技能執行相同的迴圈，但步驟 1 會先偵測你的技術堆疊、執行 harness 的 `doctor`，並請你確認量測後端——這是唯一需要互動的暫停——而步驟 4 則會在已啟動的目標上量測裝置 × 方向 × 狀態矩陣。

如果你在沒有相符核准的情況下嘗試提交 UI，閘門會擋下它，並提示你執行迴圈。

## 它能做什麼

```
your-project/
└── .ux-ui/
    ├── measure/<feature>/        # 螢幕截圖、snapshots.md、signals.md、context.md
    └── approvals/<diff-hash>.json # 提交閘門會檢查的 APPROVED 產出物
```

外掛本身包含：

```
plugins/ux-ui-builder/
├── .claude-plugin/plugin.json          # manifest + 隨附的 MCP（chrome-devtools、mobile-mcp、ios-simulator、flutter）
├── hooks/hooks.json                    # PreToolUse → 提交閘門
├── scripts/
│   ├── ui-commit-gate.sh               # 閘門：hash | approve <feature> [dir] | hook-block（Web + 行動裝置類型）
│   └── mobile-snapshot.sh              # CLI 快照 harness：doctor | capture <ios|android> <dir> <label>
├── agents/
│   ├── ux-ui-art-director.md           # Web 藝術總監（量測 + 評論，Opus）
│   └── ux-ui-mobile-art-director.md    # 行動版藝術總監（HIG / Material 慣例，Opus）
└── skills/
    ├── ux-ui-builder/                  # Web：measure → critique → iterate → gate
    │   ├── SKILL.md
    │   └── references/
    │       ├── design-principles.md    # 正確性 + 優雅度標準（自成一體）
    │       ├── measurement-protocol.md # 精確的 chrome-devtools 擷取協定
    │       └── review-rubric.md        # verdict 格式 + APPROVED 產出物契約
    └── ux-ui-builder-mobile/           # 行動裝置：detect → measure → critique → iterate → gate
        ├── SKILL.md
        └── references/
            ├── backend-detection.md          # 偵測技術堆疊 + 選擇真實像素後端
            ├── mobile-design-principles.md   # HIG / Material、安全區域、點擊目標、手勢、鍵盤、深色模式
            ├── mobile-measurement-protocol.md # 各後端的擷取方式（裝置 × 方向 × 狀態）
            └── mobile-review-rubric.md       # verdict 格式 + APPROVED 產出物契約
```

## 迴圈

| 步驟 | 職責 |
|------|------|
| 0 | **Bootstrap**——確認瀏覽器 MCP + 開發伺服器；選定 feature slug。*行動裝置：* 偵測技術堆疊、執行 `mobile-snapshot.sh doctor`、與你確認後端，並確保 App 在已啟動的目標上執行 |
| 1 | **Plan**——為*這項*功能擬定精簡的設計意圖；避免 AI 預設的外觀（行動裝置：在平台慣例的範圍內） |
| 2 | **Build**——實作，並重用既有的元件／token |
| 3 | **Measure**——擷取真實的狀態 × 斷點矩陣 + 稽核（行動裝置：裝置 × 方向 × 狀態）——必要步驟 |
| 4 | **Critique**——針對實測產出物啟動 `ux-ui-art-director`（Web）或 `ux-ui-mobile-art-director`（行動裝置）（硬性閘門） |
| 5 | **Iterate**——套用修正，回到步驟 3，重新審查（上限 = 3） |
| 6 | **Record approval**——僅在 APPROVED 時執行；為這份 diff 本身解除提交封鎖 |

量測永遠不是可選的，也絕不造假。**沒有螢幕截圖 → 沒有審查 → 沒有提交。**

## 行動裝置量測後端

每一種行動技術堆疊都有取得真實像素的途徑。技能會優先選擇能同時回傳螢幕截圖與 a11y/view 樹的 MCP，其次是任何能回傳螢幕截圖的 MCP，最後才是 CLI harness：

| 偵測到的技術堆疊 | 優先後端 | 螢幕截圖 | A11y / 結構 |
|------------------|----------|----------|-------------|
| 行動網頁 | `chrome-devtools` MCP（隨附） | `take_screenshot` + `emulate`/`resize_page` | `take_snapshot` |
| Flutter | `flutter` MCP（`dart mcp-server`） | 螢幕截圖工具 | widget 樹 + hot reload |
| 原生 iOS | `ios-simulator` MCP（idb，僅限 macOS） | `screenshot` / `ui_view` | `ui_describe_all` |
| React Native | **CLI 快照 harness**（預設；`mobile-mcp` 作為替代選項） | `mobile-snapshot.sh capture …` | `adb uiautomator dump`（Android）；僅像素（iOS） |
| 原生 Android / 跨平台 | `mobile-mcp` MCP | `mobile_take_screenshot` | `mobile_list_elements_on_screen` |
| 任何技術堆疊，但沒有可用的 MCP | **CLI 快照 harness** | `mobile-snapshot.sh capture …` | `adb uiautomator dump`（Android）；僅像素（iOS） |

完整規則與平手時的判定方式：[`backend-detection.md`](skills/ux-ui-builder-mobile/references/backend-detection.md)。

## 提交閘門

`PreToolUse` hook 會在每次 `Bash` 呼叫前執行 `ui-commit-gate.sh`。它會：

1. 放行任何不是 `git commit` 的操作（快速路徑）。
2. 放行沒有暫存 UI 檔案的提交。
3. 對於 UI 提交，計算暫存 UI diff 的 sha256，並尋找含有 `verdict: APPROVED` 的 `.ux-ui/approvals/<hash>.json`。
4. 若找到 → 放行。否則 → **exit 2**，阻擋提交並顯示訊息，提示你執行迴圈。

由於核准綁定在 diff 雜湊值上，之後任何 UI 修改都會使其失效——閘門無法偽造，也永遠不會過期。Web 與行動 UI 共用同一個閘門。

可用 `UX_UI_GLOBS` 環境變數覆寫哪些檔案算作 UI。產出物存放在 `.ux-ui/` 之下；若不想提交它們，請將其加入 `.gitignore`。

## FAQ

**為什麼不直接讓模型目測它自己拍的螢幕截圖就好？**
因為「拍過一次螢幕截圖」算不上紀律。這個外掛*強制要求*完整的狀態 × 斷點矩陣、a11y 快照，以及 console／網路／Lighthouse 訊號，並在獨立的藝術總監代理核可這些產出物之前阻擋提交。靠的是強制執行，而不是感覺。

**這是把瀏覽器自動化重新做成自訂 MCP 嗎？**
不是。瀏覽器自動化已經有 `chrome-devtools-mcp`，本外掛直接將其隨附（行動裝置 MCP 也一樣）。附加價值在於*編排與強制執行*——measure → critique → iterate → gate——這些都放在技能 + 代理 + hook 之中，因為 MCP 伺服器無法產生 Claude Code 子代理，也無法驅動審查迴圈。

**為什麼要用藝術總監，而不是直接交給主模型？**
為了分離。負責建置的代理對自己的作品有所投入；而一個只根據實測產出物評判、無法修改程式碼的全新代理，能抓到建置者自我合理化而放過的問題。這和設計工作室設有審查環節的道理相同。

**它會擋下我的後端提交嗎？**
不會。閘門只會針對 UI 檔案類型觸發，並刻意排除單純的 `.ts`/`.js`/`.java` 與非版面配置的 `.xml`。純後端的提交會原封不動地通過。

**可以核准一次後繼續修改嗎？**
不行——這正是重點。核准綁定在暫存 UI diff 的雜湊值上。只要改動一行 UI，雜湊值就不再相符，閘門會再次阻擋，直到你重新執行迴圈為止。

**我的行動技術堆疊沒有能擷取螢幕截圖的 MCP，怎麼辦？**
CLI 快照 harness（`mobile-snapshot.sh`）會透過 `simctl`/`adb` 直接從模擬器（simulator/emulator）擷取真實的 PNG，再由藝術總監審查。它唯一絕不會做的事，就是審查想像出來的狀態。

**如果它連不上開發伺服器、Chrome 或已啟動的裝置呢？**
它會停下來告訴你，而不是退而求其次去審查想像出來的狀態。環境故障就是硬性停止，這是刻意的設計。

## 授權

MIT。詳見 [LICENSE](../../LICENSE)。

## 致謝

先量測、再評論的紀律，借鑑了 `frontend-design` 技能（美學方向）與 `chrome-devtools-mcp` 外掛（瀏覽器量測）。硬性閘門與綁定 diff 的核准模式，則沿用作者在 harness-engineering 工作中的 review-gate 設計。
