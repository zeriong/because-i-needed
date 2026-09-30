<p align="center">
  <strong>claude-x-codex</strong>
</p>

<p align="center">
  <strong>Claude × Codex 同伴编排——两个智能体以同伴身份互相规划、实现和评审彼此的工作。</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.3.1-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a>
</p>

<p align="center">
  <a href="#安装">安装</a> &bull;
  <a href="#命令">命令</a> &bull;
  <a href="#工作原理">工作原理</a> &bull;
  <a href="#配置">配置</a> &bull;
  <a href="#平台">平台</a>
</p>

<p align="center">
  <a href="README.md">English</a> &bull;
  <a href="README.ko.md">한국어</a> &bull;
  <a href="README.ja.md">日本語</a> &bull;
  <a href="README.zh-CN.md">简体中文</a> &bull;
  <a href="README.zh-TW.md">繁體中文</a>
</p>

<p align="center">
  <sub><a href="../../README.zh-CN.md">because-i-needed</a> 的插件</sub>
</p>

---

**C**laude **×** **C**odex 同伴编排。基础不同的两个智能体会以不同的方式出错，所以它们互相评审对方的工作——主智能体自己的计划也不例外。两者意见分歧时，由测试而不是角色来裁定。

claude-x-codex 是非官方的社区插件，并非由 Anthropic 或 OpenAI 制作、认可或提供支持。

## Codex

需要 Codex CLI 0.158.0 或更高版本。安装后请启动新会话。Claude 使用 `/plugin:skill`，Codex 使用 `$plugin:skill`。共享技能和资源均包含在此插件内。依赖自动行为前，请在 `/hooks` 中审核并信任随附的钩子。

```bash
codex plugin marketplace add https://github.com/zeriong/because-i-needed.git
codex plugin add claude-x-codex@bin
```

使用 `$claude-x-codex:run`、`$claude-x-codex:mode on|off|status|clear` 和 `$claude-x-codex:audit`。两个宿主的模式操作都需要用户明确请求。Codex 可以担任主代理，现有 Codex 适配器保持跨厂商评审。审计包含 `.codex/hooks.json` 及未提交的 `.codex/`、`.agents/` 上下文。自动模式需要信任 UserPromptSubmit 钩子，显式 run 不依赖它。Codex 为主代理时，跨厂商工作需要 Claude CLI；缺少时使用既有单厂商回退路径。

### Codex 设置

两端使用相同的 `CXC_*` 设置、模式作用域和跨供应商评审规则。链接的 Git worktree 中也会在本地排除模式文件。审计不修改配置，并报告 `AGENTS.override.md` 的优先级及无效的钩子声明。

各宿主的路由使用配置的 CXC 评审模型和推理强度，括号内仅为默认值。仅提及文件名或 fallback 配置不会被判定为指令一致，而会标为 CHECK，要求核对实际生效内容。

## 命令

| 命令 | 作用 |
|---|---|
| `/claude-x-codex:run` | 编排一项任务：主智能体负责规划并做出每个关卡的决定，把工作分派到 `claude-fast` / `codex-bulk` / `main` 通道，并让每个厂商评审另一个厂商的工作 |
| `/claude-x-codex:mode on\|off\|status\|clear [--global]` | 开启或关闭自动编排的一行开关。仅限用户使用，模型无法切换 |
| `/claude-x-codex:audit` | 以只读方式检查两个厂商是否从同样的项目上下文出发；只提出修改建议，不做任何更改 |

`on`、`off` 写入本项目的标志（`.claude-x-codex/mode`，已排除在 git 之外）；`--global` 写入对所有项目生效的默认值（`~/.config/claude-x-codex/mode`）；`clear` 删除项目标志；`CXC_MODE=on|off` 在单个 shell 中优先于两者。模式关闭时，`run` 只在你明确要求时才启动。

## 安装

### 通过 Claude Code 插件市场

1. 在 Claude Code 中运行 `/plugin`。
2. Marketplaces → Add Marketplace。
3. 输入 URL：`https://github.com/zeriong/because-i-needed.git`（或本仓库的本地路径）。
4. 安装 `claude-x-codex`。

