<p align="center">
  <strong>claude-x-codex</strong>
</p>

<p align="center">
  <strong>Claude × Codex のピアオーケストレーション — 2 つのエージェントが同僚として、互いの計画・実装・レビューを担います。</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.1.0-blue" alt="Version"></a>
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

**C**laude **×** **C**odex のピアオーケストレーションです。土台の異なる 2 つのエージェントは異なる形で間違えるため、それぞれが相手の作業をレビューします — メインエージェント自身の計画も例外ではありません。意見が分かれたときに判定するのは、役割ではなくテストです。

claude-x-codex は非公式のコミュニティプラグインです。Anthropic や OpenAI が作成・保証・サポートしているものではありません。

## コマンド

| コマンド | 内容 |
|---|---|
| `/claude-x-codex:run` | タスクをオーケストレーションします。メインエージェントが計画してすべてのゲートを判断し、作業を `claude-fast` / `codex-bulk` / `main` のレーンに振り分け、各ベンダーに相手ベンダーの作業をレビューさせます |
| `/claude-x-codex:mode on\|off\|status\|clear [--global]` | 自動オーケストレーションをオン / オフする 1 行のスイッチです。ユーザー専用で、モデルは切り替えられません |
| `/claude-x-codex:audit` | 両ベンダーが同じプロジェクトの文脈から始められるかを読み取り専用で点検します。修正案を提案するだけで、何も変更しません |

`on`・`off` はこのプロジェクトのフラグ（`.claude-x-codex/mode`、git から除外）を書き込み、`--global` はすべてのプロジェクトに適用される既定値（`~/.config/claude-x-codex/mode`）を書き込みます。`clear` はプロジェクトのフラグを削除し、`CXC_MODE=on|off` は 1 つのシェルで両方より優先されます。モードがオフのとき、`run` は依頼されたときだけ開始します。

## インストール

### Claude Code プラグインマーケットプレイスから

1. Claude Code で `/plugin` を実行します。
2. Marketplaces → Add Marketplace。
3. URL を入力します: `https://github.com/zeriong/because-i-needed.git`（またはこのリポジトリのローカルパス）。
4. `claude-x-codex` をインストールします。

### または CLI から

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git   # またはローカルパス
claude plugin install claude-x-codex@bin
```

### または `~/.claude/settings.json` に直接記述

```json
{
  "extraKnownMarketplaces": {
    "bin": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": { "claude-x-codex@bin": true }
}
```

- **注意:** インストールすると `UserPromptSubmit` フックが登録されます。すべてのプロンプトで実行されますが、モードがオフの間は何も出力しません。オンのときは、実装作業を `run` に回すよう指示する 4 行のメモ（プロンプトごとに入力約 100 トークン）を追加します。

## 動作要件

- **Claude Code**（またはメインエージェントとしての Codex）、**git** リポジトリ、bash 3.2+。
- **任意 — Codex CLI**（`codex`）。ない場合、`run` は single-vendor モードに切り替わり、すべてのレビューを同じベンダーの別のレビュアーインスタンスに任せ、そのことを伝えます。
- **任意 — Orca**（オーケストレーションを有効化）。あればワーカーが作業中に質問でき、ゲートがユーザーの判断を待ちます。なければワーカーはサブエージェントや CLI 呼び出しとして一方向に実行されます。
- 監査のフック表には `python3` が、Codex がメインエージェントとして Claude レビュアーを動かすときは `jq` が必要です。
- Claude Code 2.1.283、Codex CLI 0.157.1、Orca 1.4.215 で確認しています。

## 仕組み

- **レーン** — ワーカーは effort `high` で動きます。`claude-fast`（Claude Sonnet: UI、インタラクション、コードのセンス、Claude 側のツール）、`codex-bulk`（Codex `gpt-6-luna`: 既存の契約に対するテスト、型、機械的なマイグレーションなど、結果が完全に決まっている作業）、`main`（メインエージェント: 密結合な作業や、仕様がまだ固まっていない作業）。
- **クロスベンダーレビュー** — レビュアーは常に作成者と別のベンダーで、メインエージェント自身の計画や振り分けの判断も相手ベンダーがレビューします。Claude は Opus、Codex は `gpt-6-sol` でレビューし、どちらも effort `xhigh`（両 CLI で `max` のすぐ下の段階）です。認証・決済・データ移行などの高リスクな段階でも、最上位モデル（`gpt-6-astra` または `max` の Opus）のレビューを追加する前に必ずユーザーに確認し、自分からは引き上げません。レビュアーは読み取り専用で動き、両方の CLI がスキーマで強制する JSON を返します。
- **反論は 1 回** — 却下された blocking・major の指摘は、理由とともに一度だけレビュアーへ戻ります。レビュアーは受け入れるか、新しい証拠で反論します。それでも解決しなければ、両者の主張とともに DISPUTED としてユーザーに上がります。
- **証拠が判定する** — 意見が分かれたら、テスト・再現・トレースのどれかを持つ側が勝ちます。証拠がなければユーザーが決めます。
- **コンテキストブリッジ** — 監査は、2 つのベンダーが別々の指示ファイルを読んでいる場所、片方のベンダーにしか効かないフック、ワーカーの worktree に欠けるコミットされていない文脈を見つけます。`run` が行う Codex の呼び出しは Codex のフォールバック設定で `CLAUDE.md` を読むので、リポジトリの変更は不要です。対話型の Codex セッション（Orca のワーカー、またはメインエージェントとしての Codex）では、同じ設定がユーザーの Codex 設定に必要です。ユーザーの設定やリポジトリを変える修正は、計画の承認時に提案します。
- **ディスク上の状態** — `.claude-x-codex/`（git から除外）に計画・判断・レビューが残るため、実行はコンパクションを経ても再開できます。

[plan-smith](../plan-smith) と一緒にインストールすると、計画ステップに `/plan-smith:forge` が使われます — `run` は専用の計画スキルがあれば計画をそれに任せます。

## 設定

`run` は以下を環境変数から読み、なければ既定値を使います:

| 変数 | 既定値 |
|---|---|
| `CXC_WORKER_MODEL` | `gpt-6-luna` |
| `CXC_REVIEW_MODEL` | `gpt-6-sol` |
| `CXC_FINAL_MODEL` | `gpt-6-astra` |
| `CXC_CLAUDE_WORKER` | `sonnet` |
| `CXC_CLAUDE_REVIEWER` | `opus` |
| `CXC_REVIEW_EFFORT` | `xhigh` |
| `CXC_WORKER_EFFORT` | `high` |
| `CXC_MAX_CYCLES` | `3` |
| `CXC_PARALLEL` | `3` |

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
