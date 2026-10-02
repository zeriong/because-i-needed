<p align="center"><strong>free-hands</strong></p>

<p align="center"><strong>有限の目標を渡すと、エージェントが質問や中断をせずチェックリストを最後まで進めます。</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.1.0-blue" alt="バージョン"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="ライセンス: MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code プラグイン"></a></p>

<p align="center"><a href="#開始">開始</a> &bull; <a href="#目標ファイル">目標ファイル</a> &bull; <a href="#質問しない">質問しない</a> &bull; <a href="#フック">フック</a> &bull; <a href="#パネル">パネル</a> &bull; <a href="#積み上げpr">積み上げ PR</a> &bull; <a href="#制限と状態">制限と状態</a> &bull; <a href="#codex">Codex</a> &bull; <a href="#必要条件">必要条件</a> &bull; <a href="#インストール">インストール</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub><a href="../../README.ja.md">because-i-needed</a> の一部</sub></p>

---

free-hands は目標を有限で確認可能なチェックリストにし、未完了項目をユーザーに尋ねたり停止したりせずに進めます。本来ユーザーが決める場面では、読み取り専用の5役パネルが助言し、メインエージェントが証拠に基づいて決定し、異論と元に戻す方法を記録します。

## 開始

- Claude Code: `/free-hands:run <目標>`
- Codex: `$free-hands:run <目標>`
- プロンプトに **free-hands** と書いて開始することもできます。最初の応答でユーザーの言語による開始質問を一度だけ行います。はいと答えるとその目標でスキルを開始し、いいえと答えると可能な方向を提案してターンを終えます。名称の説明や引用は開始要求ではありません。目標が有効な間にもう一度「free-hands」と伝えると、確認なしで進め方を修正します。

## 目標ファイル

リポジトリのルートに `.free-hands/goal.md` と `.free-hands/.gitignore`（`*`）を置き、`.git` に触れずにフォルダーを Git の対象外にします。目標、有限のチェックリスト、決定、再開時のメモを記録します。

```markdown
status: active
max_iterations: 40
iterations: 0
## Goal
<一文の目標>
## Checklist
- [ ] <完了を確認できる有限の項目>
## Decisions
## Resume
<次のセッションに必要な情報>
```

マークは `- [ ]` 未完了、`- [x]` 完了、`- [-] … — needs the user` ハードリミットや別の障害で進められない項目です。状態は `active`、`done`、`waiting`、`paused` です。未完了 `[ ]` だけが質問・停止ガードを有効にし、未完了項目が残っている間は `done` や `waiting` でも実行は終了しません。すべて完了すると `done`、ユーザー対応待ちだけが残ると `waiting` を記録します。`max_iterations` の40回に達すると、復元メモが `paused` に設定して未完了項目を報告し停止するよう指示します。質問は再び可能です。

## 質問しない

目標が有効な間、スキルはユーザーに質問しません。プロジェクトや他のスキルの質問ルール、claude-x-codex などのワークフローの承認ゲートもこの規則で上書きされます。エージェントは確認を求めずにブランチをプッシュし、PR を作成します。失敗したテスト、ゲート、フック、レビューは修正するか、ユーザー対応が必要として `- [-]` に記録し、合格扱いにしません。他プラグインのフックは引き続き動作します。

## フック

フックごとに条件が異なります。

- `## Checklist` の下にあり、かつコードブロック外にある `- [ ]` 行だけを未完了項目として数えます。
- 質問・停止ガードは目標に未完了 `[ ]` があり、`max_iterations` 未満で、状態が `active` または未完了項目が残る `done`/`waiting` の場合に動作します。質問ガードは質問ツールを拒否します。上限では質問が可能です。Stop フックは停止をブロックする前にカウンターをディスクへ記録し、最大40回継続します。
- 復元メモ（`UserPromptSubmit`、圧縮後を含む `SessionStart`）は目標が `active`（未完了項目がなくても）または未完了項目が残る `done`/`waiting` の間に出力されます。
- 有効で正しい目標がなく、プロンプトに「free-hands」がある場合は開始メモを出力します。バックグラウンドタスクの通知はプロンプトとして扱いません。プロンプト内で引用された通知は無視し、プロンプトの残りを読み取ります。

不正なフック入力では何も起きません。不正または読み取れない目標ファイルでは復元・質問・停止動作は有効になりません。プロンプトに「free-hands」があれば、プロンプトフックは有効な目標がない場合の開始ルートを使い、開始質問を出すことがあります。書き込み失敗やロック待ちタイムアウトでも何も起きず、ツール呼び出しや停止が進みます。

## パネル

5役はラウンド1で同じブリーフを独立して検討し、メインエージェントは集計前にディスパッチしたすべての役の応答を待ちます。ラウンド2はラウンド1で意見が割れた場合だけ行います。不足または不正な応答は一度だけ再試行し、有効な応答が3件未満なら **panel degraded** と記録してメインエージェントが単独で決めます。最新モデルを確認できない役は代替モデルを使わずスキップし、不足として数えます。Claude Code で `ANTHROPIC_DEFAULT_<FAMILY>_MODEL` のリダイレクトがある場合、その family の役は利用できません。メインエージェントは重要な主張を確認し、投票ではなく証拠で決定します。リポジトリや実行で確認した事実、出典のある証拠、推論の順で重視し、各意見、異論、決定、元に戻す方法を記録します。

