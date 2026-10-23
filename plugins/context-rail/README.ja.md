<p align="center"><strong>context-rail</strong></p>

<p align="center"><strong>Claude Code</strong> と <strong>Codex CLI</strong> でのみ動作します。測定は Claude Code で行いました。</p>

<p align="center"><strong>記録された決定は毎ターンではなく、エージェントがその決定の対象ファイルを開いた瞬間に届きます。</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.2.0-blue" alt="Version"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a></p>

<p align="center"><a href="#開始">開始</a> &bull; <a href="#書き込むもの">書き込むもの</a> &bull; <a href="#記録">記録</a> &bull; <a href="#到着フック">到着フック</a> &bull; <a href="#決定を変える">決定を変える</a> &bull; <a href="#測定したこと">測定したこと</a> &bull; <a href="#codex">Codex</a> &bull; <a href="#必要条件">必要条件</a> &bull; <a href="#インストール">インストール</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub><a href="../../README.ja.md">because-i-needed</a> の一部</sub></p>

---

`CLAUDE.md` と `AGENTS.md` は毎ターン読み込まれます。そこに書いた決定はすべて毎ターンのコストになり、ほかの内容に埋もれがちです。context-rail はファイルごとの決定を、その決定が対象とするコードの隣へ移します。さらに、エージェントがそのファイルを読む・編集するときにその決定をコンテキストへ入れるフックを入れます。常に読み込まれるファイルは縮むだけです。

## 開始

- Claude Code: `/context-rail:build` — 現在のリポジトリに rail を設定します。
- Codex: `$context-rail:build`。
- `/context-rail:audit`(Codex: `$context-rail:audit`)は既存の rail を点検するだけで、何も変更しません。

`build` は指示ファイルを読み、項目ごとに番号を付けて表を一つ示します。表は次のように分かれています。

- 残すもの
- 決定記録にするもの
- パス単位のルールにするもの
- 提案だけするもの(自動化、個人設定、ツールがすでに強制しているルール)

回答するまで何も書き込みません。個人の項目を代わりに移すことはありません。

## 書き込むもの

すべてプロジェクトファイルで、リポジトリをクローンする全員と共有されます。

| ファイル | 内容 |
|---|---|
| `<dir>/PRECEDENT.md` | そのディレクトリのファイルの決定記録 |
| `.claude/rules/<topic>.md` | パスの集合に適用するルール(`paths:` frontmatter 付き) |
| `.claude/hooks/precedent-context.py` | 到着フック |
| `.claude/settings.json` | PostToolUse(Read・Edit・Write・MultiEdit・Bash)と PostToolUseFailure(Bash)にフックを接続。ほかの設定は残します |
| `.claude/context-rail.json` | フックが対象とするソース拡張子 |

`CLAUDE.md` から移した項目はそこから削除し、ポインター行は追加しません。`build` は指示ファイルの大きさを前後で文字数とバイト数の両方で測り、どちらかが増えたら失敗とします。

## 記録

```markdown
## tab-keys.mjs

### §stable-tab-keys — closing a tab never renumbers the others
- Since: 2026-09-02
- Decision: a key is assigned once and is never reused or shifted.
- Forbidden: renumbering the remaining keys after a close.
- Reason: shifting keys remounts the tabs to the right and drops their form input.
- Evidence: `tab-keys.test.mjs`
```

ファイルは、自分のディレクトリかその上にある最も近い `PRECEDENT.md` の対象になります。`## ` 見出しには一つ以上のファイル名を書きます(`a.ts · b.ts`)。名前が実在するファイルを指す場合は、そのファイルにだけ付きます。完全な形式は [`skills/build/references/record-format.md`](skills/build/references/record-format.md) にあります。

## 到着フック

エージェントが対象ファイルを読む・編集すると、フックがそのファイルの節をコンテキストに入れ、決定の変更についての短い段落を続けます。読み込みには Read ツールのほか、シェルの `cat`・`sed`・`grep` なども含みます。

- ファイルごとにセッション・エージェント単位で一度だけ発火するので、サブエージェントも記録を受け取ります。
- 失敗したシェルの読み込みは PostToolUseFailure が拾います。
- 出力は 10,000 文字未満に保ちます。
  - 6,000 文字以下の節はそのまま入れ、長いものは見出しと決定の行に圧縮します。
  - 10,000 文字を超えると Claude Code はプレビューしか表示しないため、末尾の段落が切れてしまいます。
- git が無視するファイルには何も渡しません。
- 内部エラーは黙って終了し、エージェントを止めません。

## 決定を変える

各節の後の段落は、決定はユーザーの確認によってのみ変わると伝えます。

