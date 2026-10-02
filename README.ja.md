<p align="center">
  <strong>because-i-needed</strong>
</p>

<p align="center"><strong>Claude Code</strong> と <strong>Codex CLI</strong> でのみ動作します。</p>

<p align="center">
  <strong>必要だから作った Claude Code と Codex プラグイン集 — プロジェクトハーネス、実測ベースの UI、Claude × Codex のオーケストレーション、自律ゴール実行。</strong>
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

このリポジトリは、独立した4つのプラグインを収めた Claude Code と Codex の**プラグインマーケットプレイス**です。必要なものだけをインストールしてください。

## Codex

同じ4つのプラグインを Codex CLI 0.158.0 以降でも使用できます。必要なものを選んでインストールします。

```bash
curl -fsSL https://raw.githubusercontent.com/zeriong/because-i-needed/main/install.sh | bash -s -- --host codex --only harness,ux-ui,peer-coding,free-hands
```

CLI から直接インストールすることもできます。

```bash
codex plugin marketplace add https://github.com/zeriong/because-i-needed.git
codex plugin add harness@because-i-needed
codex plugin add ux-ui@because-i-needed
codex plugin add peer-coding@because-i-needed
codex plugin add free-hands@because-i-needed
```

新しい Codex セッションで `$harness:build`、`$ux-ui:build`、`$ux-ui:build-mobile`、`$peer-coding:run`、`$free-hands:run` を呼び出します。自動オーケストレーションは `$peer-coding:mode on`、コンテキスト点検は `$peer-coding:audit` です。自動ルーティング、UI コミットゲート、free-hands の強制動作を使う前に、`/hooks` でフックを確認して信頼してください。

インストーラーの既定は Claude Code です。`--host codex` で Codex を選択します。Codex はユーザースコープのみで、`--scope` を省略するか `--scope user` を指定します。project/local は拒否されます。スキル、スクリプト、作業手順は共有し、各プラグインに Codex マニフェストを同梱します。Codex では独自の質問ツールと独立したエージェントを使用します。ハーネスは `.codex/hooks.json`、`.codex/hooks/`、`.codex/scripts/review-gate.sh`、`.codex/scripts/latest-model.py`、`.agents/skills/` を生成し、既存の Claude ファイルを保持します。UI の実測には対応するブラウザー・モバイルツールが必要です。詳細は各プラグインの Codex 節を参照してください。

各プラグインの Codex 節に設定方法があります。執筆者・レビュアーごとにモデルと推論強度を指定でき、未設定の役割はアクティブなセッションのファミリーの最新モデルで実行します。ハーネスは Claude・Codex・両方の構成を生成できます。CXC のクロスベンダールーティングは維持されます。ブラウザー・デバイス要件とフック信頼は引き続き必要です。

## プラグイン

### [harness](plugins/harness) · `v1.3.0`

**テンプレートではなく、事実に基づく分析からプロジェクト専用の Claude Code・Codex ハーネスを構築します**。リポジトリの実際のレイヤー構成と関心の分離を読み取り、すべてのルールがあなたのコードの `file:line` を引用する形で導出したうえで、`project-rules`、決定論的な `review-gate.sh`、`UserPromptSubmit` フック、`harness-engineering` スキルを生成します。

- **使いどころ:** ハーネスがないプロジェクトで Claude Code または Codex の作業を始めるとき、または構成が大きく変わり、既存のセットアップが合わなくなったとき。
- **エントリーポイント:** `/harness:build`、または *「build harness」*

[harness の日本語 README を読む →](plugins/harness/README.ja.md)

### [ux-ui](plugins/ux-ui) · `v1.4.1`

**実際のレンダリングを実測しながら Web とモバイルの UI を構築します**。実際のスクリーンショットを撮影し（Web は chrome-devtools、React Native / Flutter / iOS / Android はモバイル MCP または CLI スナップショットハーネス）、アートディレクターエージェントにその実測スナップショットを批評させ、UI が正確かつエレガントになるまで反復し、ステージされた diff そのものが APPROVED されるまで UI の `git commit` をブロックします。

- **使いどころ:** コンポーネント、ページ、画面を作成・変更するときに、想像ではなく実際のレンダリングで検証したいとき。
- **エントリーポイント:** `/ux-ui:build`（Web）· `/ux-ui:build-mobile`（モバイル）、または UI の作成を依頼するだけ
- **注意:** インストールすると、`PreToolUse` のコミットゲートフック（すべての `Bash` 呼び出しの前に実行され、UI のコミットだけをブロック）と 4 つの MCP サーバーが登録されます。

