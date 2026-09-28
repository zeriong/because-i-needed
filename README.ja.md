<p align="center">
  <strong>because-i-needed</strong>
</p>

<p align="center">
  <strong>必要だから作った Claude Code プラグイン集 — プランニング、プロジェクトハーネス、実測ベースの UI。</strong>
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

このリポジトリは、独立した 3 つのプラグインを収めた Claude Code の**プラグインマーケットプレイス**です。必要なものだけをインストールしてください。

## プラグイン

### [plan-smith](plugins/plan-smith) · `v1.5.0`

**2 段構成のパイプラインでプランを鍛え上げます**。メインエージェントが会話全体をコンテキストパケット（目標、ハード制約、却下された代替案）に蒸留してあなたに確認し、続いてクリーンなコンテキストの `plan-writer` エージェントが推論フレームライブラリと検証済みの執筆スタイルでプランを書きます。完成したプランは原文のまま届けられます — 要約による欠落も、コンテキスト汚染もありません。

- **使いどころ:** マイグレーション、ローンチ、build-out など、長くノイズの多いセッションではプランがぼやけてしまいがちな作業の計画が必要なとき。
- **エントリーポイント:** `/plan-smith:forge <タスク>`、または単に *「… のプランを書いて」*

[plan-smith の日本語 README を読む →](plugins/plan-smith/README.ja.md)

### [harness](plugins/harness) · `v1.1.0`

**テンプレートではなく、事実に基づく分析からプロジェクト専用の Claude Code ハーネスを構築します**。リポジトリの実際のレイヤー構成と関心の分離を読み取り、すべてのルールがあなたのコードの `file:line` を引用する形で導出したうえで、`project-rules`、決定論的な `review-gate.sh`、`UserPromptSubmit` フック、`harness-engineering` スキルを生成します。

- **使いどころ:** `.claude/` のセットアップがないプロジェクトで Claude Code の作業を始めるとき、または構成が大きく変わり、既存のセットアップが合わなくなったとき。
- **エントリーポイント:** `/harness:build`、または *「build harness」*

[harness の日本語 README を読む →](plugins/harness/README.ja.md)

### [ux-ui](plugins/ux-ui) · `v1.2.0`

**実際のレンダリングを実測しながら Web とモバイルの UI を構築します**。実際のスクリーンショットを撮影し（Web は chrome-devtools、React Native / Flutter / iOS / Android はモバイル MCP または CLI スナップショットハーネス）、アートディレクターエージェントにその実測スナップショットを批評させ、UI が正確かつエレガントになるまで反復し、ステージされた diff そのものが APPROVED されるまで UI の `git commit` をブロックします。

- **使いどころ:** コンポーネント、ページ、画面を作成・変更するときに、想像ではなく実際のレンダリングで検証したいとき。
- **エントリーポイント:** `/ux-ui:build`（Web）· `/ux-ui:build-mobile`（モバイル）、または UI の作成を依頼するだけ
- **注意:** インストールすると、`PreToolUse` のコミットゲートフック（すべての `Bash` 呼び出しの前に実行され、UI のコミットだけをブロック）と 4 つの MCP サーバーが登録されます。

[ux-ui の日本語 README を読む →](plugins/ux-ui/README.ja.md)

## インストール

マーケットプレイスを一度追加してから、使いたいプラグインをインストールします。

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install plan-smith@bin
claude plugin install harness@bin
claude plugin install ux-ui@bin
```

または Claude Code 内で `/plugin` → Marketplaces → Add Marketplace → `https://github.com/zeriong/because-i-needed.git` と進み、一覧からインストールします。

または `~/.claude/settings.json` に直接記述します。

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
    "ux-ui@bin": true
  }
}
```

## 命名規則

すべてのコマンドは **対象 : 動作** と読めます — `/<プラグイン>:<スキル>`。

- **プラグイン = 対象** — 何を扱うか（`harness`、`ux-ui`）。`plan-smith` はすでに知られた名前を維持します。
- **スキル = 動詞** — 1 つの共通語彙から選び、同じ動詞はどのプラグインでも同じ意味です。
- プラグインは分けたままにします。必要なものだけをインストールでき、あるプラグインのフックや MCP サーバーが別のプラグインに付いてくることはありません。

| 動詞 | 意味 |
|---|---|
| `build` | プロジェクトに成果物（ハーネス、UI など）を作る |
| `forge` | 会話の文脈を蒸留してドキュメント（プランなど）を作る |
| `run` | タスクを実行する |
| `mode` | 動作をオン / オフする |
| `audit` | 読み取り専用で点検する |
| `review` | 結果物をレビューする |

`run`、`mode`、`audit`、`review` は今後のプラグインのために予約されています。

## リポジトリ構成

```
because-i-needed/
├── .claude-plugin/marketplace.json   # 3 つのプラグインを登録
└── plugins/
    ├── plan-smith/                   # スキル + plan-writer エージェント (+ CHANGELOG.md)
    ├── harness/                      # スキル
    └── ux-ui/                        # スキル 2 + エージェント 2 + コミットゲートフック + MCP 4
```

各プラグインフォルダは自己完結しています。README、マニフェスト、配布されるすべてのファイルが `plugins/<名前>/` の下にあります。

## 言語ポリシー

- このリポジトリのすべての README（本書と各プラグインの README）は **5 つの言語**で提供されます: `README.md`（英語、原本）、`README.ko.md`（한국어）、`README.ja.md`（日本語）、`README.zh-CN.md`（简体中文）、`README.zh-TW.md`（繁體中文）。
- README を変更するときは、同じコミットで 5 つすべてを更新します。新しいプラグインは、最初のコミットから 5 言語すべてを揃えます。
- 翻訳するのは README だけです。それ以外のすべてのファイル（`CLAUDE.md`、`SKILL.md`、`references/*.md`、`agents/*.md`、`CHANGELOG.md`、フックのメッセージ）は英語で書きます。ユーザーの入力と一致する必要があるトリガーフレーズは、その言語のまま残します。

## ライセンス

MIT。[LICENSE](LICENSE) を参照してください。
