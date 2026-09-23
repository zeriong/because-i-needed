<p align="center">
  <strong>harness-builder</strong>
</p>

<p align="center">
  <strong>打造專屬於你專案的 Claude Code harness——依據事實分析，而不是套用範本。</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-1.0.0-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a>
</p>

<p align="center">
  <a href="#安裝">安裝</a> &bull;
  <a href="#它能做什麼">它能做什麼</a> &bull;
  <a href="#8-phase-工作流程">工作流程</a> &bull;
  <a href="#fact-check-迴圈">Fact-check 迴圈</a> &bull;
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

大多數「Claude Code harness」外掛，只是套印出一個固定的 `.claude/` 骨架就收工。它們強制執行的規則，是*外掛作者*想到的規則——而不是*你的專案真正需要*的規則。

**harness-builder 把這個順序反過來。** 它先閱讀你的專案，從實際存在的內容推導出規則，之後才建立強制執行*這些*規則的 harness。成果是一個為你的儲存庫量身打造的 `.claude/` 目錄，其中每條規則都能追溯到你自己程式碼中的 `file:line` 引用。

## 功能特色

- **以事實為本的規則推導**——每條規則都來自對真實程式碼做出的 verdict，而不是範本。沒有 `file:line` 引用的主張一律捨棄。
- **閘門優先的強制執行**——能以確定性方式檢查的規則，會成為 `review-gate.sh` 中以結束碼判定的閘門。只能定性判斷的規則則保留為建議性質（advisory），並在每次提示時呈現給 Claude。
- **考量副作用的回歸**——建置期間只要套用任何修補，就會強制回到 Phase 1。harness 假設即使只改一行，也可能讓先前所有的 verdict 失效。
- **雙審查者交叉檢查**——在宣告完成之前，建置流程會平行啟動一個 Opus 與一個 Sonnet 代理（全新產生、不共享上下文），並依六個品質面向彙整它們的 JSON 報告。
- **Worse/better case 索引**——每條規則都附帶一份 `docs/conventions/<rule>.md`，內含你儲存庫中實際有問題的程式碼與實際的改良寫法，以及方便 grep 的關鍵字。
- **預設採用 YAGNI**——在你的儲存庫中零違規、使用者也從未提及的規則，一律不引入。只需要 5 條規則的專案得到一個 5 條規則的 harness，這是成功，而不是失敗。

## 適用時機

- 在尚未設定 `.claude/` 的專案上開始使用 Claude Code。
- 專案結構大幅變動後，重新建置既有的 `.claude/`。
- 你想要的是與儲存庫中實際程式碼綁定的規則，而不是抽象的慣例。

**可以跳過的情況：**

- 單一檔案的工具程式或一次性腳本——用 harness 太小題大作。
- 你已經建立並細心維護了一套值得信賴的 `.claude/` 的專案。
- 沒有清楚分層的儲存庫（fact-check 迴圈需要有結構可以著力）。

## 安裝

### 透過 Claude Code 外掛市集

1. 在 Claude Code 中執行 `/plugin`。
2. Marketplaces → Add Marketplace。
3. 輸入 URL：`https://github.com/zeriong/because-i-needed.git`。
4. 安裝 `harness-builder`。

