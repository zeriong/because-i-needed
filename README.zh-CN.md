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

### [plan-smith](plugins/plan-smith) · `v1.4.2`

**通过两阶段流水线锻造计划。** 主智能体把整段对话提炼成一份上下文包（目标、硬约束、被否决的备选方案），并与你确认；随后由一个上下文干净的 `plan-writer` 智能体借助推理框架库和经过验证的写作风格撰写计划，再把计划原样转交给你——没有摘要损失，也没有上下文污染。

- **适用场景：** 需要为迁移、发布、build-out 制定计划时——凡是冗长嘈杂的会话容易把计划写得一团糟的任务都适用。
- **入口：** `/plan-smith:plan-smith <任务>` 或直接说 *“帮我写一份……的计划”*

[查看 plan-smith 简体中文 README →](plugins/plan-smith/README.zh-CN.md)

### [harness-builder](plugins/harness-builder) · `v1.0.0`

**基于事实分析而非模板，构建为项目量身定制的 Claude Code harness。** 它直接读取仓库中实际的分层与关注点分离，推导出每条都引用你代码中 `file:line` 的规则，然后生成 `project-rules`、确定性的 `review-gate.sh`、`UserPromptSubmit` 钩子以及 `harness-engineering` 技能。

- **适用场景：** 在还没有 `.claude/` 配置的项目上开始使用 Claude Code，或者项目结构变化太大、旧配置已不再适用时。
- **入口：** `/harness-builder:harness-builder` 或 *“build harness”*

[查看 harness-builder 简体中文 README →](plugins/harness-builder/README.zh-CN.md)

### [ux-ui-builder](plugins/ux-ui-builder) · `v1.1.0`

**以真实渲染的实测结果为依据构建 Web 与移动端 UI。** 它截取真实截图（Web 用 chrome-devtools；React Native / Flutter / iOS / Android 用移动端 MCP 或 CLI 快照 harness），让艺术总监智能体评审这些实测快照，反复迭代直到 UI 正确且优雅，并且在暂存的 diff 本身获得 APPROVED 之前拦截 UI 的 `git commit`。

- **适用场景：** 新建或修改任何组件、页面或界面，并希望在真实渲染上验证、而不是凭想象时。
- **入口：** `/ux-ui-builder:ux-ui-builder`（Web）· `/ux-ui-builder:ux-ui-builder-mobile`（移动端），或者直接让它构建 UI
- **注意：** 安装后会注册一个 `PreToolUse` 提交门禁钩子（在每次 `Bash` 调用前运行，只拦截 UI 提交）以及四个 MCP 服务器。

[查看 ux-ui-builder 简体中文 README →](plugins/ux-ui-builder/README.zh-CN.md)

## 安装

先添加一次插件市场，再安装需要的插件：

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install plan-smith@because-i-needed
claude plugin install harness-builder@because-i-needed
claude plugin install ux-ui-builder@because-i-needed
```

或者在 Claude Code 中：`/plugin` → Marketplaces → Add Marketplace → 输入 `https://github.com/zeriong/because-i-needed.git`，然后从列表中安装。

或者直接写入 `~/.claude/settings.json`：

```json
{
  "extraKnownMarketplaces": {
    "because-i-needed": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": {
    "plan-smith@because-i-needed": true,
    "harness-builder@because-i-needed": true,
    "ux-ui-builder@because-i-needed": true
  }
}
```

## 仓库结构

```
because-i-needed/
├── .claude-plugin/marketplace.json   # 登记三个插件
└── plugins/
    ├── plan-smith/                   # 技能 + plan-writer 智能体 (+ CHANGELOG.md)
    ├── harness-builder/              # 技能
    └── ux-ui-builder/                # 2 个技能 + 2 个智能体 + 提交门禁钩子 + 4 个 MCP
```

每个插件目录都是自包含的：它的 README、清单文件以及随插件发布的所有内容都位于 `plugins/<名称>/` 下。

## 语言策略

- 本仓库的每一份 README——包括本文件和各插件的 README——都提供**五种语言**：`README.md`（英语，原文）、`README.ko.md`（한국어）、`README.ja.md`（日本語）、`README.zh-CN.md`（简体中文）、`README.zh-TW.md`（繁體中文）。
- 修改 README 时，在同一次提交中同步更新全部五种语言。新插件从第一次提交起就提供全部五种语言。
- Claude 直接读取的文件——`SKILL.md`、`references/*.md`、`agents/*.md`——保持英文。

## 许可证

MIT。详见 [LICENSE](LICENSE)。