| 役割 | 観点 | Claude のモデル系列 |
|---|---|---|
| `quick-thinker` | 素早い第一原理の判断 | `sonnet` |
| `deep-thinker` | 結果、端のケース、二次的影響 | `opus` |
| `evidence-hunter` | ドキュメントとソースの証拠 | `sonnet` |
| `trend-tracker` | 日付付きの最近の変化 | `sonnet` |
| `devils-advocate` | 有力案への最も強い反論 | `opus` |

各役は系列内で利用可能な最新モデルを使います。Claude Code の Agent ツールは実行されたモデル ID を表示しないため、resolver が返した family alias と「id not visible」を記録します。Codex では子プロセスの実行が報告したモデルを記録します。

## 積み上げPR

最初の PR はリポジトリの integration ブランチを対象にします。すべての PR のタイトル末尾に実行内で増える番号 ` (n)` を付け、後続の PR は直前のブランチを基にします。ユーザーが積み上げ順に PR をマージします。先行 PR のマージ後、必要ならエージェントが次の PR の base を integration ブランチに変更し、後続の各ブランチに `origin/<integration>` をマージしてプッシュします。詰まった batch を飛ばさないため、積み上げ順がマージ順です。

## 制限と状態

パネルが単独エージェントより良い判断をするという主張は、**測定されていない仮説**です。Claude Code 2.1.286–2.1.287 および Codex 0.159.3–0.160.0 で各ケース1回ずつ測定した内容（[z-lab `free-hands-lab`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab)：`run-0.1.0`、`run-0.1.0-r2`）：

- フックはセッション開始時、各プロンプトで、圧縮後に復元メモを注入します（F01、F04、G02）。Claude Code では、未完了項目がある間に停止ガードが停止をブロックし、カウンターをディスクに記録します（F02）。Codex はフックイベントを出力しないため、ブロックは1回だけ確認されています（F04）。
- 開始質問、「はい」と「いいえ」の回答、説明のための言及は、両ホストで説明どおりに動作します。ただし、韓国語のプロンプトに対して Codex は英語で質問し、「いいえ」には方向を示さず簡単な相づちで応答しました（F06）。
- 停止要求は `paused` で終了し、ユーザー対応が必要な項目は `[-]` と `waiting` で終了します（G01、G03）。
- `FREE_HANDS_ROLE` で起動したパネルの子プロセスは親の目標に影響しません（F05）。
- 5役は両ホストで各系列の最新モデルを実行して有効な応答を返し、Claude のメインエージェントは5役すべてを待ちます（F08、F09、G04）。

未測定：`AskUserQuestion` の拒否（headless Claude Code にはこのツールがない）と Codex の `request_user_input` の拒否（エージェントが呼び出さなかった）、実行時の `max_iterations` での解除とカウンター書き込み失敗（単体テストのみ）、ラウンド2（パネル全員が合意）、役割による書き込み試行の阻止（試行なし）、対話型 `/hooks` の信頼、積み上げ PR。4回の実行でエージェント自身が `iterations` を書き換えたため（F04、G03）、エージェントがカウンターを変更しない間だけ上限が機能します。

以下はスキルと復元メモがエージェントに伝えるルールです。該当コマンドをブロックするフックはありません。

- PR をマージしたり、デフォルトブランチに何かをマージしたりしません。
- リポジトリ外のファイル、データ、リモートブランチ、データベースを取り消せない形で削除しません。
- デプロイ、公開、外部への送信（リリース、パッケージ公開、メール、メッセージなど）をしません。

該当項目は理由を付けて `- [-]` と記し、他の作業を続けます。すでにプッシュしたブランチへの force-push は一行で通知した後に可能です。

一時停止するには **「pause」**、「**stop**」、または **「일시정지」** と入力します。目標を `paused` と記録します。コマンドを再実行すると再開します。

由来: プロジェクトローカルのスキルを移植しました。

## Codex

自動動作に頼る前に `/hooks` でプラグインのフックを信頼してください。質問フックの matcher には `request_user_input` が含まれますが、拒否はまだ観測されていません。Codex のデフォルトモードには質問ツールがないため、作業継続のルールは Stop フックが担います。フックを信頼または有効化していない場合も、スキルの規則に従いますがフックの効果は無効な可能性があります。

パネルは役割ごとに `codex exec -s read-only` の子プロセスを1つ実行します（native subagent はモデルを指定できますが読み取り専用制御がないため使用しません — F10）。子プロセスは役割にかかわらずウェブ検索でき、`evidence-hunter` と `trend-tracker` には `--search` を追加します（F09）。子プロセスにはネットワークが必要です。サンドボックス内のメインエージェントでは、`panel.py run` を承認済みの権限昇格でサンドボックス外で実行するか、セッションでネットワークを許可する必要があります。そうしないとすべての子プロセスが失敗し、実行はメインエージェントが単独で決定して **panel degraded** と記録し、続行します（G06）。

## 必要条件

- フック用の `python3`（`PATH` 上に必要）。
- リポジトリルートを見つけるための `git`。
- 積み上げ PR の処理に `gh`。
- Codex パネル経路に Codex CLI（`codex`）。

## インストール

先にマーケットプレイスを追加し、その後プラグインをインストールします。

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install free-hands@because-i-needed
```

Codex は[マーケットプレイスの説明](../../README.ja.md#codex)を参照してください。

## ライセンス

MIT。[LICENSE](../../LICENSE) を参照してください。