[ux-ui の日本語 README を読む →](plugins/ux-ui/README.ja.md)

### [peer-coding](plugins/peer-coding) · `v1.0.0`

**Claude × Codex のピアオーケストレーション**。メインエージェントが計画してすべてのゲートを判断し、作業を高速な Claude ワーカーか大量処理向けの Codex ワーカーに振り分け、2 つのベンダーが互いの作業をレビューします — メインエージェント自身の計画も含みます。反論は 1 回で、判定するのは役割ではなく証拠です。監査機能が、両ベンダーが同じプロジェクトの指示から始められるかを確認します。非公式のコミュニティプラグインです。

- **使いどころ:** Claude Code と Codex の両方を使っていて、機能のすべての段階で別ベンダーのレビューを受けたいとき。
- **エントリーポイント:** `/peer-coding:run`、または `/peer-coding:mode on` でオンにすると実装の依頼がこの流れを通ります
- **注意:** インストールすると `UserPromptSubmit` フックが登録されます（すべてのプロンプトで実行され、モードがオフの間は何も出力しません）。

[peer-coding の日本語 README を読む →](plugins/peer-coding/README.ja.md)

### [free-hands](plugins/free-hands) · `v0.2.0`

**有限の目標を、質問や中断なしでチェックリストの最後まで進めます。** ユーザーが決める場面では5役のパネルが助言し、メインエージェントが証拠に基づいて決定します。

- **使いどころ:** 決定を記録し、中断後にも再開できる範囲の定まった目標を任せたいとき。
- **エントリーポイント:** `/free-hands:run <目標>`（Claude Code）· `$free-hands:run <目標>`（Codex）、またはプロンプトに「free-hands」と書いて開始確認を一度受ける
- **注意:** フックはプロンプト、セッション開始、質問、シェルコマンド、停止ごとに実行されます。有効な目標がなければ、プロンプトに「free-hands」とある場合の一度だけの開始質問を除いて何も出力しません。未完了項目がある間、Stop は最大40回ターンを続けます。目標が有効な間は、補助フックがデフォルトブランチへのマージ・リモート削除・デプロイ・公開を行う一覧のシェルコマンドを拒否します（プラグイン README を参照）。

[free-hands の日本語 README を読む →](plugins/free-hands/README.ja.md)

## 退役したプラグイン

### plan-smith — 2026-09-30 退役（最終バージョン 1.8.0）