### 或通过 CLI

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git   # 或本地路径
claude plugin install claude-x-codex@bin
```

### 或直接写入 `~/.claude/settings.json`

```json
{
  "extraKnownMarketplaces": {
    "bin": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": { "claude-x-codex@bin": true }
}
```

- **注意：** 安装后会注册一个 `UserPromptSubmit` 钩子。它在每条提示时运行，模式关闭时不输出任何内容；模式开启时，它会添加一段四行的提示（每条提示约 100 个输入 token），把实现类工作转交给 `run`。

## 环境要求

- **Claude Code**（或作为主智能体的 Codex）、一个 **git** 仓库，以及 bash 3.2+。
- **可选——Codex CLI**（`codex`）。没有它时，`run` 会切换到 single-vendor 模式，把所有评审交给同一厂商的另一个评审实例，并告知你这一点。
- **可选——Orca**（已启用编排）。有了它，工作者可以在任务进行中提问，关卡会等待你的决定；没有它时，工作者以子智能体或 CLI 调用的方式单向运行。
- 审计的钩子表需要 `python3`；当 Codex 作为主智能体运行 Claude 评审者时需要 `jq`。
- 已在 Claude Code 2.1.283、Codex CLI 0.157.1 和 Orca 1.4.215 上验证。

## 工作原理

- **通道**——工作者以 effort `high` 运行。`claude-fast`（Claude 最新 Sonnet：UI、交互、代码品味、Claude 侧的工具）、`codex-bulk`（Codex 最新 `luna`：结果已完全确定的工作，例如针对现有契约的测试、类型和机械式迁移）、`main`（主智能体：紧密耦合的工作，或规格仍在摸索中的工作）。
- **跨厂商评审**——评审者始终与作者属于不同厂商，主智能体自己的计划和分诊决定也交给另一个厂商评审。Claude 用最新 Opus、Codex 用最新 `sol` 评审，两者的 effort 都是 `xhigh`——在两个 CLI 中都是仅次于 `max` 的级别。即使是认证、支付、数据迁移等高风险阶段，在追加顶级模型（最新 `astra` 或 `max` 的最新 Opus）评审之前也会先询问你，绝不自行升级。评审者以只读方式运行，返回由两个 CLI 用 schema 强制约束的 JSON。
- **一轮反驳**——被驳回的 blocking 或 major 意见会连同理由退回给评审者一次。评审者要么认可，要么用新证据反驳；仍未解决时，会连同双方论点以 DISPUTED 提交给你。
- **证据说了算**——出现分歧时，拥有测试、复现或追踪的一方胜出。没有证据时由你决定。
- **上下文桥接**——审计会找出两个厂商读取不同指令文件的位置、只约束一个厂商的钩子，以及工作者的 worktree 中会缺失的未提交上下文。`run` 发起的 Codex 调用通过 Codex 的回退设置读取 `CLAUDE.md`，无需修改仓库；交互式 Codex 会话（Orca 工作者，或作为主智能体的 Codex）需要在你的 Codex 配置中加入同样的设置。任何需要修改你的配置或仓库的调整都会在计划审批时提出。
- **状态落盘**——`.claude-x-codex/`（已排除在 git 之外）保存计划、决定和评审，因此一次运行在上下文压缩后仍可恢复。

有专用规划技能时，`run` 会将规划交给该技能。

## 配置

`run` 从环境变量读取以下值，缺省时使用默认值：

| 变量 | 默认值 |
|---|---|
| `CXC_WORKER_MODEL` | `luna` |
| `CXC_REVIEW_MODEL` | `sol` |
| `CXC_FINAL_MODEL` | `astra` |
| `CXC_CLAUDE_WORKER` | `sonnet` |
| `CXC_CLAUDE_REVIEWER` | `opus` |
| `CXC_REVIEW_EFFORT` | `xhigh` |
| `CXC_WORKER_EFFORT` | `high` |
| `CXC_MAX_CYCLES` | `3` |
| `CXC_PARALLEL` | `3` |

模型设置表示一个系列，并始终运行已安装 CLI 提供的该系列最新版本。像 `gpt-6-sol` 这样的版本值也会提升到该系列最新版本；若无法确定最新版本，通道会说明原因并停止。

CXC = **C**laude **×** **C**odex——你在 shell 中设置的变量的前缀。

## 平台

脚本是只使用 POSIX 工具的 bash（兼容 macOS 的 bash 3.2 和 BSD 工具）。

| 平台 | 状态 |
|---|---|
| Linux | 支持 |
| macOS | 支持 |
| Windows + WSL | 支持（行为与 Linux 相同） |
| Windows + Git Bash | 应该可用；路径遵循 Git Bash（`~` = `/c/Users/<you>`） |
| 仅 Windows PowerShell / cmd | 不支持——请安装 Git for Windows 或使用 WSL |

在 Windows 上，脚本必须保持 LF 换行。插件的 `.gitattributes` 会强制这一点；如果你不通过 git 复制文件，请把换行符转换为 LF。

## 许可证

MIT。参见 [LICENSE](../../LICENSE)。
