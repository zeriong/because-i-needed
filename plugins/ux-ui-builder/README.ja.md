<p align="center">
  <strong>ux-ui-builder</strong>
</p>

<p align="center">
  <strong>スタジオが出荷するように Web とモバイルの UI を作ります — 実際のレンダリングで計測し、アートディレクターが批評し、コミット時にゲートで守ります。</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-1.1.0-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a>
</p>

<p align="center">
  <a href="#インストール">インストール</a> &bull;
  <a href="#できること">できること</a> &bull;
  <a href="#ループ">ループ</a> &bull;
  <a href="#モバイル計測バックエンド">モバイルバックエンド</a> &bull;
  <a href="#コミットゲート">コミットゲート</a> &bull;
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

エージェントが想像で UI を実装すると、出来は悪くなります — 見えない overflow、欠けた focus ring、処理されていない empty 状態、ラベルに漏れ出た生の UUID。どれも、実際のレンダリングを見るまでは表に出てきません。

**ux-ui-builder はループから想像を取り除きます**。すべての UI の変更は実際のレンダリングで計測され（Web は chrome-devtools によるブラウザページ、モバイルは実機 / シミュレーター）、アートディレクターエージェントが*計測された*スナップショットをもとに批評し、正確かつエレガントになるまで反復したうえで、ハードゲートがかかります: ステージされた diff そのものに対してアートディレクターが APPROVED を出していない UI は、コミットできません。

## 特長

- **実測のみ、想像はしない** — スキルが同梱の **chrome-devtools MCP** を操作して、実際のレンダリングをキャプチャします: default / hover / focus / loading / empty / error / long-content を mobile / tablet / desktop にわたって、さらに DOM / a11y スナップショット、コンソール + ネットワークのシグナル、Lighthouse 監査も。
- **モバイルにも対応** *（1.1 で追加）* — 2 つ目のスキル `ux-ui-builder-mobile` がアプリのスタック（React Native / Expo / Flutter / ネイティブ iOS / ネイティブ Android / モバイル Web）を検出し、起動済みの実機またはシミュレーターから**実際のピクセル**を返す計測バックエンドを選んで、device × orientation × state のマトリクスをキャプチャします。そのスタックのスクリーンショットを撮れる MCP がない場合は、同梱の **CLI スナップショットハーネス**（`simctl` / `adb`）が代わりに撮影します。
- **アートディレクターによるハードゲート** — `ux-ui-art-director` エージェント（Opus）は、計測されたアーティファクトだけを批評します。モバイルでは `ux-ui-mobile-art-director` が、プラットフォームのイディオム（Apple HIG / Material）に照らして判定します。critical / major の欠陥が 1 つでもあれば → `CHANGES_REQUIRED`。ディレクターは状態を自ら再計測できますが（モバイルのディレクターは MCP が使えるスタックでのみ。CLI ハーネスしか使えないスタックでは、代わりにキャプチャを要求します）、コードは編集できません（レビュアーと実装者の分離）。
- **diff に紐づく承認** — 承認は、ステージされた UI の diff の sha256 に紐づけられます。UI を編集し直すとハッシュが変わるので、ゲートは再びブロックします。「一度承認を得たら編集し続ける」ことは構造的に不可能で、古い承認や偽造された承認はありえません。
- **自律的な反復** — build → measure → critique → fix → re-measure を最大 3 サイクル、ユーザーの追加指示なしで回します。最初のコミットからエレガントなフロントエンドに。（モバイルのループは、計測バックエンドを確認するために、最初に一度だけ止まります。）
- **Zero-config** — ブラウザとモバイルの MCP を自前で同梱し、正確さ + エレガンスの基準も自ら備えているので、何もセットアップされていないプロジェクトでも動きます。ホスト側のプロジェクトがデザインルールを*定義している*場合は、そちらが優先されます。
- **控えめな blast radius** — ゲートが発動するのは本物の UI ファイル形式だけです: Web（`.tsx .jsx .vue .svelte .astro .css .scss .sass .less .html`）とモバイル（`.swift .kt .dart .storyboard .xib`、Android の `res/layout*/**/*.xml`）。素の `.ts`/`.js`/`.java` と、レイアウト以外の `.xml` は対象外なので、バックエンドだけのコミットがブロックされることはありません。

