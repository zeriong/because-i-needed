<p align="center">
  <strong>harness-builder</strong>
</p>

<p align="center">
  <strong>为项目量身定制 Claude Code harness——基于事实分析，而非模板。</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-1.0.0-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a>
</p>

<p align="center">
  <a href="#安装">安装</a> &bull;
  <a href="#它能做什么">它能做什么</a> &bull;
  <a href="#8-phase-工作流">工作流</a> &bull;
  <a href="#fact-check-loop">Fact-check loop</a> &bull;
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
  <sub><a href="../../README.zh-CN.md">because-i-needed</a> 的插件</sub>
</p>

---

大多数“Claude Code harness”插件只是套出一个固定的 `.claude/` 骨架就算完事。它们强制执行的是*插件作者*想到的规则——而不是*你的项目真正需要*的规则。

**harness-builder 把这个顺序倒了过来。** 它先读你的项目，从实际存在的内容中推导规则，然后才生成一个强制执行*这些*规则的 harness。结果是一个为你的仓库量身定制的 `.claude/` 目录，每条规则都能追溯到你自己代码中的某处 `file:line` 引用。

## 特性

- **基于事实推导规则**——每条规则都来自对真实代码的 verdict，而不是模板。没有 `file:line` 引用的论断一律丢弃。
- **门禁优先的强制执行**——能够确定性检查的规则会变成 `review-gate.sh` 中基于退出码的门禁。只能定性判断的规则则作为建议性（advisory）规则保留，并在每次提示时呈现给 Claude。
- **感知副作用的回退**——构建过程中只要应用了任何补丁，就强制回到 Phase 1。harness 假定改动一行就可能让之前所有的 verdict 失效。
- **双评审交叉检查**——在宣布完成之前，构建流程会并行启动一个 Opus 智能体和一个 Sonnet 智能体（全新启动，不共享上下文），并依据六个质量维度综合它们的 JSON 报告。
- **Worse/better case 索引**——每条规则都附带一份 `docs/conventions/<rule>.md`，其中包含你仓库里实际存在问题的代码和实际的改进写法，并附有便于 grep 的关键词。
- **默认遵循 YAGNI**——在你的仓库中零违规、用户也从未提及的规则不会被引入。5 条规则就够的项目得到一个 5 条规则的 harness，这是成功，而不是失败。

## 何时使用

- 在还没有 `.claude/` 配置的项目上开始使用 Claude Code。
- 项目结构发生重大变化后，需要重建现有的 `.claude/`。
- 你想要的是与仓库中实际代码绑定的规则，而不是抽象的约定。

**可以跳过的情况：**

- 单文件工具或一次性脚本——用 harness 属于大材小用。
- 已经搭建并精心维护了一套你信得过的 `.claude/` 的项目。
- 没有清晰分层的仓库（fact-check loop 需要有可以抓住的结构）。

## 安装

### 通过 Claude Code 插件市场

1. 在 Claude Code 中运行 `/plugin`。
2. Marketplaces → Add Marketplace。
3. 输入 URL：`https://github.com/zeriong/because-i-needed.git`。
4. 安装 `harness-builder`。