- 記録された決定を名指しして覆すよう指示した場合、エージェントは変更を行い、決定ブロックをその場で書き直して、ユーザーが覆したことを記します。例:「`src/tabs/PRECEDENT.md` §stable-tab-keys がこれを禁じているが、覆す」。
- それ以外の、決定と衝突する依頼は、どれほど強く言われても、エージェントが編集の前に止まります。決定と衝突点を示して確認を求め、上流の変更、新しい測定、報告された不具合、異なる軸のどれかが当てはまるかにも触れます。
- 別のエージェントから任された作業(サブエージェントや peer-coding のようなワーカー)なら、その依頼は、ユーザーが決定を名指しして覆すよう言ったと伝える場合にだけ確認として扱われます。「それでも進めて」や「新しい決定が記録を置き換える」という依頼は確認ではなく、エージェントは止まって依頼元のエージェントに報告し、ユーザーに確認してもらいます。

## 測定したこと

測定はすべて [z-lab `precedent-lab/`](https://github.com/zeriong/z-lab/tree/main/precedent-lab) にあります。条件は Claude Code 2.1.296–2.1.309 と Codex 0.163.0、headless で、行にほかのエージェントが書かれていなければ Opus、effort `xhigh` です。

| 主張 | 結果 | 実験 |
|---|---|---|
| ポインターではなく節の本文を入れると、禁止の行が最初の編集の前にコンテキストに入る | 罠のラン 3/15 → 44/45 | `real-env-rail-2.1.296` |
| 段落は記録を名指ししない衝突依頼を止める | 禁止を破った数: 段落なし 11/12 → 段落あり 0/12 | `stop-en-r2-2.1.306` |
| …明示的な上書きは通す | 12/12 が実行し、記録をその場で書き直した | `stop-en-r2-2.1.306` |
| …衝突のない編集は止めない | 0/15 停止 | `stop-en-r2-2.1.306` |
| `build` は項目を正しい場所へ移す | 5/5 ラン: 14/14 項目、検査すべて通過、`CLAUDE.md` 1,906 → 540 文字 | `build-fidelity-0.1.0` |
| `audit` は何も変更せずに点検し、仕込んだ不具合を指摘する | 4/4 ラン: 変更 0、検査をすべて実行、仕込んだ不具合 3/3 を指摘、誤検出 0 | `audit-canary-0.1.0` |
| `build` で正規化したプロジェクトは、同じ決定を `CLAUDE.md` に置いた場合より決定を守る | 権威的な依頼での禁止破り: 常駐 12/12 → 正規化 0/12、誤停止は両方 0/15 | `fresh-project-0.1.0` |
| パス単位のルールは、一致するファイルに初めて触れたときに読み込まれる | Read・シェル読み込み・Write のいずれでもルールが付いた | `platform-r2-2.1.308-0.163.0` |
| 別のエージェントの依頼は、ユーザーの名指しを伝えるときだけ確認になる | メインが書いた「それでも進めて」の依頼で、0.1.0 の段落の Sonnet サブエージェントが 6/9 破った。同じ文を固定した依頼では 0.1.0 の段落 12/12 → 0.2.0 の段落 0/12 | `leaf-2.1.309`、`leaf-r2-2.1.309` |
| 作業を任されたエージェントもルールを守る | Opus・Sonnet サブエージェント、Sonnet `claude -p`・Codex `gpt-6-luna` ワーカーのすべての経路で禁止破り 0/12、上書きの実行 12/12、停止 0/15 | `leaf-r2-2.1.309` |

罠と build の結果は合成 fixture と非公開リポジトリ一つから得たもので、セルあたり 12–15 ランです。

**測定していないこと**
- ほかのモデル・effort、対話型セッション
- ほかの言語で書いた記録とこの段落の組み合わせ
- 大きなリポジトリ、Orca の双方向ワーカー
- Codex で `build`・`audit` を動かすこと

## Codex

Codex でも同じスキルが同じフックをインストールします(`$context-rail:build`、`install-hooks.py --host codex` → `.codex/hooks/`、`.codex/hooks.json`)。

- **プラットフォーム**(Codex 0.163.0、実験用の probe フック)
  - PostToolUse の出力がモデルに届きます。
  - シェルの読み込みは `Bash`、編集は `apply_patch` として届きます。
  - 失敗したシェル呼び出しでも PostToolUse が発火します。
- **Codex でのこのプラグインのフック**(`install-hooks.py --host codex` でインストール): Codex ワーカー(`gpt-6-luna`、effort high、peer-coding の依頼)はルールを守りました。禁止破り 0/12、上書きの実行 12/12、停止 0/15(`leaf-r2-2.1.309`)。
- **測定していないこと**: Codex で `build`・`audit` を動かすこと、入れ子の `AGENTS.md` がいつ読み込まれるか、`apply_patch` 側の配信。

頼る前に `/hooks` でフックを信頼してください。

## 必要条件

- `PATH` 上の `python3`(3.9 以上)。
- `git` — フックがリポジトリのルートを見つけ、無視されたファイルを飛ばすのに使います。

## インストール

まずマーケットプレイスを追加し、次にプラグインをインストールします。

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install context-rail@because-i-needed
```

Codex は [マーケットプレイスの手順](../../README.ja.md#codex) に従ってください。

## ライセンス

MIT。[LICENSE](../../LICENSE) を参照してください。
