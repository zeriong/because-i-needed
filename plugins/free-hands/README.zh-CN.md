<p align="center"><strong>free-hands</strong></p>

<p align="center"><strong>给智能体一个有限目标，它就会不提问、不停下地完成清单。</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.1.0-blue" alt="版本"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="许可证：MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code 插件"></a></p>

<p align="center"><a href="#开始">开始</a> &bull; <a href="#目标文件">目标文件</a> &bull; <a href="#不提问">不提问</a> &bull; <a href="#钩子">钩子</a> &bull; <a href="#讨论面板">讨论面板</a> &bull; <a href="#堆叠pr">堆叠 PR</a> &bull; <a href="#限制与状态">限制与状态</a> &bull; <a href="#codex">Codex</a> &bull; <a href="#要求">要求</a> &bull; <a href="#安装">安装</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub><a href="../../README.zh-CN.md">because-i-needed</a> 的一部分</sub></p>

---

free-hands 将目标固定为有限且可检查的清单，然后不向你提问或停下，逐项完成所有未完成事项。遇到原本需要你决定的问题时，由五个只读角色组成的讨论面板提供意见；主智能体依据证据作决定，并记录不同意见和撤销方法。

## 开始

- Claude Code：`/free-hands:run <目标>`
- Codex：`$free-hands:run <目标>`
- 也可以在提示中写入 **free-hands**。首次响应会以你的语言询问一次是否开始。回答“是”后会带着该目标启动技能；回答“否”则会给出可能方向并结束本轮。解释或引用名称不算开始请求。目标有效期间再次说“free-hands”表示纠正当前执行方式，无需再次确认。

## 目标文件

free-hands 在仓库根目录保存 `.free-hands/goal.md`，并放置 `.free-hands/.gitignore`（`*`），这样无需触碰 `.git` 即可忽略该目录。文件记录一个目标、有限清单、决策和恢复说明：

```markdown
status: active
max_iterations: 40
iterations: 0
## Goal
<一句话目标>
## Checklist
- [ ] <有明确完成条件的有限事项>
## Decisions
## Resume
<下一会话需要的信息>
```

标记：`- [ ]` 未完成，`- [x]` 已完成，`- [-] … — needs the user` 因硬性限制或其他阻碍无法继续。状态为 `active`、`done`、`waiting` 或 `paused`。只有未完成的 `[ ]` 会让提问和停止守卫生效；只要仍有 `[ ]` 项，`done`/`waiting` 都不会结束本次运行。清单全部完成后记录 `done`；只剩需用户处理的事项时记录 `waiting`。达到 `max_iterations`（40）后，恢复说明要求智能体设为 `paused`、报告未完成事项并停止；此时可以再次提问。

## 不提问

目标处于活动状态时，技能不会向用户提问。此规则覆盖项目和其他技能中的提问要求，也覆盖 claude-x-codex 等工作流的审批门禁。智能体会不经询问推送分支并创建 PR。失败的测试、门禁、钩子或评审会被修复，或标记为 `- [-]`、需要用户处理；绝不会改成通过。其他插件的钩子仍会运行。

## 钩子

各钩子的触发条件不同：

- 只有位于 `## Checklist` 下方、且在代码块之外的 `- [ ]` 行才计为未完成项。
- 目标有未完成 `[ ]`、迭代数低于 `max_iterations`，且状态为 `active`，或为仍有未完成项的 `done`/`waiting` 时，提问和停止守卫会生效。提问守卫会拒绝提问工具。达到上限后可以提问。Stop 钩子会先将计数写入磁盘再阻止停止，最多继续40次。
- 目标为 `active` 时会发送恢复说明（`UserPromptSubmit`、包括压缩后的 `SessionStart`），即使没有未完成项也会发送；有未完成项的 `done`/`waiting` 状态也会发送。
- 没有有效且活动中的目标、但提示中出现“free-hands”时，会发送开始说明。后台任务通知不视为提示；提示中引用的通知会被忽略，提示的其余部分仍会被读取。

钩子输入错误时不会产生任何效果。目标文件格式错误或无法读取时，不会启用恢复、提问或停止行为；如果提示中含有“free-hands”，提示钩子会按没有活动目标的入口路径处理，并可能发送开始问题。写入失败和锁超时也不产生效果，因此钩子出错时工具调用或停止可以继续。

## 讨论面板

第一轮由五个角色独立阅读相同的简报，主智能体在汇总前会等待每个已派发角色的回复。只有第一轮意见不一致时才进行第二轮。缺失或无效的答复会重试一次；有效答复少于三份时标记为 **panel degraded**，由主智能体独自决定。无法确认最新模型的角色会跳过并计为缺失，不会换用其他模型。在 Claude Code 中，如果配置了 `ANTHROPIC_DEFAULT_<FAMILY>_MODEL` 重定向，该 family 的角色会缺席。主智能体会核实关键主张，依据证据而非票数决策：实际检查过的事实优先，其次是有来源的证据，再其次是推理。记录每个角色的意见、异议、最终决定和撤销方式。