## インストール

### Claude Code プラグインマーケットプレイスから

1. Claude Code で `/plugin` を実行します。
2. Marketplaces → Add Marketplace を選びます。
3. URL を入力します: `https://github.com/zeriong/because-i-needed.git`（またはこのリポジトリのローカルパス）。
4. `ux-ui-builder` をインストールします。

### または CLI から

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git   # またはローカルパス
claude plugin install ux-ui-builder@because-i-needed
```

### または `~/.claude/settings.json` に直接記述

```json
{
  "extraKnownMarketplaces": {
    "because-i-needed": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": { "ux-ui-builder@because-i-needed": true }
}
```

インストールすると、すべてが自動で登録されます: 4 つの MCP サーバー（`chrome-devtools`、`mobile-mcp`、`ios-simulator`、`flutter`）、コミットゲートフック、`ux-ui-art-director` と `ux-ui-mobile-art-director` エージェント、`ux-ui-builder` と `ux-ui-builder-mobile` スキル。

## 動作要件

- **Web**: **Node.js**（同梱の `chrome-devtools-mcp` は `npx` 経由で実行されます）、ローカルの **Chrome**、そして UI を作るプロジェクトの実行可能な**開発サーバー**。
- **モバイル**: スタックに応じたプラットフォーム SDK — Xcode + シミュレーター（iOS、macOS のみ）、Android SDK + エミュレーター、または Flutter SDK — と、起動済みの実機 / シミュレーター上で動作しているアプリ。モバイル MCP（`@mobilenext/mobile-mcp`、`ios-simulator-mcp`、`dart mcp-server`）は、対応するツールがインストールされた環境でのみ起動します。`mobile-snapshot.sh` ハーネスに必要なのは `simctl`/`adb` だけです。
- **git** の work tree と、`shasum`/`sha256sum`（macOS / Linux には標準で入っています）。

## クイックスタート

```
cd your-project
# Claude Code で、そのまま UI を作るだけです。画面を実装・変更するとき:
/ux-ui-builder:ux-ui-builder          # Web
/ux-ui-builder:ux-ui-builder-mobile   # モバイル (RN / Flutter / iOS / Android / モバイル Web)
```

コンポーネント、ページ、画面、フォーム、シート、リスト、レイアウトの作成・修正・再デザイン・スタイリングを頼むと、どちらのスキルも自動的に起動します。

Web スキルが行うこと:

1. ブラウザ MCP と開発サーバーをセルフチェックします（必要ならサーバーを起動）。
2. この機能のためだけのデザイン意図を立てます（テンプレート的なデフォルトではなく）。
3. UI を構築します。
4. state × breakpoint のマトリクス全体で、実際のレンダリングを計測します。
5. 計測結果をアートディレクターに渡して批評を受けます。
6. `APPROVED` になるまで修正と再計測を繰り返します（cap = 3）。
7. コミットのブロックを解除する承認を記録します。

モバイルスキルも同じループを回しますが、ステップ 1 ではまずスタックを検出し、ハーネスの `doctor` を実行して、計測バックエンドの確認を求めます（唯一の対話的な一時停止です）。またステップ 4 では、起動済みのターゲット上で device × orientation × state のマトリクスを計測します。

一致する承認なしに UI をコミットしようとすると、ゲートがブロックし、ループを実行するよう伝えます。

## できること

```
your-project/
└── .ux-ui/
    ├── measure/<feature>/        # スクリーンショット、snapshots.md、signals.md、context.md
    └── approvals/<diff-hash>.json # コミットゲートがチェックする APPROVED アーティファクト
```

プラグイン自体の構成:

```
plugins/ux-ui-builder/
├── .claude-plugin/plugin.json          # マニフェスト + 同梱 MCP (chrome-devtools, mobile-mcp, ios-simulator, flutter)
├── hooks/hooks.json                    # PreToolUse → コミットゲート
├── scripts/
│   ├── ui-commit-gate.sh               # ゲート: hash | approve <feature> [dir] | hook-block (Web + モバイルの形式)
│   └── mobile-snapshot.sh              # CLI スナップショットハーネス: doctor | capture <ios|android> <dir> <label>
├── agents/
│   ├── ux-ui-art-director.md           # Web のアートディレクター (計測 + 批評、Opus)
│   └── ux-ui-mobile-art-director.md    # モバイルのアートディレクター (HIG / Material のイディオム、Opus)
└── skills/
    ├── ux-ui-builder/                  # Web: measure → critique → iterate → gate
    │   ├── SKILL.md
    │   └── references/
    │       ├── design-principles.md    # 正確さ + エレガンスの基準 (自己完結)
    │       ├── measurement-protocol.md # chrome-devtools の厳密なキャプチャ手順
    │       └── review-rubric.md        # verdict の形式 + APPROVED アーティファクトの契約
    └── ux-ui-builder-mobile/           # モバイル: detect → measure → critique → iterate → gate
        ├── SKILL.md
        └── references/
            ├── backend-detection.md          # スタックを検出 + 実ピクセルのバックエンドを選択
            ├── mobile-design-principles.md   # HIG / Material、セーフエリア、タップターゲット、ジェスチャー、キーボード、ダークモード
            ├── mobile-measurement-protocol.md # バックエンドごとのキャプチャ (device × orientation × state)
            └── mobile-review-rubric.md       # verdict の形式 + APPROVED アーティファクトの契約
```

## ループ

| ステップ | 責務 |
|------|------|
| 0 | **Bootstrap** — ブラウザ MCP + 開発サーバーを確認し、feature slug を決めます。*モバイル:* スタックを検出し、`mobile-snapshot.sh doctor` を実行し、バックエンドをあなたと確定し、起動済みのターゲットでアプリが動いていることを確認します |
| 1 | **Plan** — *この* feature のための簡潔なデザイン意図。AI のデフォルトっぽい見た目は避けます（モバイル: プラットフォームのイディオムの範囲内で） |
| 2 | **Build** — 既存のコンポーネント / トークンを再利用して実装 |
| 3 | **Measure** — 実際の state × breakpoint マトリクス + 監査をキャプチャ（モバイル: device × orientation × state）— 必須 |
| 4 | **Critique** — 計測したアーティファクトに対して `ux-ui-art-director`（Web）または `ux-ui-mobile-art-director`（モバイル）を起動（ハードゲート） |
| 5 | **Iterate** — 修正を適用してステップ 3 に戻り、再レビュー（cap = 3） |
| 6 | **Record approval** — APPROVED のときだけ。この diff そのものに対してコミットのブロックを解除 |

計測は省略できず、偽装もできません。**スクリーンショットなし → レビューなし → コミットなし。**

## モバイル計測バックエンド

どのモバイルスタックにも、実際のピクセルに至る経路があります。スキルは、スクリーンショットと a11y / view ツリーの両方を返す MCP を最優先し、次にスクリーンショットを返す MCP、最後に CLI ハーネスを選びます:

| 検出されたスタック | 優先バックエンド | スクリーンショット | A11y / 構造 |
|----------------|-------------------|------------|------------------|
| モバイル Web | `chrome-devtools` MCP（同梱） | `take_screenshot` + `emulate`/`resize_page` | `take_snapshot` |
| Flutter | `flutter` MCP（`dart mcp-server`） | スクリーンショットツール | ウィジェットツリー + ホットリロード |
| ネイティブ iOS | `ios-simulator` MCP（idb、macOS のみ） | `screenshot` / `ui_view` | `ui_describe_all` |
| React Native | **CLI スナップショットハーネス**（デフォルト。`mobile-mcp` を代替として提示） | `mobile-snapshot.sh capture …` | `adb uiautomator dump`（Android）、ピクセルのみ（iOS） |
| ネイティブ Android / クロスプラットフォーム | `mobile-mcp` MCP | `mobile_take_screenshot` | `mobile_list_elements_on_screen` |
| 任意のスタックで、機能する MCP がない場合 | **CLI スナップショットハーネス** | `mobile-snapshot.sh capture …` | `adb uiautomator dump`（Android）、ピクセルのみ（iOS） |

完全なルールと同点時の決め方: [`backend-detection.md`](skills/ux-ui-builder-mobile/references/backend-detection.md)。

## コミットゲート

`PreToolUse` フックが、すべての `Bash` 呼び出しの前に `ui-commit-gate.sh` を実行します。このゲートは:

1. `git commit` 以外はすべて許可します（fast path）。
2. ステージされた UI ファイルがないコミットは許可します。
3. UI のコミットであれば、ステージされた UI の diff の sha256 を計算し、`verdict: APPROVED` を含む `.ux-ui/approvals/<hash>.json` を探します。
4. 見つかれば → 許可。見つからなければ → **exit 2** でコミットをブロックし、ループを実行するよう伝えるメッセージを表示します。

承認は diff のハッシュに紐づいているため、その後に UI を編集すると承認は無効になります — ゲートは偽造できず、古くなることもありません。Web とモバイルの UI は同じゲートを共有します。

どのファイルを UI とみなすかは、環境変数 `UX_UI_GLOBS` で上書きできます。アーティファクトは `.ux-ui/` の下に置かれるので、コミットしたくない場合は `.gitignore` に追加してください。

## FAQ

**モデルに自分で撮ったスクリーンショットを目視確認させるだけではだめなのですか？**
「一度スクリーンショットを撮った」というのは規律ではないからです。このプラグインは、state × breakpoint マトリクス全体、a11y スナップショット、コンソール / ネットワーク / Lighthouse のシグナルを*必須とし*、独立したアートディレクターエージェントがそれらのアーティファクトを承認するまでコミットをブロックします。雰囲気ではなく、強制です。

**ブラウザ自動化をカスタム MCP として作り直しているのですか？**
いいえ。ブラウザ自動化は `chrome-devtools-mcp` としてすでに存在し、このプラグインはそれを同梱しています（モバイル MCP も同様です）。付加価値は*オーケストレーションと強制*、つまり measure → critique → iterate → gate にあり、それはスキル + エージェント + フックとして実装されています。MCP サーバーは Claude Code のサブエージェントを起動することも、レビューループを回すこともできないからです。

**なぜメインのモデルではなく、アートディレクターなのですか？**
分離のためです。実装するエージェントは自分の仕事に思い入れがあります。計測されたアーティファクトだけを見て判断し、コードを編集できない新しいエージェントなら、実装者が理屈をつけて見逃したものを捉えられます。スタジオにレビューの工程があるのと同じ理由です。

**バックエンドのコミットもブロックされますか？**
いいえ。ゲートは UI のファイル形式でのみ発動し、素の `.ts`/`.js`/`.java` とレイアウト以外の `.xml` は意図的に除外しています。バックエンドだけのコミットは、そのまま通過します。

**一度承認を得たら、そのまま編集を続けられますか？**
いいえ — それこそが狙いです。承認はステージされた UI の diff のハッシュに紐づいています。UI を 1 行でも変えるとハッシュが一致しなくなるので、ループを再実行するまでゲートは再びブロックします。

**使っているモバイルスタックのスクリーンショットを撮れる MCP がありません。どうすればいいですか？**
CLI スナップショットハーネス（`mobile-snapshot.sh`）が、`simctl`/`adb` を使ってシミュレーター / エミュレーターから実際の PNG を直接キャプチャし、アートディレクターがそれをレビューします。想像上の状態をレビューすることだけは、決してありません。

**開発サーバー、Chrome、起動済みのデバイスに到達できない場合は？**
想像上の状態のレビューにフォールバックするのではなく、停止してそのことを伝えます。環境が壊れていればハードストップ、というのが設計上の方針です。

## ライセンス

MIT。[LICENSE](../../LICENSE) を参照してください。

## 謝辞

計測してから批評するという規律は、`frontend-design` スキル（美的な方向性）と `chrome-devtools-mcp` プラグイン（ブラウザでの計測）に基づいています。ハードゲートと diff に紐づく承認のパターンは、作者の harness-engineering の取り組みにおける review-gate の設計を踏襲しています。
