<p align="center">
  <strong>harness-builder</strong>
</p>

<p align="center">
  <strong>プロジェクトに合わせた Claude Code ハーネスを構築します — テンプレートではなく、事実に基づく分析から。</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-1.0.0-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a>
</p>

<p align="center">
  <a href="#インストール">インストール</a> &bull;
  <a href="#できること">できること</a> &bull;
  <a href="#8-phase-ワークフロー">ワークフロー</a> &bull;
  <a href="#fact-check-ループ">Fact-check ループ</a> &bull;
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
  <sub><a href="../../README.ja.md">because-i-needed</a> のプラグイン</sub>
</p>

---

「Claude Code ハーネス」をうたうプラグインの多くは、決まった `.claude/` の骨組みを量産して終わりにします。そこで強制されるルールは*プラグインの作者*が思いついたルールであって、*あなたのプロジェクトが実際に必要とする*ルールではありません。

**harness-builder はこれを逆転させます**。まずプロジェクトを読み、実際にそこにあるものからルールを導き出し、そのうえで初めて*そのルール*を強制するハーネスを形にします。結果として得られるのは、あなたのリポジトリに合わせて仕立てられた `.claude/` ディレクトリで、すべてのルールはあなた自身のコードの `file:line` 引用までたどれます。

## 特長

- **事実に基づくルールの導出** — すべてのルールは、テンプレートではなく実際のコードに対する verdict から生まれます。`file:line` の引用がない主張は破棄されます。
- **ゲート優先の強制** — 決定論的にチェックできるルールは、`review-gate.sh` の終了コードによるゲートになります。定性的にしか判断できないルールは advisory として残し、プロンプトのたびに Claude に提示します。
- **副作用を考慮した回帰** — ビルド中にパッチが 1 つでも適用されると、Phase 1 に戻ることが強制されます。ハーネスは、1 行の変更がそれまでのすべての verdict を無効にしうると想定しています。
- **2 人のレビュアーによるクロスチェック** — 完了を宣言する前に、Opus と Sonnet のエージェントを 1 つずつ並列に起動し（fresh-spawn、コンテキストの共有なし）、6 つの品質軸に沿った両者の JSON レポートを統合します。
- **Worse / better case のインデックス化** — すべてのルールには `docs/conventions/<rule>.md` が付属し、あなたのリポジトリにある実際の問題コードと、実際により良い形、そして grep しやすいキーワードが含まれます。
- **デフォルトで YAGNI** — リポジトリ内の違反が 0 件で、ユーザーからの言及もないルールは導入されません。5 ルールで足りるプロジェクトに 5 ルールのハーネスができるのは成功であって、失敗ではありません。

## 使いどころ

- `.claude/` のセットアップがまだないプロジェクトで、Claude Code の作業を始めるとき。
- プロジェクトの構成が大きく変わり、既存の `.claude/` を作り直すとき。
- 抽象的な規約ではなく、リポジトリの実際のコードに結びついたルールが欲しいとき。

**使わなくてよいとき:**

- 単一ファイルのユーティリティや使い捨てのスクリプト — ハーネスは過剰です。
- 信頼できる `.claude/` をすでに構築し、手入れしてきたプロジェクト。
- 明確なレイヤー構成がないリポジトリ（fact-check ループには手がかりとなる構造が必要です）。

## インストール

### Claude Code プラグインマーケットプレイスから

1. Claude Code で `/plugin` を実行します。
2. Marketplaces → Add Marketplace を選びます。
3. URL を入力します: `https://github.com/zeriong/because-i-needed.git`。
4. `harness-builder` をインストールします。

