<p align="center"><strong>budget</strong></p>

<p align="center"><strong>Claude Code</strong> と <strong>Codex CLI</strong> でのみ動作します。</p>

<p align="center"><strong>使用量ウィンドウの割合を決めておくと、そこに達した時点で実行中のすべてのセッションが止まり、続けるかどうかを尋ねます。</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.1.0-blue" alt="バージョン"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="ライセンス: MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code プラグイン"></a></p>

<p align="center"><a href="#開始">開始</a> &bull; <a href="#仕組み">仕組み</a> &bull; <a href="#設定と状態">設定と状態</a> &bull; <a href="#制限と状態">制限と状態</a> &bull; <a href="#必要条件">必要条件</a> &bull; <a href="#インストール">インストール</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub><a href="../../README.ja.md">because-i-needed</a> の一部</sub></p>

---

budget はアカウントが報告する使用量ウィンドウを監視し、あなたが選んだ割合ですべてのセッションを止めます。ウィンドウがその割合に達すると、実行中の各セッションの次のツール呼び出し（サブエージェントの呼び出しを含む）は、1つの質問への回答を待ちます。**"지정한 n%에 도달했습니다, 작업을 이어서 진행하시겠어요?"**（設定した n% に達しました。作業を続けますか？）。続けるなら 예、止めるなら 아니오 と答えます。設定した割合は [dashboard](../dashboard) プラグインに表示されます。

## 開始

- Claude Code: `/budget:mode 80` · Codex: `$budget:mode 80` — 80% で止めて尋ねます。
- `/budget:mode off` でオフにし、`/budget:mode status` で割合と最後に測定したウィンドウを表示します。
- 割合はユーザーアカウントに1つだけの設定で、Claude Code と Codex で共有されます。

## 仕組み

**Claude Code** は**5時間**ウィンドウを測定します。Claude Code はターンごとと、値が1ポイント動くたびにプラグインへ報告します。それが割合以上のとき、budget は次のツール呼び出しを保留し、Claude Code 自身の質問ダイアログで尋ねます（チップ `budget`、選択肢は 예 と 아니오）。

- 예: 呼び出しが進み、そのセッションはウィンドウがリセットされるまで再び尋ねられません。
- 아니오: 呼び出しは拒否され、ターンが止まります。
- 1つの質問が、開いている間に届いたすべての呼び出しに答えるため、並列のサブエージェントへの質問は1回です。
- 回答する人がいない実行（`claude -p`）と、閉じられたダイアログは 아니오 として扱います。

**Codex** は **7日**ウィンドウを測定します。Codex が報告するのはこれだけです。budget はアカウントの最近のセッションログ（`~/.codex/sessions`）にある最新の値を読むため、新しいセッションは最初の呼び出しから保留されます。Codex にはプラグインが開けるダイアログがないので、budget は呼び出しを拒否し、同じ質問でターンを終えるようエージェントに指示します。続けるには 예（`네`、`yes`、`y`、`계속`、`continue` も可）と答えます。それ以外の回答ではセッションは止まったままです。先に `/hooks` でプラグインのフックを信頼してください。

**[free-hands](../free-hands) との併用:** free-hands は目標の実行中に質問しませんが、この質問だけは例外です。budget の質問がセッションで開いている間、free-hands 0.4.0 はそれを通し、ターンを続けさせません。

## 設定と状態

- `~/.config/because-i-needed/budget.json`（`$XDG_CONFIG_HOME` が設定されていればその下）: `{"percent": 80}`。`/budget:mode` が書き込み、`off` で削除されます。
- `~/.config/because-i-needed/budget/`: セッションの質問が開いている間は `pending/<session>.json`、ウィンドウに対して 예 と答えた後は `acks/<session>.json`、ホストが最後に報告したウィンドウを記した `usage.json`（dashboard が表示します）。
- 新しいウィンドウでは再び尋ねます。リセット時刻が数秒ずれても同じウィンドウとみなします。Codex が報告するリセット時刻は、読み取りのたびに1秒ずれるためです。

## 制限と状態

Claude Code 2.1.299 と Codex 0.162.1 で、ケースごとに1回ずつ測定しました（[z-lab `budget-lab`](https://github.com/zeriong/z-lab/tree/main/budget-lab): `run-0.1.0`、`run-0.1.0-r2`。その土台となる事実は `codex-gate-0.1.0`、`codex-gate-0.1.0-r2` と z-lab `plugin-platform-lab/mod-interactive-2.1.299` にあります）。

- Claude Code はダイアログを表示しました。예 で呼び出しが実行され、아니오 でターンが止まりました（「Interrupted」）。割合を下回っているときは何も起きませんでした。並列の2つのサブエージェントへの質問は1回でした。예 の後、以降の呼び出しは再度の質問なしで実行されました（R01–R05、R10）。
- Codex は質問でターンを終え、何も実行しませんでした。예 でセッションのロックが解除され、以降の呼び出しは再度の質問なしで実行されました。割合を下回っているときは何も起きませんでした（R06、R09、R11）。
- free-hands が目標を実行している状態でも、Claude Code では質問が表示されました。Codex では、ゲートされたターンがすぐに終了しました。free-hands 0.3.0 では停止ガードがさらに3回続行させていました（R04、R07、R12。codex-gate B03）。

未測定: すでに実行中のターンの途中で割合を超える場合（Claude Code の次の報告の前に、ターンが割合を超えることがあります）、複数の対話セッションの同時実行、割合に達した `claude -p` の実行、Codex の5時間ウィンドウ（測定したアカウントでは報告されませんでした）、バイパスではなく `/hooks` で信頼した Codex フック。

budget が使う Claude Code のプラグインフックモジュール API は早期アクセスとされており、リリース間で変更される可能性があります。

## 必要条件

- プラグインフックモジュールに対応した Claude Code（2.1.299 で測定）、または Codex CLI（0.162.1 で測定）。
- Codex フックと `/budget:mode` のための、`PATH` 上の `python3`。

## インストール

先にマーケットプレイスを追加し、その後プラグインをインストールします。

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install budget@because-i-needed
```

Codex は[マーケットプレイスの説明](../../README.ja.md#codex)を参照してください。

## ライセンス

MIT。[LICENSE](../../LICENSE) を参照してください。
