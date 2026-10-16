<p align="center"><strong>dashboard</strong></p>

<p align="center">仅适用于 <strong>Claude Code</strong> 和 <strong>Codex CLI</strong>。</p>

<p align="center"><strong>一行看清你开启的所有 because-i-needed 模式，以及每个值的来源。</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.2.0-blue" alt="Version"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a></p>

<p align="center"><a href="#显示内容">显示内容</a> &bull; <a href="#claude-code">Claude Code</a> &bull; <a href="#codex">Codex</a> &bull; <a href="#插件如何加入">插件如何加入</a> &bull; <a href="#限制与状态">限制与状态</a> &bull; <a href="#安装">安装</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub><a href="../../README.zh-CN.md">because-i-needed</a> 的一部分</sub></p>

---

because-i-needed 的插件带有会一直保持设定的开关——peer-coding 的编排模式、free-hands 目标、budget 阈值——设置在项目级或用户级。dashboard 把它们全部显示出来，这样开关绝不会在你不知情的情况下开着。

## 显示内容

```
────────────────────────────────────────────────────────────────────────────────────────────────
💰budget: 80% · 5h now 24%   🙌free-hands: active 0/40 · 1 open (project) · owner lab-sess   🤝peer-coding: on (project)
```

- 一条浅色分隔线下方，每个已启用的 because-i-needed 插件所声明的开关各占一项 `{icon}label: value`；由项目级或环境变量决定时附上 `(project)` 或 `(env)`，以及一项细节，例如最近一次测得的用量窗口或目标所属的会话。终端较窄时，各项会换行，每行一项。
- 没有已启用的插件声明开关时，不显示任何内容。
- `/dashboard:audit`（Claude Code）或 `$dashboard:audit`（Codex）会打印同样的一行，并为每个开关给出项目级和全局级设置的值。它不会改动任何内容。

## Claude Code

这一行位于提示上方。它会在会话开始时、每一轮之后以及用量窗口变化时刷新。dashboard 会找出 Claude Code 已安装并已启用的 because-i-needed 插件。

## Codex

Codex 没有给插件提供绘制的位置，所以在 Codex 上，dashboard 就是 `$dashboard:audit` 命令。要让用量窗口保持可见，请在 `~/.codex/config.toml` 中（或通过 `/statusline`）打开 Codex 自带的状态栏项目：

```toml
[tui]
status_line = ["model-with-reasoning", "weekly-limit"]
```

它显示的是 7 天窗口**剩余**的部分（例如 `weekly 28% left`），而不是已用的部分。未知的项目 ID 会被丢弃并给出警告。

## 插件如何加入

插件在其根目录的 `dashboard.json` 中声明自己的开关。每个带有 `mode` 技能的 because-i-needed 插件都必须这样做，其他插件也可以这样做（本仓库的 Rule 11）：

```json
{ "entries": [ { "label": "peer-coding", "icon": "🤝", "status": ["bash", "scripts/mode.sh", "status", "--json"] } ] }
```

`icon` 是显示在名称前的一个表情符号（缺省时为 `🔹`）。`status` 命令是只读的，在项目目录中运行，并打印一个 JSON 对象：`value`、`source`（`env`、`project`、`global` 或 `default`）、`project` 和 `global`（各级的值，或 `null`），以及可选的 `detail`。命令失败、耗时超过两秒或输出了其他内容时，显示为 `error`。之后新增的插件无需 dashboard 发布新版本就会出现。

用 `claude --plugin-dir` 从文件夹加载的插件不在 Claude Code 的安装记录中；把它们的文件夹列在 `BECAUSE_I_NEEDED_PLUGIN_DIRS` 中（分隔方式与 `PATH` 相同）即可显示。

## 限制与状态

在 Claude Code 2.1.299 和 Codex 0.162.1 上每个用例测量一次（[z-lab `dashboard-lab/run-0.1.0`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab/run-0.1.0)；Codex 状态栏见 [`codex-status-line-0.162.1`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab/codex-status-line-0.162.1)）：

- 在 Claude Code 上，提示上方的这一行显示了 budget、free-hands 和 peer-coding，`/dashboard:audit` 打印了各级设置；没有声明开关的插件时，则没有这一行（D01–D03）。
- 在 Codex 上，`$dashboard:audit` 根据已安装的插件打印了同样的条目，其中 budget 条目带有 7 天窗口；没有声明开关的插件时，它会如实说明（D04–D05）。
- Codex 的 `weekly-limit` 项目显示了 `weekly 28% left`（C02）。
- 从 0.2.0 起（[`run-0.2.0`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab/run-0.2.0)，Claude Code 2.1.300）：在 200 列下，分隔线和 `{icon}label: value` 各项排在一行；在 80 列下，各项完整换行，每行一项；Codex 的 audit 也输出了相同的各项（D06–D08）。

未测量：tmux 以外的终端，以及粗体与浅色样式；通过 Claude Code 市场安装的插件（被测的这一行读取的是 `--plugin-dir` 文件夹；安装记录只做了单元测试）；会话中途开关变化后这一行是否刷新；桌面端和 IDE 界面。

绘制这一行所用的 Claude Code 插件钩子模块 API 被标记为抢先体验，在不同版本之间可能会变化。

## 安装

先添加市场，再安装插件：

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install dashboard@because-i-needed
```

Codex 请参阅[市场说明](../../README.zh-CN.md#codex)。`python3` 必须在 `PATH` 中。

## 许可证

MIT。参见 [LICENSE](../../LICENSE)。
