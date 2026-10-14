<p align="center"><strong>dashboard</strong></p>

<p align="center"><strong>Claude Code</strong> と <strong>Codex CLI</strong> でのみ動作します。</p>

<p align="center"><strong>オンにしている because-i-needed のモードと、各値の出どころを、1行で確認できます。</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.1.0-blue" alt="バージョン"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="ライセンス: MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code プラグイン"></a></p>

<p align="center"><a href="#表示内容">表示内容</a> &bull; <a href="#claude-code">Claude Code</a> &bull; <a href="#codex">Codex</a> &bull; <a href="#プラグインの参加方法">プラグインの参加方法</a> &bull; <a href="#制限と状態">制限と状態</a> &bull; <a href="#インストール">インストール</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub><a href="../../README.ja.md">because-i-needed</a> の一部</sub></p>

---

because-i-needed のプラグインには、プロジェクトまたはユーザーのレベルで設定したままになるスイッチがあります — peer-coding のオーケストレーションモード、free-hands の目標、budget の割合などです。dashboard はそのすべてを表示するので、知らないうちにスイッチがオンになっていることはありません。

## 表示内容

```
because-i-needed │ budget 80% · 5h now 20% │ free-hands active 0/40 · 1 open (project) · owner lab-sess │ peer-coding on (project)
```

- 有効な because-i-needed プラグインが宣言したスイッチごとに1項目: その値、決めているレベルが該当する場合は `(project)` または `(env)`、そして最後に測定した使用量ウィンドウや目標の所有セッションなどの詳細。
- 有効なプラグインがスイッチを宣言していなければ、何も表示されません。
- `/dashboard:audit`（Claude Code）または `$dashboard:audit`（Codex）は、同じ行に加えて、各スイッチについてプロジェクトレベルとグローバルレベルで設定された値を表示します。何も変更しません。

## Claude Code

行はプロンプトの上に表示されます。セッション開始時、ターンごと、使用量ウィンドウが動いたときに更新されます。dashboard は、Claude Code がインストールして有効にしている because-i-needed プラグインを見つけます。

## Codex

Codex にはプラグインが描画できる場所がないため、Codex では dashboard は `$dashboard:audit` コマンドになります。使用量ウィンドウを常に見えるようにするには、`~/.codex/config.toml`（または `/statusline`）で Codex 自身のステータスライン項目をオンにします。

```toml
[tui]
status_line = ["model-with-reasoning", "weekly-limit"]
```

表示されるのは7日ウィンドウの**残り**（例: `weekly 28% left`）で、使用済みの量ではありません。未知の項目 ID は警告とともに無視されます。

## プラグインの参加方法

プラグインは、ルートの `dashboard.json` でスイッチを宣言します。`mode` スキルを持つ because-i-needed プラグインはすべて宣言が必須で、それ以外のプラグインも宣言できます（リポジトリの Rule 11）。

```json
{ "entries": [ { "label": "peer-coding", "status": ["bash", "scripts/mode.sh", "status", "--json"] } ] }
```

`status` コマンドは読み取り専用で、プロジェクトのディレクトリで実行され、JSON オブジェクトを1つ出力します。内容は `value`、`source`（`env`、`project`、`global` または `default`）、`project` と `global`（各レベルの値。なければ `null`）、任意の `detail` です。失敗する、2秒を超える、または別の内容を出力するコマンドは `error` と表示されます。あとから追加されたプラグインは、dashboard のリリースなしで表示されます。

`claude --plugin-dir` でフォルダーから読み込んだプラグインは Claude Code のインストール記録にありません。表示するには、そのフォルダーを `BECAUSE_I_NEEDED_PLUGIN_DIRS`（`PATH` と同じ区切り）に列挙してください。

## 制限と状態

Claude Code 2.1.299 と Codex 0.162.1 で、ケースごとに1回ずつ測定しました（[z-lab `dashboard-lab/run-0.1.0`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab/run-0.1.0)。Codex のステータスラインは [`codex-status-line-0.162.1`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab/codex-status-line-0.162.1)）。

- Claude Code では、上の行に budget、free-hands、peer-coding が表示され、`/dashboard:audit` は各レベルを出力しました。宣言するプラグインがなければ行は表示されませんでした（D01–D03）。
- Codex では、`$dashboard:audit` がインストール済みのプラグインから同じ項目を出力し、budget の項目には7日ウィンドウが表示されました。宣言するプラグインがなければ、その旨を表示しました（D04–D05）。
- Codex の `weekly-limit` 項目は `weekly 28% left` と表示されました（C02）。

未測定: Claude Code のマーケットプレイス経由でインストールしたプラグイン（測定した行は `--plugin-dir` のフォルダーを読み取っており、インストール記録は単体テストのみ）、セッション途中でスイッチが変わったときの行の更新、デスクトップと IDE のサーフェス。

行を描画する Claude Code のプラグインフックモジュール API は早期アクセスとされており、リリース間で変更される可能性があります。

## インストール

先にマーケットプレイスを追加し、その後プラグインをインストールします。

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install dashboard@because-i-needed
```

Codex は[マーケットプレイスの説明](../../README.ja.md#codex)を参照してください。`python3` が `PATH` 上に必要です。

## ライセンス

MIT。[LICENSE](../../LICENSE) を参照してください。