### 或透過 CLI

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install harness-builder@because-i-needed
```

### 或直接寫入 `~/.claude/settings.json`

```json
{
  "extraKnownMarketplaces": {
    "because-i-needed": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": { "harness-builder@because-i-needed": true }
}
```

## 快速開始

```
cd your-project
# 在 Claude Code 中：
/harness-builder:harness-builder
```

也可以用自然語言提出——觸發關鍵字（韓文／英文）：`harness 만들어`、`build harness`、`harness 셋업`、`프로젝트 룰 추출`、`review gate 깔아줘`、`harness-builder`。

這個技能會：

1. 針對你的專案提出四個問題（套件管理器、monorepo 形態、lint/typecheck 指令，以及你堅持要採用的規則）。
2. 閱讀你的程式碼庫，並對每一層執行 fact-check 迴圈。
3. 推導規則、產生閘門腳本、接上 hook、撰寫技能，並為慣例文件建立索引。
4. 以刻意違規的範例驗證一切運作正常。
5. 啟動雙審查者小組做最後檢查。

完整執行通常需要好幾個回合——這個技能會坦白告訴你這一點。支援用 `/loop` 包起來執行，但並非必要。

## 它能做什麼

寫入專案根目錄的輸出：

```
.claude/
├── settings.json                    # UserPromptSubmit hook 接線
├── hooks/inject-context.sh          # 每次提示時注入 project-rules + harness-engineering
├── scripts/review-gate.sh           # 確定性閘門——exit 0 / 1 / 2
└── skills/
    ├── project-rules/SKILL.md       # 在 Phase 1–2 從你的程式碼推導出的規則
    └── harness-engineering/SKILL.md # 供日後任務使用的 11-phase 工作流程

docs/conventions/
├── <rule-1>.md                      # Worse-case + better-case（來自你儲存庫的真實程式碼）+ 關鍵字索引
├── <rule-2>.md
└── ...
```

建置完成後，你專案中的每個使用者提示都會自動載入 `project-rules` 與 harness 的各個 phase。前端程式碼？推導出的分層規則就會觸發。編輯一個 300 行的元件？推導出的檔案長度上限就會擋下它。這些規則是你的，不是外掛的。

外掛本身只包含一個技能：[`skills/harness-builder/SKILL.md`](skills/harness-builder/SKILL.md)——也就是下方的 8-phase 建置流程。

## 8-Phase 工作流程

| Phase | 職責 | 必須執行 fact-check 迴圈 |
|-------|------|--------------------------|
| 0 | **Intake**——套件管理器、monorepo 形態、既有腳本、使用者建議的規則 | — |
| 1 | **Layer / Concern Reconnaissance**——每項主張都必須引用 `file:line` | ✅ 強制 |
| 2 | **Convention Extraction**——將 Phase 1 的 verdict 轉為規則 | ✅ |
| 3 | **`docs/conventions/<rule>.md`**——以儲存庫真實程式碼建立索引的 worse / better case | ✅ |
| 4 | 產生 **Gate script**（`review-gate.sh`） | — |
| 5 | **Hook 接線**（`UserPromptSubmit`） | — |
| 6 | **Skill 本文**（`project-rules` + `harness-engineering`） | — |
| 7 | **Self-verification**——以範例 diff 實際測試閘門 | — |
| 8 | **Review gate**——Opus + Sonnet 單次審查，由主代理彙整修補 | — |

**在 Phase 8 套用任何修補，都會強制回歸到 Phase 1。** 這是絕對規則，不是經驗法則——預設副作用會讓先前的 verdict 失效。迭代上限為 3 次；若仍無法收斂，技能會輸出一份如實的失敗報告，並等待你做決定。

## Fact-check 迴圈

這是整個技能中最重要的一條規則。Phase 1 對你程式碼提出的每一項主張，都必須通過以下流程：

```
主張：        「src/components/admin/audit-logs/page.tsx 只負責呈現」
              ↓
自我懷疑：    「真的嗎？來驗證一下。」
              ↓
直接讀取：    用 Read 工具打開檔案——不靠記憶、不靠推論
              ↓
範圍掃描：    在同一目錄中 grep "useState|useEffect|fetch"
              ↓
副作用：      用 grep -r 找出匯入此模組的地方
              ↓
SRP 測試：    它是否恰好只有一個變更理由？
              ↓
Verdict：     「呈現與資料混雜——page.tsx:24-31 呼叫了 fetch()」
              並附上 file:line 引用
              ↓
進入下一個 phase
```

跳過任何一步的主張都會被**捨棄**，Phase 1 重新開始。正因如此，推導出的規則才值得信賴——它們不是來自模型的直覺，而是來自你儲存庫中可驗證的事實。

## 高品質的定義

技能考慮套用的每一項修補，都會依六個面向自我評分（各 0–5 分）：

| 面向 | 意義 |
|------|------|
| **SRP** | 每個模組只有一個變更理由 |
| **註解清晰度** | 精簡、只寫重點、≤ 2 行 |
| **KISS** | 能解決問題的最簡單形式 |
| **DRY** | 模組之間沒有重複的邏輯 |
| **YAGNI** | 不加入臆測性的功能或規則 |
| **易於理解** | 人類讀者不費力就能讀懂 |

平均分數低於 3.5 的修補會被拒絕；若拒絕率偏高，相應的 phase 就會回歸。

## 繞過 harness

建置完成後，每個使用者提示都會觸發注入 hook。若只想在某一回合繞過：

- 在提示前加上 `!`（例如 `!直接回答就好`）
- 或加入可辨識的繞過用語（韓文／英文）：`harness 빼고`、`without harness`、`skip harness`、`no harness`

繞過模式只會停用該回合的 phase 強制執行，project-rules 仍會保持可見。

## FAQ

**為什麼不直接給我一份 `.claude/` 範本？**
因為範本強制執行的是*別人的*規則。這個技能的重點，是強制執行*你專案的*規則——從它的實際程式碼推導而來。你程式碼庫中一個 200 LOC 的元件，和別人程式碼庫中一個 200 LOC 的元件，意義並不相同；上限應該來自你自己的程式碼。

**這和 linter／ESLint 設定有什麼不同？**
Linter 檢查的是語法與已知的反模式。這個技能檢查的是 linter 不太能建模的結構性問題（分層、SRP、檔案長度、命名），並把每條規則連結到你儲存庫中的 `file:line`，讓違規有脈絡可循。兩者是互補，而非取代。

**為什麼是兩位審查者，而不是五位？**
這個技能所源自的 setup-guide 使用由 2 個 Opus + 3 個 Sonnet 組成的 5 代理小組。對建置結束時的單次審查來說，那是過度設計——第 3 到第 5 個代理的邊際效益撐不起它帶來的延遲。一個 Opus 加一個 Sonnet，就能以五分之一的成本取得大部分的模型多樣性效益。

**如果 Phase 1 判定我的專案已經分層得很完美呢？**
那就不會引入分層規則。YAGNI 適用於此——零違規且使用者從未提及的規則，禁止加入。如果你唯一在意的是命名，你就會得到一個只有一條規則的 harness。

**建置完成後，我可以編輯產生的 `.claude/` 嗎？**
可以。輸出是你的。技能不會追蹤或重新同步產生的檔案。如果你重新執行 `/harness-builder:harness-builder`，就需要自行處理合併。

**非前端專案也能用嗎？**
Phase 1 的分層訊號是針對前端儲存庫（`*.tsx`、`use-*.ts`、`api/*`）調校的。若是 Go 服務或 Python 後端，技能就需要不同的分層辨識訊號——而這正是 Phase 0 那個自由填答問題的用途。技能的*工作流程*與專案無關；只有 Phase 1 的經驗法則經過調校。

## 需求

- `git`、`jq`、`bash 4+`
- 目標專案必須是 git 工作樹
- 支援外掛的 Claude Code

## 授權

MIT。詳見 [LICENSE](../../LICENSE)。

## 致謝

8-phase 工作流程源自作者撰寫的一份非公開 harness setup-guide 與 research-foundation。fact-check 迴圈模式受到 CRITIC（Gou et al. 2023）以及 Anthropic Multi-Agent Research System 工程部落格的影響。收斂上限（= 3）則取自 Reflexion（Shinn et al. 2023）。
