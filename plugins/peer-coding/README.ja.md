<p align="center">
  <strong>peer-coding</strong>
</p>

<p align="center"><strong>Claude Code</strong> と <strong>Codex CLI</strong> でのみ動作します。</p>

<p align="center">
  <strong>Claude × Codex のピアオーケストレーション — 2 つのエージェントが同僚として、互いの計画・実装・レビューを担います。</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-1.2.0-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a>
</p>

<p align="center">
  <a href="#インストール">インストール</a> &bull;
  <a href="#コマンド">コマンド</a> &bull;
  <a href="#仕組み">仕組み</a> &bull;
  <a href="#設定">設定</a> &bull;
  <a href="#プラットフォーム">プラットフォーム</a>
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

Claude × Codex のピアオーケストレーションです。土台の異なる 2 つのエージェントは異なる形で間違えるため、それぞれが相手の作業をレビューします — メインエージェント自身の計画も例外ではありません。意見が分かれたときに判定するのは、役割ではなくテストです。

peer-coding は非公式のコミュニティプラグインです。Anthropic や OpenAI が作成・保証・サポートしているものではありません。

## Codex

Codex CLI 0.158.0 以降が必要です。インストール後、新しいセッションを開始してください。Claude は `/plugin:skill`、Codex は `$plugin:skill` を使います。共通のスキルと資料はこのプラグインに同梱されています。自動動作を利用する前に `/hooks` で同梱フックを確認して信頼してください。

```bash
codex plugin marketplace add https://github.com/zeriong/because-i-needed.git
codex plugin add peer-coding@because-i-needed
```

`$peer-coding:run`、`$peer-coding:mode on|off|status|clear`、`$peer-coding:mode <setting> <value>`、`$peer-coding:audit` を使います。モード操作は両ホストともユーザーの明示的な要求が必要です。Codex をメインにでき、既存の Codex アダプターがベンダー間レビューを維持します。監査は `.codex/hooks.json` と未コミットの `.codex/`、`.agents/` も対象です。自動モードには UserPromptSubmit フックの信頼が必要ですが、明示的な run はフックに依存しません。Codex がメインの場合、ベンダー間作業には Claude CLI が必要で、なければ既存の単一ベンダー経路を使います。

### Codex 設定