### または CLI から

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install harness-builder@because-i-needed
```

### または `~/.claude/settings.json` に直接記述

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

## クイックスタート

```
cd your-project
# Claude Code で:
/harness-builder:harness-builder
```

自然な言葉で頼むこともできます — トリガーキーワード（韓国語 / 英語）: `harness 만들어`、`build harness`、`harness 셋업`、`프로젝트 룰 추출`、`review gate 깔아줘`、`harness-builder`。

スキルが行うこと:

1. プロジェクトについて 4 つの質問をします（パッケージマネージャー、モノレポの形、lint / typecheck コマンド、必ず守らせたいルール）。
2. コードベースを読み、レイヤーごとに fact-check ループを実行します。
3. ルールを導出し、ゲートスクリプトを生成し、フックを配線し、スキルを書き、規約ドキュメントをインデックス化します。
4. わざと違反させたサンプルで、すべてが機能することを検証します。
5. 最終チェックのために、2 人のレビュアーによるパネルを起動します。

全体の実行には通常、複数のターンがかかります — スキルはそのことを正直に伝えます。`/loop` で包むこともできますが、必須ではありません。

## できること

プロジェクトのルートに書き出される出力:

```
.claude/
├── settings.json                    # UserPromptSubmit フックの配線
├── hooks/inject-context.sh          # プロンプトごとに project-rules + harness-engineering を注入
├── scripts/review-gate.sh           # 決定論的ゲート — exit 0 / 1 / 2
└── skills/
    ├── project-rules/SKILL.md       # Phase 1–2 であなたのコードから導出したルール
    └── harness-engineering/SKILL.md # 今後のタスク向けの 11-phase ワークフロー

docs/conventions/
├── <rule-1>.md                      # Worse case + better case (リポジトリの実際のコード) + キーワードインデックス
├── <rule-2>.md
└── ...
```

ビルド後は、プロジェクト内のすべてのユーザープロンプトで `project-rules` とハーネスの各 phase が自動的に読み込まれます。フロントエンドのコードなら、導出されたレイヤー分離ルールが発動します。300 行のコンポーネントを編集しようとすれば、導出されたファイル長の上限がブロックします。ルールはプラグインのものではなく、あなたのものです。

プラグイン自体に含まれるスキルは 1 つだけです: [`skills/harness-builder/SKILL.md`](skills/harness-builder/SKILL.md) — 以下で説明する 8-phase のビルドです。

## 8-Phase ワークフロー

| Phase | 責務 | Fact-check ループ必須 |
|-------|------|-----------------------|
| 0 | **Intake** — パッケージマネージャー、モノレポの形、既存のスクリプト、ユーザーが推奨するルール | — |
| 1 | **Layer / Concern Reconnaissance** — すべての主張に `file:line` を引用 | ✅ 必須 |
| 2 | **Convention Extraction** — Phase 1 の verdict をルールにする | ✅ |
| 3 | **`docs/conventions/<rule>.md`** — リポジトリの実際のコードからインデックス化した worse / better case | ✅ |
| 4 | **Gate script**（`review-gate.sh`）の生成 | — |
| 5 | **Hook の配線**（`UserPromptSubmit`） | — |
| 6 | **Skill の本文**（`project-rules` + `harness-engineering`） | — |
| 7 | **Self-verification** — サンプルの diff でゲートを動かして確認 | — |
| 8 | **Review gate** — Opus + Sonnet による 1-shot レビュー、メインがパッチを統合 | — |

**Phase 8 でパッチが 1 つでも適用されると、Phase 1 への回帰が強制されます**。これはヒューリスティックではなく絶対的なルールです — 副作用によってそれまでの verdict が無効になると想定しています。反復の上限は 3 回で、収束しなければ、スキルはありのままの失敗レポートを出力してあなたの判断を待ちます。

## Fact-check ループ

これはスキルの中で最も重要なルールです。Phase 1 があなたのコードについて行うすべての主張は、次の手順を通過しなければなりません:

```
主張:         "src/components/admin/audit-logs/page.tsx は presentation だけを持つ"
              ↓
自己懐疑:     "本当に？ 検証しよう。"
              ↓
直接読む:     Read ツールでファイルを開く — 記憶も推論も使わない
              ↓
スコープ走査: 同じディレクトリ全体に grep "useState|useEffect|fetch"
              ↓
副作用:       grep -r でこのモジュールの import 元を調べる
              ↓
SRP テスト:   変更される理由はちょうど 1 つか？
              ↓
Verdict:      "presentation + data が混在 — page.tsx:24-31 が fetch() を呼んでいる"
              file:line の引用付き
              ↓
