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

### [plan-smith](plugins/plan-smith) · `v1.4.2`

**2 段構成のパイプラインでプランを鍛え上げます**。メインエージェントが会話全体をコンテキストパケット（目標、ハード制約、却下された代替案）に蒸留してあなたに確認し、続いてクリーンなコンテキストの `plan-writer` エージェントが推論フレームライブラリと検証済みの執筆スタイルでプランを書きます。完成したプランは原文のまま届けられます — 要約による欠落も、コンテキスト汚染もありません。

- **使いどころ:** マイグレーション、ローンチ、build-out など、長くノイズの多いセッションではプランがぼやけてしまいがちな作業の計画が必要なとき。
- **エントリーポイント:** `/plan-smith:plan-smith <タスク>`、または単に *「… のプランを書いて」*

[plan-smith の日本語 README を読む →](plugins/plan-smith/README.ja.md)

### [harness-builder](plugins/harness-builder) · `v1.0.0`

**テンプレートではなく、事実に基づく分析からプロジェクト専用の Claude Code ハーネスを構築します**。リポジトリの実際のレイヤー構成と関心の分離を読み取り、すべてのルールがあなたのコードの `file:line` を引用する形で導出したうえで、`project-rules`、決定論的な `review-gate.sh`、`UserPromptSubmit` フック、`harness-engineering` スキルを生成します。

- **使いどころ:** `.claude/` のセットアップがないプロジェクトで Claude Code の作業を始めるとき、または構成が大きく変わり、既存のセットアップが合わなくなったとき。
- **エントリーポイント:** `/harness-builder:harness-builder`、または *「build harness」*

[harness-builder の日本語 README を読む →](plugins/harness-builder/README.ja.md)

### [ux-ui-builder](plugins/ux-ui-builder) · `v1.1.0`

**実際のレンダリングを実測しながら Web とモバイルの UI を構築します**。実際のスクリーンショットを撮影し（Web は chrome-devtools、React Native / Flutter / iOS / Android はモバイル MCP または CLI スナップショットハーネス）、アートディレクターエージェントにその実測スナップショットを批評させ、UI が正確かつエレガントになるまで反復し、ステージされた diff そのものが APPROVED されるまで UI の `git commit` をブロックします。

- **使いどころ:** コンポーネント、ページ、画面を作成・変更するときに、想像ではなく実際のレンダリングで検証したいとき。
- **エントリーポイント:** `/ux-ui-builder:ux-ui-builder`（Web）· `/ux-ui-builder:ux-ui-builder-mobile`（モバイル）、または UI の作成を依頼するだけ
- **注意:** インストールすると、`PreToolUse` のコミットゲートフック（すべての `Bash` 呼び出しの前に実行され、UI のコミットだけをブロック）と 4 つの MCP サーバーが登録されます。

[ux-ui-builder の日本語 README を読む →](plugins/ux-ui-builder/README.ja.md)

## インストール

マーケットプレイスを一度追加してから、使いたいプラグインをインストールします。

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install plan-smith@because-i-needed
claude plugin install harness-builder@because-i-needed
claude plugin install ux-ui-builder@because-i-needed
```

または Claude Code 内で `/plugin` → Marketplaces → Add Marketplace → `https://github.com/zeriong/because-i-needed.git` と進み、一覧からインストールします。

または `~/.claude/settings.json` に直接記述します。

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

## リポジトリ構成

```
because-i-needed/
├── .claude-plugin/marketplace.json   # 3 つのプラグインを登録
└── plugins/
    ├── plan-smith/                   # スキル + plan-writer エージェント (+ CHANGELOG.md)
    ├── harness-builder/              # スキル
    └── ux-ui-builder/                # スキル 2 + エージェント 2 + コミットゲートフック + MCP 4
```

各プラグインフォルダは自己完結しています。README、マニフェスト、配布されるすべてのファイルが `plugins/<名前>/` の下にあります。

## 言語ポリシー

- このリポジトリのすべての README（本書と各プラグインの README）は **5 つの言語**で提供されます: `README.md`（英語、原本）、`README.ko.md`（한국어）、`README.ja.md`（日本語）、`README.zh-CN.md`（简体中文）、`README.zh-TW.md`（繁體中文）。
- README を変更するときは、同じコミットで 5 つすべてを更新します。新しいプラグインは、最初のコミットから 5 言語すべてを揃えます。
- Claude が直接読み込むファイル（`SKILL.md`、`references/*.md`、`agents/*.md`）は英語のまま維持します。

## ライセンス

MIT。[LICENSE](LICENSE) を参照してください。
