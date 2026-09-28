<p align="center">
  <strong>because-i-needed</strong>
</p>

<p align="center">
  <strong>因为自己需要而做的 Claude Code 插件——规划、项目 harness、基于实测的 UI。</strong>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin%20Marketplace-orange" alt="Claude Code Plugin Marketplace"></a>
</p>

<p align="center">
  <a href="README.md">English</a> &bull;
  <a href="README.ko.md">한국어</a> &bull;
  <a href="README.ja.md">日本語</a> &bull;
  <a href="README.zh-CN.md">简体中文</a> &bull;
  <a href="README.zh-TW.md">繁體中文</a>
</p>

---

本仓库是一个 Claude Code **插件市场**，包含三个相互独立的插件。按需安装即可。

## 插件

### [plan-smith](plugins/plan-smith) · `v1.5.0`

**通过两阶段流水线锻造计划。** 主智能体把整段对话提炼成一份上下文包（目标、硬约束、被否决的备选方案），并与你确认；随后由一个上下文干净的 `plan-writer` 智能体借助推理框架库和经过验证的写作风格撰写计划，再把计划原样转交给你——没有摘要损失，也没有上下文污染。

- **适用场景：** 需要为迁移、发布、build-out 制定计划时——凡是冗长嘈杂的会话容易把计划写得一团糟的任务都适用。
- **入口：** `/plan-smith:forge <任务>` 或直接说 *“帮我写一份……的计划”*

[查看 plan-smith 简体中文 README →](plugins/plan-smith/README.zh-CN.md)

### [harness](plugins/harness) · `v1.1.0`

**基于事实分析而非模板，构建为项目量身定制的 Claude Code harness。** 它直接读取仓库中实际的分层与关注点分离，推导出每条都引用你代码中 `file:line` 的规则，然后生成 `project-rules`、确定性的 `review-gate.sh`、`UserPromptSubmit` 钩子以及 `harness-engineering` 技能。

- **适用场景：** 在还没有 `.claude/` 配置的项目上开始使用 Claude Code，或者项目结构变化太大、旧配置已不再适用时。
- **入口：** `/harness:build` 或 *“build harness”*

[查看 harness 简体中文 README →](plugins/harness/README.zh-CN.md)

### [ux-ui](plugins/ux-ui) · `v1.2.0`

**以真实渲染的实测结果为依据构建 Web 与移动端 UI。** 它截取真实截图（Web 用 chrome-devtools；React Native / Flutter / iOS / Android 用移动端 MCP 或 CLI 快照 harness），让艺术总监智能体评审这些实测快照，反复迭代直到 UI 正确且优雅，并且在暂存的 diff 本身获得 APPROVED 之前拦截 UI 的 `git commit`。

- **适用场景：** 新建或修改任何组件、页面或界面，并希望在真实渲染上验证、而不是凭想象时。
- **入口：** `/ux-ui:build`（Web）· `/ux-ui:build-mobile`（移动端），或者直接让它构建 UI
- **注意：** 安装后会注册一个 `PreToolUse` 提交门禁钩子（在每次 `Bash` 调用前运行，只拦截 UI 提交）以及四个 MCP 服务器。

[查看 ux-ui 简体中文 README →](plugins/ux-ui/README.zh-CN.md)

## 安装

先添加一次插件市场，再安装需要的插件：

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install plan-smith@bin
claude plugin install harness@bin
claude plugin install ux-ui@bin
```

或者在 Claude Code 中：`/plugin` → Marketplaces → Add Marketplace → 输入 `https://github.com/zeriong/because-i-needed.git`，然后从列表中安装。

或者直接写入 `~/.claude/settings.json`：

```json
{
  "extraKnownMarketplaces": {
    "bin": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": {
    "plan-smith@bin": true,
    "harness@bin": true,
    "ux-ui@bin": true
  }
}
```

## 命名规则

每条命令都读作 **对象 : 动作** —— `/<插件>:<技能>`。

- **插件 = 对象** —— 它处理什么（`harness`、`ux-ui`）。`plan-smith` 保留已有的名称。
- **技能 = 动词** —— 从同一套共享词汇中选取，同一个动词在所有插件中含义相同。
- 插件保持独立：你只安装需要的插件，一个插件的钩子或 MCP 服务器不会随另一个插件一起装上。

| 动词 | 含义 |
|---|---|
| `build` | 在项目中生成产物（harness、UI 等） |
| `forge` | 把对话上下文提炼成文档（如计划） |
| `run` | 执行任务 |
| `mode` | 开启或关闭某种行为 |
| `audit` | 只读检查 |
| `review` | 评审结果 |

`run`、`mode`、`audit`、`review` 为后续插件预留。

## 仓库结构

```
because-i-needed/
├── .claude-plugin/marketplace.json   # 登记三个插件
└── plugins/
    ├── plan-smith/                   # 技能 + plan-writer 智能体 (+ CHANGELOG.md)
    ├── harness/                      # 技能
    └── ux-ui/                        # 2 个技能 + 2 个智能体 + 提交门禁钩子 + 4 个 MCP
```

每个插件目录都是自包含的：它的 README、清单文件以及随插件发布的所有内容都位于 `plugins/<名称>/` 下。

## 语言策略

- 本仓库的每一份 README——包括本文件和各插件的 README——都提供**五种语言**：`README.md`（英语，原文）、`README.ko.md`（한국어）、`README.ja.md`（日本語）、`README.zh-CN.md`（简体中文）、`README.zh-TW.md`（繁體中文）。
- 修改 README 时，在同一次提交中同步更新全部五种语言。新插件从第一次提交起就提供全部五种语言。
- 只有 README 需要翻译。其他所有文件——`CLAUDE.md`、`SKILL.md`、`references/*.md`、`agents/*.md`、`CHANGELOG.md`、钩子消息——都用英文编写。必须与用户输入相匹配的触发短语保留原语言。

## 许可证

MIT。详见 [LICENSE](LICENSE)。