z-lab では、plan-smith 1.6.0 のパイプライン（Claude Code、1タスク）は、同じモデルが計画と実装を行う場合に純コストでした。計画だけで、計画・実装のベースチェーン全体の約1.65倍（Fable 5.1、完了）と少なくとも2.41倍（Opus 5.5、中断）のトークンを使い、ベース計画は最初の試行で完成していました。各数値はモデルごとに1回だけ実行した結果です。節約は近似パイプラインでのみ測定され、実際のパイプラインでの弱い実装者の影響と計画の品質は測定されていません。[測定結果](https://github.com/zeriong/z-lab/tree/main/plan-smith-lab/real-skill-tco-1.6.0)と[退役の決定](https://github.com/zeriong/z-lab/tree/main/plan-smith-lab/analyze)を参照してください。最後のソース（1.8.0）はこのリポジトリの git 履歴に残り、1.4.2 までのバージョンは[zeriong/plan-smith](https://github.com/zeriong/plan-smith)にあります。

インストール済みのコピーを削除するには:

- Claude Code: `claude plugin uninstall plan-smith@bin`（project または local スコープでインストールした場合は `--scope project` または `--scope local` を追加してください。） <!-- legacy-id -->
- Codex: `codex plugin remove plan-smith@bin` <!-- legacy-id -->

## インストール

インストーラーがプラグインの一覧を表示し、選んだものだけをインストールします。

```bash
curl -fsSL https://raw.githubusercontent.com/zeriong/because-i-needed/main/install.sh | bash
```

↑/↓（または j/k）で移動、space で選択の切り替え、`a` で全選択、enter でインストール、`q` で終了 — 最初はすべて選択されています。オプション: `--all`、`--only a,b`、`--list`、`--dry-run`、`--scope user|project|local`。パイプ経由で実行するときは `bash -s --` の後ろに付けます（例: `… | bash -s -- --only harness`）。内部では下と同じ `claude plugin` コマンドを実行します。

または、マーケットプレイスを自分で追加してから、使いたいプラグインをインストールします。

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install harness@because-i-needed
claude plugin install ux-ui@because-i-needed
claude plugin install peer-coding@because-i-needed
claude plugin install free-hands@because-i-needed
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
    "harness@because-i-needed": true,
    "ux-ui@because-i-needed": true,
    "peer-coding@because-i-needed": true,
    "free-hands@because-i-needed": true
  }
}
```

### 以前 `bin` としてインストールした場合

マーケットプレイス名が `bin` から `because-i-needed` に変わりました。プラグイン名とコマンドは変わりません。アンインストールしてから、上の手順で再インストールしてください：

```bash
# Claude Code — マーケットプレイスを削除すると、そのプラグインもアンインストールされます
claude plugin marketplace remove bin
# Codex — インストール済みのプラグインを先に削除します。削除しないと古いコピーが読み込まれ続けます
codex plugin remove harness@bin
codex plugin remove ux-ui@bin
codex plugin remove claude-x-codex@bin
codex plugin marketplace remove bin
```

古い ID（`<plugin>@bin`）に紐づく設定は引き継がれません。

### 以前 claude-x-codex をインストールした場合

プラグイン名が `claude-x-codex` から `peer-coding`（1.0.0）に変わりました。Claude Code が `claude-` で始まるプラグイン名を予約しているためです。コマンドは `/claude-x-codex:…` から `/peer-coding:…` に変わります（Codex は `$peer-coding:…`）。マーケットプレイスを更新し、旧プラグインをアンインストールしてから、上の手順で `peer-coding` をインストールしてください：

```bash
claude plugin marketplace update because-i-needed
claude plugin uninstall claude-x-codex@because-i-needed
# Codex
codex plugin marketplace upgrade
codex plugin remove claude-x-codex@because-i-needed
```

モードフラグ（`.claude-x-codex/mode`、`~/.config/claude-x-codex/mode`）と `CXC_*` 変数名は変わらないため、既存の設定はそのまま適用されます。プロジェクトの `.claude/settings.json` にある `claude-x-codex@because-i-needed` は `peer-coding@because-i-needed` に書き換えてください。`.claude-x-codex/<feature>/` の作業は `/peer-coding:run` で再開できます。

## 命名規則

すべてのコマンドは **対象 : 動作** と読めます — `/<プラグイン>:<スキル>`。

- **プラグイン = 対象** — 何を扱うか（`harness`、`ux-ui`）。
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

現時点で `forge` と `review` を使うプラグインはありません。

## リポジトリ構成

```
because-i-needed/
├── .claude-plugin/marketplace.json   # 4 つのプラグインを登録
├── install.sh                        # 対話式インストーラー（--host claude|codex）
└── plugins/
    ├── harness/                      # スキル
    ├── ux-ui/                        # スキル 2 + エージェント 2 + コミットゲートフック + MCP 4
    ├── peer-coding/                  # スキル 3 + プロンプトフック + スクリプト 3
    └── free-hands/                   # スキル 1 + エージェント 5 + フック 4 + スクリプト 4
```

各プラグインフォルダは自己完結しています。README、マニフェスト、配布されるすべてのファイルが `plugins/<名前>/` の下にあります。

## 言語ポリシー

- このリポジトリのすべての README（本書と各プラグインの README）は **5 つの言語**で提供されます: `README.md`（英語、原本）、`README.ko.md`（한국어）、`README.ja.md`（日本語）、`README.zh-CN.md`（简体中文）、`README.zh-TW.md`（繁體中文）。
- README を変更するときは、同じコミットで 5 つすべてを更新します。新しいプラグインは、最初のコミットから 5 言語すべてを揃えます。
- 翻訳するのは README だけです。それ以外のすべてのファイル（`CLAUDE.md`、`SKILL.md`、`references/*.md`、`agents/*.md`、`CHANGELOG.md`、フックのメッセージ）は英語で書きます。ユーザーの入力と一致する必要があるトリガーフレーズは、その言語のまま残します。

## ライセンス

MIT。[LICENSE](LICENSE) を参照してください。