次の phase へ進む
```

どれか 1 つでもステップを飛ばした主張は**破棄**され、Phase 1 がやり直しになります。導出されたルールが信頼できるのはこのためです — ルールはモデルの直感からではなく、リポジトリ内の検証可能な事実から生まれています。

## 高品質の定義

スキルが適用を検討するすべてのパッチは、6 つの軸で自己採点されます（各 0–5 点）:

| 軸 | 意味 |
|----|------|
| **SRP** | モジュールごとに変更される理由は 1 つ |
| **コメントの明快さ** | 簡潔で要点のみ、2 行以内 |
| **KISS** | 問題を解決する最もシンプルな形 |
| **DRY** | モジュール間でロジックが重複しない |
| **YAGNI** | 推測に基づく機能やルールを入れない |
| **認知的な容易さ** | 人間の読み手が苦労せずに理解できる |

平均が 3.5 未満のパッチは却下されます。却下率が高い場合は、該当する phase が回帰します。

## ハーネスのバイパス

ビルド後は、すべてのユーザープロンプトで注入フックが発動します。1 ターンだけバイパスするには:

- プロンプトの先頭に `!` を付けます（例: `!答えだけ教えて`）
- または、認識されるバイパスフレーズ（韓国語 / 英語）を含めます: `harness 빼고`、`without harness`、`skip harness`、`no harness`

バイパスモードでは、そのターンの phase の強制だけが無効になり、project-rules は引き続き表示されます。

## FAQ

**なぜ `.claude/` のテンプレートをそのまま渡さないのですか？**
テンプレートでは*他の誰かの*ルールを強制することになるからです。このスキルの目的は、*あなたのプロジェクトの*ルールを、実際のコードから導出したうえで強制することです。あなたのコードベースにある 200 LOC のコンポーネントは、他の誰かのコードベースにある 200 LOC のコンポーネントと同じ意味を持ちません。上限はあなたのコードから決めるべきです。

**linter や ESLint の設定とは何が違うのですか？**
linter は構文や既知のアンチパターンをチェックします。このスキルは、linter がうまくモデル化できない構造上の関心事（レイヤー分離、SRP、ファイル長、命名）をチェックし、各ルールをリポジトリの `file:line` に結びつけて、違反に文脈を与えます。置き換えるものではなく、補完し合うものです。

**なぜレビュアーが 5 人ではなく 2 人なのですか？**
このスキルの元になった setup-guide では、Opus 2 + Sonnet 3 の 5 エージェントによるパネルを使います。ビルドの最後に 1 回だけ行うレビューには、それは過剰設計です — 3–5 番目のエージェントがもたらす限界的な利点は、レイテンシに見合いません。Opus 1 + Sonnet 1 で、モデルの多様性による利点の大部分を 5 分の 1 のコストで得られます。

**Phase 1 が、プロジェクトはすでに完璧にレイヤー化されていると判定したら？**
その場合、レイヤー分離のルールは導入されません。YAGNI が適用されます — 違反が 0 件でユーザーの言及もないルールは、追加が禁止されています。気になるのが命名だけなら、ルールが 1 つだけのハーネスになります。

**ビルド後に、生成された `.claude/` を編集してもいいですか？**
はい。出力はあなたのものです。スキルは生成したファイルを追跡も再同期もしません。`/harness-builder:harness-builder` を再実行する場合は、マージを自分で行う必要があります。

**フロントエンド以外のプロジェクトでも動きますか？**
Phase 1 のレイヤーのシグナルは、フロントエンドのリポジトリ（`*.tsx`、`use-*.ts`、`api/*`）向けに調整されています。Go のサービスや Python のバックエンドでは、別のレイヤー識別シグナルが必要になります — Phase 0 の自由記述の質問は、まさにそのためにあります。スキルの*ワークフロー*はプロジェクトに依存せず、調整されているのは Phase 1 のヒューリスティックだけです。

## 動作要件

- `git`、`jq`、`bash 4+`
- 対象プロジェクトが git の work tree であること
- プラグインに対応した Claude Code

## ライセンス

MIT。[LICENSE](../../LICENSE) を参照してください。

## 謝辞

8-phase ワークフローは、作者が執筆した非公開のハーネス setup-guide と research-foundation に由来します。fact-check ループのパターンは、CRITIC（Gou et al. 2023）と、Anthropic の Multi-Agent Research System に関するエンジニアリングブログの影響を受けています。収束の上限（= 3）は Reflexion（Shinn et al. 2023）から採用しました。