### 或通过 CLI

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install harness-builder@because-i-needed
```

### 或直接写入 `~/.claude/settings.json`

```json
{
  "extraKnownMarketplaces": {
    "because-i-needed": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": { "harness-builder@because-i-needed": true }
}
```

## 快速开始

```
cd your-project
# 在 Claude Code 中:
/harness-builder:harness-builder
```

也可以用自然语言提出——触发关键词（韩语 / 英语）：`harness 만들어`、`build harness`、`harness 셋업`、`프로젝트 룰 추출`、`review gate 깔아줘`、`harness-builder`。

该技能会：

1. 就你的项目提出四个问题（包管理器、monorepo 形态、lint/typecheck 命令，以及你坚持要求的规则）。
2. 读取你的代码库，并对每一层运行 fact-check loop。
3. 推导规则、生成门禁脚本、接好钩子、编写技能，并为约定文档建立索引。
4. 用一个故意违规的样例验证一切正常工作。
5. 启动双评审小组做最终检查。

完整运行通常需要多轮对话——技能会如实告诉你这一点。支持用 `/loop` 包裹运行，但并非必需。

## 它能做什么

写入项目根目录的输出：

```
.claude/
├── settings.json                    # UserPromptSubmit 钩子接线
├── hooks/inject-context.sh          # 每次提示时注入 project-rules + harness-engineering
├── scripts/review-gate.sh           # 确定性门禁 — exit 0 / 1 / 2
└── skills/
    ├── project-rules/SKILL.md       # 在 Phase 1–2 中从你的代码推导出的规则
    └── harness-engineering/SKILL.md # 供后续任务使用的 11-phase 工作流

docs/conventions/
├── <rule-1>.md                      # worse case + better case (你仓库中的真实代码) + 关键词索引
├── <rule-2>.md
└── ...
```

构建完成后，项目中的每一条用户提示都会自动加载 `project-rules` 和 harness 的各个阶段。写前端代码？推导出的分层分离规则就会触发。编辑一个 300 行的组件？推导出的文件长度上限会把它拦下。规则是你的，不是插件的。

插件本身只包含一个技能：[`skills/harness-builder/SKILL.md`](skills/harness-builder/SKILL.md)——即下文的 8-phase 构建流程。

## 8-Phase 工作流

| Phase | 职责 | 需要 fact-check loop |
|-------|------|---------------------|
| 0 | **Intake**——包管理器、monorepo 形态、现有脚本、用户推荐的规则 | — |
| 1 | **Layer / Concern Reconnaissance**——每条论断都必须引用 `file:line` | ✅ 强制 |
| 2 | **Convention Extraction**——Phase 1 的 verdict 转化为规则 | ✅ |
| 3 | **`docs/conventions/<rule>.md`**——基于仓库真实代码建立 worse / better case 索引 | ✅ |
| 4 | 生成 **Gate script**（`review-gate.sh`） | — |
| 5 | **Hook 接线**（`UserPromptSubmit`） | — |
| 6 | **Skill 正文**（`project-rules` + `harness-engineering`） | — |
| 7 | **Self-verification**——用样例 diff 实际运行门禁 | — |
| 8 | **Review gate**——Opus + Sonnet 一次性评审，由主智能体综合并打补丁 | — |

**Phase 8 中只要应用了任何补丁，就强制回退到 Phase 1。** 这是一条绝对规则，而不是启发式经验——默认假定副作用会让之前的 verdict 失效。迭代上限为 3 次；若仍未收敛，技能会输出一份如实的失败报告，并等待你的决定。

## Fact-check loop

这是整个技能中最重要的一条规则。Phase 1 对你的代码做出的每一条论断，都必须通过以下流程：

```
论断:         "src/components/admin/audit-logs/page.tsx 只负责 presentation"
              ↓
自我怀疑:     "真的吗？验证一下。"
              ↓
直接读取:     用 Read 工具打开文件 — 不凭记忆，不做推断
              ↓
范围扫描:     在同一目录下 grep "useState|useEffect|fetch"
              ↓
副作用:       用 grep -r 查找导入该模块的地方
              ↓
SRP 测试:     它是否恰好只有一个变更理由？
              ↓
Verdict:      "presentation 与数据混杂 — page.tsx:24-31 调用了 fetch()"
              附 file:line 引用
              ↓
进入下一个 phase
```

跳过任何一步的论断都会被**丢弃**，Phase 1 重新开始。正是这一点让推导出的规则值得信赖——它们不是来自模型的直觉，而是来自你仓库中可验证的事实。

## “高质量”的定义

技能考虑应用的每个补丁，都会按六个维度自评打分（每项 0–5 分）：

| 维度 | 含义 |
|------|------|
| **SRP** | 每个模块只有一个变更理由 |
| **注释清晰度** | 简洁、只写要点、不超过 2 行 |
| **KISS** | 能解决问题的最简形式 |
| **DRY** | 模块之间没有重复逻辑 |
| **YAGNI** | 不引入投机性的功能或规则 |
| **易于理解** | 人类读者无需费力即可读懂 |

平均分低于 3.5 的补丁会被拒绝；如果拒绝率偏高，相应的 phase 会回退。

## 绕过 harness

构建完成后，每一条用户提示都会触发注入钩子。若只想在某一轮绕过：

- 在提示前加上 `!` 前缀（例如 `!直接回答就行`）
- 或者包含一个可识别的绕过短语（韩语 / 英语）：`harness 빼고`、`without harness`、`skip harness`、`no harness`

绕过模式会在该轮停用 phase 强制执行，但 project-rules 依然可见。

## FAQ

**为什么不直接给我一个 `.claude/` 模板？**
因为模板强制执行的是*别人的*规则。这个技能的意义在于强制执行*你项目自己的*规则——从它的实际代码中推导出来。你代码库里一个 200 LOC 的组件，和别人代码库里一个 200 LOC 的组件意义并不相同；上限应该来自你自己的代码。

**它和 linter / ESLint 配置有什么区别？**
linter 检查语法和已知的反模式。这个技能检查的是 linter 不擅长建模的结构性问题（分层分离、SRP、文件长度、命名），并把每条规则关联到你仓库中的某个 `file:line`，让违规有上下文可循。它是互补，而不是替代。

**为什么是两个评审而不是五个？**
这个技能所源自的 setup-guide 使用 2 个 Opus + 3 个 Sonnet 组成的 5 智能体评审小组。对于构建结束时的一次性评审来说，这属于过度设计——第 3 到第 5 个智能体带来的边际收益不足以抵消延迟。一个 Opus 加一个 Sonnet 就能以五分之一的成本获得大部分模型多样性收益。

**如果 Phase 1 判定我的项目分层已经很完美呢？**
那就不会引入分层分离规则。YAGNI 在这里同样适用——零违规且用户从未提及的规则禁止添加。如果你唯一关心的是命名，你就会得到一个只有一条规则的 harness。

**构建完成后可以修改生成的 `.claude/` 吗？**
可以。输出归你所有。技能不会跟踪或重新同步生成的文件。如果重新运行 `/harness-builder:harness-builder`，你需要自己处理合并。

**非前端项目也能用吗？**
Phase 1 中的分层信号是针对前端仓库（`*.tsx`、`use-*.ts`、`api/*`）调优的。对于 Go 服务或 Python 后端，技能需要不同的分层识别信号——而这正是 Phase 0 那个自由文本问题的用途。技能的*工作流*与项目无关；只有 Phase 1 的启发式规则经过了调优。

## 环境要求

- `git`、`jq`、`bash 4+`
- 目标项目必须是 git 工作树
- 支持插件的 Claude Code

## 许可证

MIT。详见 [LICENSE](../../LICENSE)。

## 致谢

8-phase 工作流源自作者撰写的一份非公开 harness setup-guide 和 research-foundation。fact-check loop 模式受到 CRITIC（Gou et al. 2023）以及 Anthropic Multi-Agent Research System 工程博客的影响。收敛上限（= 3）取自 Reflexion（Shinn et al. 2023）。