| 角色 | 关注点 | Claude 模型系列 |
|---|---|---|
| `quick-thinker` | 快速的第一性原理判断 | `sonnet` |
| `deep-thinker` | 后果、边界情况和二阶影响 | `opus` |
| `evidence-hunter` | 文档与源代码证据 | `sonnet` |
| `trend-tracker` | 带日期的近期变化 | `sonnet` |
| `devils-advocate` | 对领先选项提出最有力的反对意见 | `opus` |

每个角色使用其模型系列中当前可用的最新模型。Claude Code 的 Agent 工具不会显示实际运行的模型 ID，因此应记录resolver 返回的 family alias，并注明“id not visible”。Codex 则记录子进程运行时报告的模型。

## 堆叠PR

第一个 PR 以仓库的 integration 分支为目标。每个 PR 的标题末尾都附上运行期间递增的编号 ` (n)`，之后的每个 PR 都基于前一个分支。用户按堆叠顺序合并 PR。前一个 PR 合并后，智能体在需要时将下一个 PR 的目标分支改为 integration，再把 `origin/<integration>` 合并到其后的每个分支并推送。受阻的批次不会跳过，因此堆叠顺序就是合并顺序。

## 限制与状态

“面板比单个智能体决策更好”目前是**尚未测量的假设**。在 Claude Code 2.1.286–2.1.287 和 Codex 0.159.3–0.160.0 上，每个案例测量一次的内容（[z-lab `free-hands-lab`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab)：`run-0.1.0`、`run-0.1.0-r2`）：

- 钩子会在会话开始、每条提示以及压缩后注入恢复说明（F01、F04、G02）。在 Claude Code 上，有未完成项时停止守卫会拦截停止并将计数写入磁盘（F02）；Codex 不会打印钩子事件，因此只有一次拦截得到证实（F04）。
- 开始问题、对“是”和“否”的回答，以及解释性提及，在两个宿主上的表现均符合描述；但对韩语提示，Codex 用英语提问，并在用户回答“否”后只作简单回应，没有给出方向建议（F06）。
- 停止请求以 `paused` 结束；需要用户处理的事项以 `[-]` 和 `waiting` 结束（G01、G03）。
- 以 `FREE_HANDS_ROLE` 启动的面板子进程不会改动父进程的目标（F05）。
- 五个角色在两个宿主上均使用各自系列的最新模型并返回有效答复；Claude 主智能体会等待五个角色全部完成（F08、F09、G04）。

未测量：拒绝 `AskUserQuestion`（无头模式的 Claude Code 没有此工具）以及拒绝 Codex 的 `request_user_input`（智能体未调用）；运行时在 `max_iterations` 处的解除和计数器写入失败（仅有单元测试）；第二轮（所有面板成员意见一致）；阻止角色写入尝试（没有角色尝试）；交互式 `/hooks` 信任；堆叠 PR。智能体在四次运行中自行重写了 `iterations`（F04、G03），因此只有智能体不改动计数器时上限才有效。

以下是技能和恢复说明给智能体的规则。没有钩子会拦截这些命令：

- 不合并 PR，也不向默认分支合并任何内容。
- 不以不可逆的方式删除仓库外的文件、数据、远程分支或数据库。
- 不部署、发布或向外部发送内容（例如版本发布、包发布、邮件或消息）。

此类事项标记为 `- [-]` 并写明原因，然后继续其他事项。已推送分支允许在提前一行告知后强制推送。

要暂停，请说 **“pause”**、**“stop”** 或 **“일시정지”**。目标记录为 `paused`；再次运行命令即可恢复。

来源：移植自一个项目本地技能。

## Codex

依赖自动执行前，请在 `/hooks` 中信任插件钩子。提问钩子的 matcher 包含 `request_user_input`；尚未观察到它被拒绝。Codex 默认模式没有提问工具，因此由 Stop 钩子负责确保继续执行。即使钩子未获信任或未启用，技能仍按书面规则继续，但钩子效果可能未启用。

面板为每个角色启动一个 `codex exec -s read-only` 子进程（native subagent 可以指定模型，但没有只读控制，因此不使用 — F10）。无论角色如何，子进程都可以搜索网页；为 `evidence-hunter` 和 `trend-tracker` 添加 `--search`（F09）。子进程需要网络。从沙箱中的主智能体运行时，`panel.py run` 必须通过获准的提权在沙箱外运行，或由会话允许网络。否则所有子进程都会失败，本次运行继续由主智能体独自决策并记录为 **panel degraded**（G06）。

## 要求

- 钩子需要 `python3`，并且必须位于 `PATH` 中。
- 需要 `git` 来查找仓库根目录。
- 堆叠 PR 流程需要 `gh`。
- Codex 面板流程需要 Codex CLI（`codex`）。

## 安装

先添加市场，再安装插件：

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install free-hands@because-i-needed
```

Codex 请参阅[市场说明](../../README.zh-CN.md#codex)。

## 许可证

MIT。参见 [LICENSE](../../LICENSE)。
