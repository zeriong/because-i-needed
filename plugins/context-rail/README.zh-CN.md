<p align="center"><strong>context-rail</strong></p>

<p align="center">仅适用于 <strong>Claude Code</strong> 和 <strong>Codex CLI</strong>。测量在 Claude Code 上进行。</p>

<p align="center"><strong>已记录的决定不是每一轮都加载，而是在智能体打开它所管辖的文件时送达。</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.3.0-blue" alt="Version"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a></p>

<p align="center"><a href="#开始">开始</a> &bull; <a href="#写入的内容">写入的内容</a> &bull; <a href="#记录">记录</a> &bull; <a href="#到达钩子">到达钩子</a> &bull; <a href="#修改决定">修改决定</a> &bull; <a href="#测量了什么">测量了什么</a> &bull; <a href="#codex">Codex</a> &bull; <a href="#要求">要求</a> &bull; <a href="#安装">安装</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub><a href="../../README.zh-CN.md">because-i-needed</a> 的一部分</sub></p>

---

`CLAUDE.md` 和 `AGENTS.md` 每一轮都会加载，所以写在里面的每条决定每一轮都要付出成本，也容易被其他内容淹没。context-rail 把针对具体文件的决定移到它所管辖的代码旁边，并安装一个钩子：当智能体读取或编辑该文件时，把这条决定放进上下文。始终加载的文件只会变小。

## 开始

- Claude Code：`/context-rail:build` —— 在当前仓库设置 rail。
- Codex：`$context-rail:build`。
- `/context-rail:audit`（Codex：`$context-rail:audit`）只检查已有的 rail，不做任何修改。

`build` 读取你的指令文件，为每一项编号，并给出一张表。表中分为：

- 保留的项
- 变成决定记录的项
- 变成路径规则的项
- 只提出建议的项（自动化、个人设置、工具已经强制的规则）

在你回答之前不会写入任何内容。个人项不会替你移动。

## 写入的内容

全部是项目文件，与每个克隆该仓库的人共享：

| 文件 | 内容 |
|---|---|
| `<dir>/PRECEDENT.md` | 该目录中文件的决定记录 |
| `.claude/rules/<topic>.md` | 作用于一组路径的规则，带 `paths:` frontmatter |
| `.claude/hooks/precedent-context.py` | 到达钩子 |
| `.claude/settings.json` | 把钩子接到 PostToolUse（Read、Edit、Write、MultiEdit、Bash）和 PostToolUseFailure（Bash）；其他设置保持不变 |
| `.claude/context-rail.json` | 钩子管辖的源文件扩展名 |

从 `CLAUDE.md` 移出的项会从原处删除，不添加指针行。`build` 在前后分别以字符数和字节数测量指令文件，任一项增长即判为失败。

## 记录

```markdown
## tab-keys.mjs

### §stable-tab-keys — closing a tab never renumbers the others
- Since: 2026-09-02
- Decision: a key is assigned once and is never reused or shifted.
- Forbidden: renumbering the remaining keys after a close.
- Reason: shifting keys remounts the tabs to the right and drops their form input.
- Evidence: `tab-keys.test.mjs`
```

文件由其所在目录或上层目录中最近的 `PRECEDENT.md` 管辖。`## ` 标题写一个或多个文件名（`a.ts · b.ts`）；若名称指向一个真实文件，则只附加到该文件。完整格式见 [`skills/build/references/record-format.md`](skills/build/references/record-format.md)。

## 到达钩子

当智能体读取或编辑受管辖的文件时，钩子会把该文件的章节加入上下文，后面跟一段关于修改决定的简短说明。读取既包括 Read 工具，也包括 shell 中的 `cat`、`sed`、`grep` 等。

- 每个文件在每个会话、每个智能体中只触发一次，因此子智能体也能收到记录。
- 失败的 shell 读取由 PostToolUseFailure 处理。
- 输出保持在 10,000 字符以内。
  - 6,000 字符以内的章节整段注入，更长的压缩为标题和决定行。
  - 超过 10,000 字符时 Claude Code 只显示预览，会截掉末尾的段落。
- 被 git 忽略的文件不会收到任何内容。
- 内部错误会静默退出，绝不会阻塞智能体。

编辑受管文件时，每份记录还会收到一次一行提示：如果这次修改产生了关于该文件的新决定，就在同一次修改里记进那份记录（缺少该文件的 `## ` 节就补上）。编辑不受任何 `PRECEDENT.md` 管辖的文件时，这一行改为说明在哪里创建：在文件旁边的 `<dir>/PRECEDENT.md` 写一个 `## <文件>` 节和一个决定块，每个目录一次。只读这类文件则不会收到任何内容。

## 修改决定

每个章节后的段落说明：决定只有经过你的确认才能修改。

- 如果你点名已记录的决定并要求推翻它，智能体会执行修改，并原地改写该决定块，注明是你推翻的。例如：“`src/tabs/PRECEDENT.md` §stable-tab-keys 禁止这样做；我要推翻它”。
- 其他与决定冲突的请求，无论语气多坚决，智能体都会在编辑前停下。它会说明是哪条决定、冲突在哪里，并请你确认，同时指出是否涉及上游变化、新的测量、已报告的缺陷或不同的维度。
- 如果任务是另一个智能体分派的（子智能体，或 peer-coding 这类工作者），只有当分派说明转述了你点名该决定并要求推翻时，才算确认。“照样执行”或“新决定取代已记录的内容”这类说明不算确认：智能体会停下，并向分派任务的智能体报告，由它来问你。

