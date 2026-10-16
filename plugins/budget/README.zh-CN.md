<p align="center"><strong>budget</strong></p>

<p align="center">仅适用于 <strong>Claude Code</strong> 和 <strong>Codex CLI</strong>。</p>

<p align="center"><strong>选定用量窗口的一个比例；达到时，每个运行中的会话都会停下并询问是否继续。</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.1.1-blue" alt="Version"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a></p>

<p align="center"><a href="#开始">开始</a> &bull; <a href="#工作原理">工作原理</a> &bull; <a href="#设置与状态">设置与状态</a> &bull; <a href="#限制与状态">限制与状态</a> &bull; <a href="#要求">要求</a> &bull; <a href="#安装">安装</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub><a href="../../README.zh-CN.md">because-i-needed</a> 的一部分</sub></p>

---

budget 监视你的账户所报告的用量窗口，并让每个会话保持在你选定的比例之内。窗口达到该比例后，每个运行中的会话的下一次工具调用——包括其子智能体的调用——都会等待一个问题：**“지정한 n%에 도달했습니다, 작업을 이어서 진행하시겠어요?”**（你已达到设定的 n%——是否继续工作？）。回答 예 继续，回答 아니오 停止。[dashboard](../dashboard) 插件会显示你设定的阈值。

## 开始

- Claude Code：`/budget:mode 80` · Codex：`$budget:mode 80` ——在 80% 时停下并询问。
- `/budget:mode off` 关闭；`/budget:mode status` 显示阈值和最近一次测得的窗口。
- 阈值是针对你的用户账户的一项设置，由 Claude Code 和 Codex 共用。

## 工作原理

**Claude Code** 测量**五小时**窗口。Claude Code 会在每一轮之后，以及窗口每变化一个整数百分点时，向插件报告该窗口。当它达到或超过阈值时，budget 会拦下下一次工具调用，并在 Claude Code 自带的提问对话框中询问（标签 `budget`，选项 예 和 아니오）。

- 예：调用继续，该会话在窗口重置前不会再被询问。
- 아니오：调用被拒绝，本轮停止。
- 一个问题会同时回答其打开期间到达的所有调用，因此并行的子智能体只会被问一次。
- 无人可回答的运行（`claude -p`）和被关闭的对话框都按 아니오 处理。

**Codex** 测量 **7 天**窗口，这是 Codex 唯一会报告的窗口。budget 读取账户近期会话日志（`~/.codex/sessions`）中最新的数值，因此新会话从第一次调用起就会被拦下。Codex 没有插件可以打开的对话框，所以 budget 会拒绝该调用，并让智能体以同样的问题结束本轮。回答 예（也可以是 `네`、`yes`、`y`、`계속`、`continue`）即可继续；任何其他回答都会让会话保持停止。请先在 `/hooks` 中信任该插件的钩子。

**与 [free-hands](../free-hands) 配合：** free-hands 在目标执行期间从不提问，唯一的例外就是这个问题。budget 的问题在某个会话中处于打开状态时，free-hands 0.4.0 会放行它，并且不会让本轮继续。

## 设置与状态

- `~/.config/because-i-needed/budget.json`（设置了 `$XDG_CONFIG_HOME` 时位于其下）：`{"percent": 80}`。由 `/budget:mode` 写入；`off` 会将其删除。
- `~/.config/because-i-needed/budget/`：会话的问题处于打开状态时为 `pending/<session>.json`；某个窗口内回答 예 之后为 `acks/<session>.json`；`usage.json` 保存宿主最近一次报告的窗口（dashboard 会显示它）。
- 新窗口会再次询问。重置时间仅相差几秒视为同一个窗口，因为 Codex 报告的重置时间在两次读数之间会偏移一秒。

## 限制与状态

在 Claude Code 2.1.299 和 Codex 0.162.1 上每个用例测量一次（[z-lab `budget-lab`](https://github.com/zeriong/z-lab/tree/main/budget-lab)：`run-0.1.0`、`run-0.1.0-r2`；其依据的事实见 `codex-gate-0.1.0`、`codex-gate-0.1.0-r2` 和 z-lab `plugin-platform-lab/mod-interactive-2.1.299`）：

- Claude Code 显示了对话框；예 让调用得以执行，아니오 则停止本轮（“Interrupted”）。低于阈值时没有任何动作。两个并行的子智能体只被问了一次。回答 예 之后，后续调用无需再次询问即可执行（R01–R05、R10）。
- Codex 以该问题结束了本轮，且没有执行任何操作。예 解除了会话的限制，后续调用无需再次询问即可执行；低于阈值时没有任何动作（R06、R09、R11）。
- free-hands 运行目标时，该问题在 Claude Code 上得以显示。在 Codex 上，被拦下的这一轮立即结束；在 free-hands 0.3.0 下，停止守卫还会让它继续三次（R04、R07、R12；codex-gate B03）。

未测量：一轮已在运行时越过阈值（在 Claude Code 下一次报告之前，这一轮可能已超出阈值）；多个交互式会话同时运行；在阈值处运行 `claude -p`；Codex 的五小时窗口（在被测账户上未报告）；通过 `/hooks` 信任（而非绕过）的 Codex 钩子。

budget 所使用的 Claude Code 插件钩子模块 API 被标记为抢先体验，在不同版本之间可能会变化。

## 要求

- 支持插件钩子模块的 Claude Code（在 2.1.299 上测量）或 Codex CLI（在 0.162.1 上测量）。
- `PATH` 中有 `python3`，供 Codex 钩子和 `/budget:mode` 使用。

## 安装

先添加市场，再安装插件：

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install budget@because-i-needed
```

Codex 请参阅[市场说明](../../README.zh-CN.md#codex)。

## 许可证

MIT。参见 [LICENSE](../../LICENSE)。