両ホストで同じモデル設定・モード範囲・クロスベンダーレビュー規則を使用します。Codex にはプラグインの設定メニューがないため、`$peer-coding:mode <setting> <value>` でモデルと推論強度を設定します（[設定](#設定)参照）。Claude Code の `/config` で選んだ値もここに適用されます。 リンクされた Git worktree でもモードファイルをローカル除外します。監査は設定を変更せず、`AGENTS.override.md` の優先順位と不正なフック宣言を報告します。

各ホストのルーティングは設定された レビュアーモデルと推論強度を使い、括弧内は既定値です。ファイル名や fallback 設定への言及だけでは指示の一致を断定せず、実効内容の確認が必要な CHECK として報告します。

## コマンド

| コマンド | 内容 |
|---|---|
| `/peer-coding:run` | タスクをオーケストレーションします。メインエージェントが計画してすべてのゲートを判断し、作業を `claude-fast` / `codex-bulk` / `main` のレーンに振り分け、各ベンダーに相手ベンダーの作業をレビューさせます |
| `/peer-coding:mode on\|off\|status\|clear [--global]` | 自動オーケストレーションをオン / オフする 1 行のスイッチです。ユーザー専用で、モデルは切り替えられません |
| `/peer-coding:mode <setting> <value>\|unset [--global]` | ワーカーレーンまたはレビュアーのモデルファミリーか推論強度を選択します（[設定](#設定)）。`status` は 6 項目をすべて表示します |
| `/peer-coding:audit` | 両ベンダーが同じプロジェクトの文脈から始められるかを読み取り専用で点検します。修正案を提案するだけで、何も変更しません |

`on`・`off` はこのプロジェクトのフラグ（`.claude-x-codex/mode`、git から除外）を書き込み、`--global` はすべてのプロジェクトに適用される既定値（`~/.config/claude-x-codex/mode`）を書き込みます。`clear` はプロジェクトのフラグを削除し、`CXC_MODE=on|off` は 1 つのシェルで両方より優先されます。モードがオフのとき、`run` は依頼されたときだけ開始します。[dashboard](../dashboard) プラグインは、有効なモードとその出どころ、ワーカーとレビュアーのモデルおよび推論強度を表示します（`mode.sh status --json`、`settings.py status --json`、`dashboard.json` で宣言）。

## インストール

### Claude Code プラグインマーケットプレイスから

1. Claude Code で `/plugin` を実行します。
2. Marketplaces → Add Marketplace。
3. URL を入力します: `https://github.com/zeriong/because-i-needed.git`（またはこのリポジトリのローカルパス）。
4. `peer-coding` をインストールします。

### または CLI から

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git   # またはローカルパス
claude plugin install peer-coding@because-i-needed
```

### または `~/.claude/settings.json` に直接記述

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

- **注意:** インストールすると `UserPromptSubmit` フックが登録されます。すべてのプロンプトで実行されますが、モードがオフの間は何も出力しません。オンのときは、実装作業を `run` に回すよう指示する 4 行のメモ（プロンプトごとに入力約 100 トークン）を追加します。

## 動作要件

- **Claude Code**（またはメインエージェントとしての Codex）、**git** リポジトリ、bash 3.2+。
- **任意 — Codex CLI**（`codex`）。ない場合、`run` は single-vendor モードに切り替わり、すべてのレビューを同じベンダーの別のレビュアーインスタンスに任せ、そのことを伝えます。
- **任意 — Orca**（オーケストレーションを有効化）。あればワーカーが作業中に質問でき、ゲートがユーザーの判断を待ちます。なければワーカーはサブエージェントや CLI 呼び出しとして一方向に実行されます。
- モデル設定、最新モデルの解決、監査のフック表には `python3` が、Codex がメインエージェントとして Claude レビュアーを動かすときは `jq` が必要です。
- Claude Code 2.1.283、Codex CLI 0.157.1、Orca 1.4.215 で確認し、モデル設定と `/config` の選択項目は Claude Code 2.1.314 と Codex CLI 0.166.0 でも確認しています。

## 仕組み

- **レーン** — ワーカーはワーカーの effort（既定値 `high`）で動きます。`claude-fast`（既定では Claude の最新 Sonnet: UI、インタラクション、コードのセンス、Claude 側のツール）、`codex-bulk`（既定では Codex の最新 `terra`: 既存の契約に対するテスト、型、機械的なマイグレーションなど結果が完全に決まっている作業）、`main`（メインエージェント: 密結合な作業や、仕様がまだ固まっていない作業）。
- **クロスベンダーレビュー** — レビュアーは常に作成者と別のベンダーで、メインエージェント自身の計画や振り分けの判断も相手ベンダーがレビューします。既定では Claude は最新 Opus、Codex は最新 `sol` でレビューし、どちらも effort `xhigh`（両 CLI で `max` のすぐ下の段階）です。それぞれ設定でき（[設定](#設定)）、例えば Codex レビュアーに `astra` を指定すれば、モデルと推論強度は指定どおりに動きます。認証・決済・データ移行などの高リスクな段階では、最上位モデル（Codex の最新 `astra` または `max` の Claude 最新 Opus）のレビューを追加する前に `run` がユーザーに確認します。レビュアー設定がすでにその値なら提案せず、設定を超えて自動的に引き上げません。レビュアーは読み取り専用で動き、両 CLI がスキーマで強制する JSON を返します。
- **反論は 1 回** — 却下された blocking・major の指摘は、理由とともに一度だけレビュアーへ戻ります。レビュアーは受け入れるか、新しい証拠で反論します。それでも解決しなければ、両者の主張とともに DISPUTED としてユーザーに上がります。
- **証拠が判定する** — 意見が分かれたら、テスト・再現・トレースのどれかを持つ側が勝ちます。証拠がなければユーザーが決めます。
- **コンテキストブリッジ** — 監査は、2 つのベンダーが別々の指示ファイルを読んでいる場所、片方のベンダーにしか効かないフック、ワーカーの worktree に欠けるコミットされていない文脈を見つけます。`run` が行う Codex の呼び出しは Codex のフォールバック設定で `CLAUDE.md` を読むので、リポジトリの変更は不要です。対話型の Codex セッション（Orca のワーカー、またはメインエージェントとしての Codex）では、同じ設定がユーザーの Codex 設定に必要です。ユーザーの設定やリポジトリを変える修正は、計画の承認時に提案します。
- **ディスク上の状態** — `.claude-x-codex/`（git から除外）に計画・判断・レビューが残るため、実行はコンパクションを経ても再開できます。

専用の計画スキルが利用できる場合、`run` は計画をそのスキルに任せます。

## 設定

6 つの設定でモデルと推論強度を選びます。各設定はモードと同様に永続し、次の順序で最初に一致した値が使われます:

1. 1 つのシェルに適用する `CXC_*` 変数
2. このプロジェクト — `/peer-coding:mode <setting> <value>` で書き込む `.claude-x-codex/settings`（git から除外）
3. **Claude Code の `/config`** — 6 項目を選択できます（`peer-coding` と入力して検索）。選択は全プロジェクトの既定値です
4. グローバルファイル — `/peer-coding:mode <setting> <value> --global` で書き込む `~/.config/claude-x-codex/settings`（プラグインの設定メニューがない Codex での方法）
5. 既定値

| 設定 | 変数 | 既定値 | 選択対象 |
|---|---|---|---|
| `codex-worker` | `CXC_WORKER_MODEL` | `terra` | `codex-bulk` レーンのモデル |
| `codex-reviewer` | `CXC_REVIEW_MODEL` | `sol` | Codex レビュアーのモデル |
| `claude-worker` | `CXC_CLAUDE_WORKER` | `sonnet` | `claude-fast` レーンのモデル |
| `claude-reviewer` | `CXC_CLAUDE_REVIEWER` | `opus` | Claude レビュアーのモデル |
| `worker-effort` | `CXC_WORKER_EFFORT` | `high` | 両ベンダーのワーカー |
| `review-effort` | `CXC_REVIEW_EFFORT` | `xhigh` | 両ベンダーのレビュアー |

```text
/peer-coding:mode codex-reviewer astra          # このプロジェクト
/peer-coding:mode worker-effort xhigh --global  # 全プロジェクト
/peer-coding:mode codex-reviewer unset          # 次の優先順位に戻す
/peer-coding:mode status                        # モードと 6 項目すべて、および各出どころ
```

Codex ファミリー: `terra`, `luna`, `sol`, `astra`; Claude ファミリー: `sonnet`, `opus`, `haiku`, `fable`; effort: `low`, `medium`, `high`, `xhigh`, `max`。`/config` はこれらだけを提供し、コマンドは一覧にないファミリーも注記付きで受け付けます。上位の値が今設定した値を覆う場合、コマンドはその上位を示します。1 セッションだけに渡された設定（`--settings`、管理設定）は読みません。1.2.0 より前の Codex ワーカーの既定値は `luna` で、`/peer-coding:mode codex-worker luna --global` で維持できます。

以下は環境変数でのみ設定します:

| 変数 | 既定値 |
|---|---|
| `CXC_FINAL_MODEL` | `astra` |
| `CXC_MAX_CYCLES` | `3` |
| `CXC_PARALLEL` | `3` |

モデル設定はファミリーを指定し、インストール済み CLI が提供するそのファミリーの最新バージョンを常に実行します。`gpt-6-sol` のようなバージョン指定も最新に引き上げ、最新を特定できない場合は理由を示してレーンを停止します。

CXC = **C**laude **×** **C**odex — シェルで設定する変数の接頭辞です。

## プラットフォーム

スクリプトは POSIX ツールだけを使う bash です（macOS の bash 3.2 と BSD ユーティリティに対応）。

| プラットフォーム | 状況 |
|---|---|
| Linux | 対応 |
| macOS | 対応 |
| Windows + WSL | 対応（Linux と同じ動作） |
| Windows + Git Bash | 動作する見込み。パスは Git Bash に従う（`~` = `/c/Users/<you>`） |
| Windows PowerShell / cmd のみ | 非対応 — Git for Windows をインストールするか WSL を使ってください |

Windows ではスクリプトの改行を LF に保つ必要があります。プラグインの `.gitattributes` がこれを強制します。git を使わずにファイルをコピーした場合は、改行を LF に変換してください。

## ライセンス

MIT。[LICENSE](../../LICENSE) を参照してください。