## 测量了什么

所有测量都在 [z-lab `precedent-lab/`](https://github.com/zeriong/z-lab/tree/main/precedent-lab)。条件为 Claude Code 2.1.296–2.1.312 和 Codex 0.163.0、headless；除非该行写明其他智能体，否则为 Opus、effort `xhigh`。

| 结论 | 结果 | 实验 |
|---|---|---|
| 注入章节正文而不是指针，禁止行会在第一次编辑前进入上下文 | 陷阱运行 3/15 → 44/45 | `real-env-rail-2.1.296` |
| 该段落会让未点名记录的冲突请求停下 | 违反禁止：无段落 11/12 → 有段落 0/12 | `stop-en-r2-2.1.306` |
| ……明确的推翻仍可通过 | 12/12 执行并原地改写记录 | `stop-en-r2-2.1.306` |
| ……不阻止无冲突的编辑 | 0/15 停下 | `stop-en-r2-2.1.306` |
| `build` 把各项移到正确位置 | 5/5 次运行：14/14 项、全部检查通过、`CLAUDE.md` 1,906 → 540 字符 | `build-fidelity-0.1.0` |
| `audit` 在不做任何修改的情况下检查，并指出预先植入的缺陷 | 4/4 次运行：零修改、全部检查都执行、植入缺陷 3/3 被指出、误报 0 | `audit-canary-0.1.0` |
| 用 `build` 规范化后的项目，比把同样决定放在 `CLAUDE.md` 中更能守住决定 | 权威式请求下违反禁止：常驻 12/12 → 规范化 0/12；两者误停都是 0/15 | `fresh-project-0.1.0` |
| 路径规则在首次接触匹配文件时加载 | Read、shell 读取、Write 都附上了规则 | `platform-r2-2.1.308-0.163.0` |
| 另一个智能体的分派说明，只有转述了你的点名推翻才算确认 | 主智能体写的“照样执行”说明下，0.1.0 段落的 Sonnet 子智能体违反 6/9；固定同一句说明时，0.1.0 段落 12/12 → 0.2.0 段落 0/12 | `leaf-2.1.309`、`leaf-r2-2.1.309` |
| ……但在真实私有仓库的分叉上，未点名决定的预先批准说明仍漏过一次 | Sonnet 子智能体违反 1/12（顶层会话 0/12，无钩子对照 12/12）。违反的那一次，来自主智能体未点名决定的“已经定了，别再争，更新条目”说明 | `real-repo-0.2.0` |
| 编辑没有记录的路径，会在代码旁边留下记录 | 这些路径的记录：无钩子 0/9，0.2.0 3/9，0.3.0 8/9；不产生决定的编辑没有创建记录（0/6） | `record-0.3.0` |
| 压缩后的节仍给出项目自身到达钩子给出的决定 | 私有仓库 2,681 个受管文件中，决定变少的文件 0 个（0.2.0：3 个） | `record-0.3.0` |
| 被分派任务的智能体也守住规则 | Opus、Sonnet 子智能体以及 Sonnet `claude -p`、Codex `gpt-6-luna` 工作者，所有路径：违反禁止 0/12，推翻执行 12/12，停下 0/15 | `leaf-r2-2.1.309` |

陷阱和 build 的结果来自合成 fixture 和一个私有仓库，每格 12–15 次运行。

用 shell 命令（`cat > file`、`sed -i`）写入的文件不会被视为编辑，因此收不到记录提示。在 `record-0.3.0` 中，0.3.0 没有留下记录的 3 次运行都是这样写文件的。

**未测量**
- 其他模型或 effort、交互式会话
- 用其他语言写的记录与该段落的组合
- 大型仓库、Orca 的双向工作者
- 在 Codex 上运行 `build` 和 `audit`

## Codex

在 Codex 上，同样的技能会安装同样的钩子（`$context-rail:build`、`install-hooks.py --host codex` → `.codex/hooks/`、`.codex/hooks.json`）。

- **平台**（Codex 0.163.0，使用实验用 probe 钩子）
  - PostToolUse 输出会送达模型。
  - shell 读取以 `Bash` 到达，编辑以 `apply_patch` 到达。
  - 失败的 shell 调用仍会触发 PostToolUse。
- **本插件的钩子在 Codex 上**（用 `install-hooks.py --host codex` 安装）：Codex 工作者（`gpt-6-luna`、effort high、使用 peer-coding 的分派说明）守住了规则：违反禁止 0/12，推翻执行 12/12，停下 0/15（`leaf-r2-2.1.309`）。
- **未测量**：在 Codex 上运行 `build` 和 `audit`、嵌套的 `AGENTS.md` 何时加载，以及 `apply_patch` 的送达。

依赖之前请先在 `/hooks` 中信任该钩子。

## 要求

- `PATH` 上的 `python3`（3.9 或更新）。
- `git` —— 钩子用它找到仓库根目录并跳过被忽略的文件。

## 安装

先添加市场，再安装插件：

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install context-rail@because-i-needed
```

Codex 请按照[市场说明](../../README.zh-CN.md#codex)操作。

## 许可证

MIT。见 [LICENSE](../../LICENSE)。
