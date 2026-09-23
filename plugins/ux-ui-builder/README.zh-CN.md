<p align="center">
  <strong>ux-ui-builder</strong>
</p>

<p align="center">
  <strong>像设计工作室交付作品那样构建 Web 与移动端 UI——在真实渲染上实测，由艺术总监评审，在提交时把关。</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-1.1.0-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a>
</p>

<p align="center">
  <a href="#安装">安装</a> &bull;
  <a href="#它能做什么">它能做什么</a> &bull;
  <a href="#循环">循环</a> &bull;
  <a href="#移动端测量后端">移动端后端</a> &bull;
  <a href="#提交门禁">提交门禁</a> &bull;
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

智能体凭想象实现 UI 时，往往做得很糟——看不见的溢出、缺失的 focus ring、未处理的空状态、泄漏到标签里的原始 UUID。不看真实渲染，这些问题一个都不会暴露。

**ux-ui-builder 把想象从循环中剔除。** 每一处 UI 改动都在真实渲染上实测——Web 通过 chrome-devtools 在浏览器页面上测，移动端则在真实设备/模拟器上测——由艺术总监智能体对照*实测*快照进行评审，反复迭代直到既正确又优雅，最后再经过硬门禁：艺术总监没有针对这份暂存 diff 本身给出 APPROVED 的 UI，就无法提交。

## 特性

- **只看实测，绝不凭想象**——技能驱动内置的 **chrome-devtools MCP** 捕获真实渲染：在 mobile / tablet / desktop 下覆盖 default / hover / focus / loading / empty / error / long-content 各状态，外加 DOM/a11y 快照、控制台 + 网络信号，以及一次 Lighthouse 审计。
- **也支持移动端** *（1.1 新增）*——第二个技能 `ux-ui-builder-mobile` 会检测应用的技术栈（React Native / Expo / Flutter / 原生 iOS / 原生 Android / 移动 Web），选择一个能从已启动的设备或模拟器返回**真实像素**的测量后端，并捕获 device × orientation × state 矩阵。如果没有任何 MCP 能为该技术栈截图，就由内置的 **CLI 快照 harness**（`simctl` / `adb`）来完成。
- **艺术总监硬门禁**——`ux-ui-art-director` 智能体（Opus）只评审实测产物；移动端则由 `ux-ui-mobile-art-director` 按平台惯例（Apple HIG / Material）评判。只要存在任何 critical/major 缺陷 → `CHANGES_REQUIRED`。它们可以自行重新测量所需状态（移动端总监仅限支持 MCP 的技术栈；在只能用 CLI harness 的技术栈上，它会改为要求提供截图），但不能修改代码（评审者与实现者分离）。
- **与 diff 绑定的批准**——批准绑定在暂存 UI diff 的 sha256 上。再次修改 UI，哈希就会改变，门禁便会再次拦截。“批准一次、继续修改”在结构上不可能；不存在过期或伪造的批准。
- **自主迭代**——build → measure → critique → fix → re-measure，最多 3 轮，无需用户额外提示。第一次提交就是优雅的前端。（移动端循环只会在开始时暂停一次，用于确认测量后端。）
- **零配置**——自带浏览器与移动端 MCP，也自带正确性 + 优雅度标准，因此在什么都没配置的项目中也能工作。如果宿主项目*确实*定义了设计规则，则以宿主项目的规则为准。
- **保守的 blast radius**——门禁只对真正的 UI 文件类型生效：Web（`.tsx .jsx .vue .svelte .astro .css .scss .sass .less .html`）和移动端（`.swift .kt .dart .storyboard .xib`、Android `res/layout*/**/*.xml`）。单纯的 `.ts`/`.js`/`.java` 以及非布局的 `.xml` 被排除在外，因此纯后端提交永远不会被拦截。

## 安装

### 通过 Claude Code 插件市场

1. 在 Claude Code 中运行 `/plugin`。
2. Marketplaces → Add Marketplace。
3. 输入 URL：`https://github.com/zeriong/because-i-needed.git`（或本仓库的本地路径）。
4. 安装 `ux-ui-builder`。

### 或通过 CLI

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git   # 或本地路径
claude plugin install ux-ui-builder@because-i-needed
```

### 或直接写入 `~/.claude/settings.json`

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

安装后会自动注册所有内容：四个 MCP 服务器（`chrome-devtools`、`mobile-mcp`、`ios-simulator`、`flutter`）、提交门禁钩子、`ux-ui-art-director` 和 `ux-ui-mobile-art-director` 智能体，以及 `ux-ui-builder` 和 `ux-ui-builder-mobile` 技能。

## 环境要求

- **Web**：**Node.js**（内置的 `chrome-devtools-mcp` 通过 `npx` 运行）、本地 **Chrome**，以及你正在构建 UI 的那个项目的可运行**开发服务器**。
- **移动端**：对应技术栈的平台 SDK——Xcode + 模拟器（iOS，仅限 macOS）、Android SDK + 模拟器，或 Flutter SDK——并且应用正运行在已启动的设备/模拟器上。移动端 MCP（`@mobilenext/mobile-mcp`、`ios-simulator-mcp`、`dart mcp-server`）只在安装了相应工具的环境中启动；`mobile-snapshot.sh` harness 只需要 `simctl`/`adb`。
- **git** 工作树，以及 `shasum`/`sha256sum`（macOS/Linux 默认自带）。

## 快速开始

```
cd your-project
# 在 Claude Code 中直接构建 UI 即可。实现或修改某个界面时:
/ux-ui-builder:ux-ui-builder          # Web
/ux-ui-builder:ux-ui-builder-mobile   # 移动端 (RN / Flutter / iOS / Android / 移动 Web)
```

当你要求构建、修复、重新设计组件、页面、界面、表单、sheet、列表或布局，或为它们调整样式时，两个技能也都会自动触发。

Web 技能会：

1. 自检浏览器 MCP 和你的开发服务器（必要时启动服务器）。
2. 为这个具体功能规划设计意图（而不是套用模板式默认值）。
3. 构建 UI。
4. 在 state × breakpoint 矩阵上实测真实渲染。
5. 把实测结果交给艺术总监评审。
6. 应用修复并重新测量，直到 `APPROVED`（上限 = 3）。
7. 记录批准，解除对你提交的拦截。

移动端技能运行同样的循环，但第 1 步会先检测你的技术栈、运行 harness 的 `doctor`，并请你确认测量后端——这是唯一一次交互式暂停——第 4 步则在已启动的目标上实测 device × orientation × state 矩阵。

如果你试图在没有匹配批准的情况下提交 UI，门禁会拦截提交，并提示你运行该循环。

## 它能做什么

```
your-project/
└── .ux-ui/
    ├── measure/<feature>/        # 截图、snapshots.md、signals.md、context.md
    └── approvals/<diff-hash>.json # 提交门禁检查的 APPROVED 产物
```

插件本身包含：

```
plugins/ux-ui-builder/
├── .claude-plugin/plugin.json          # 清单 + 内置 MCP (chrome-devtools, mobile-mcp, ios-simulator, flutter)
├── hooks/hooks.json                    # PreToolUse → 提交门禁
├── scripts/
│   ├── ui-commit-gate.sh               # 门禁: hash | approve <feature> [dir] | hook-block (Web + 移动端文件类型)
│   └── mobile-snapshot.sh              # CLI 快照 harness: doctor | capture <ios|android> <dir> <label>
├── agents/
│   ├── ux-ui-art-director.md           # Web 艺术总监 (实测 + 评审, Opus)
│   └── ux-ui-mobile-art-director.md    # 移动端艺术总监 (HIG / Material 惯例, Opus)
└── skills/
    ├── ux-ui-builder/                  # Web: measure → critique → iterate → gate
    │   ├── SKILL.md
    │   └── references/
    │       ├── design-principles.md    # 正确性 + 优雅度标准 (自包含)
    │       ├── measurement-protocol.md # 精确的 chrome-devtools 捕获协议
    │       └── review-rubric.md        # verdict 格式 + APPROVED 产物契约
    └── ux-ui-builder-mobile/           # 移动端: detect → measure → critique → iterate → gate
        ├── SKILL.md
        └── references/
            ├── backend-detection.md          # 检测技术栈 + 选择真实像素后端
            ├── mobile-design-principles.md   # HIG / Material、安全区域、点击目标、手势、键盘、深色模式
            ├── mobile-measurement-protocol.md # 按后端捕获 (device × orientation × state)
            └── mobile-review-rubric.md       # verdict 格式 + APPROVED 产物契约
```

## 循环

| 步骤 | 职责 |
|------|------|
| 0 | **Bootstrap**——确认浏览器 MCP + 开发服务器；选定一个 feature slug。*移动端：* 检测技术栈，运行 `mobile-snapshot.sh doctor`，与你确认后端，确保应用运行在已启动的目标上 |
| 1 | **Plan**——为*这个*功能制定精炼的设计意图；避免 AI 默认风格（移动端：在平台惯例之内） |
| 2 | **Build**——实现，复用现有组件/token |
| 3 | **Measure**——捕获真实的 state × breakpoint 矩阵 + 各项审计（移动端：device × orientation × state）——必需 |
| 4 | **Critique**——针对实测产物启动 `ux-ui-art-director`（Web）或 `ux-ui-mobile-art-director`（移动端）（硬门禁） |
| 5 | **Iterate**——应用修复，回到第 3 步，重新评审（上限 = 3） |
| 6 | **Record approval**——仅在 APPROVED 时进行；为这份 diff 本身解除提交拦截 |

实测从来不是可选项，也绝不能造假。**没有截图 → 没有评审 → 没有提交。**

## 移动端测量后端

每个移动端技术栈都有获取真实像素的途径。技能优先选择同时返回截图和 a11y/view 树的 MCP，其次是任何能返回截图的 MCP，最后才是 CLI harness：

| 检测到的技术栈 | 首选后端 | 截图 | A11y / 结构 |
|----------------|-------------------|------------|------------------|
| 移动 Web | `chrome-devtools` MCP（内置） | `take_screenshot` + `emulate`/`resize_page` | `take_snapshot` |
| Flutter | `flutter` MCP（`dart mcp-server`） | 截图工具 | widget 树 + 热重载 |
| 原生 iOS | `ios-simulator` MCP（idb，仅限 macOS） | `screenshot` / `ui_view` | `ui_describe_all` |
| React Native | **CLI 快照 harness**（默认；`mobile-mcp` 作为备选） | `mobile-snapshot.sh capture …` | `adb uiautomator dump`（Android）；仅像素（iOS） |
| 原生 Android / 跨平台 | `mobile-mcp` MCP | `mobile_take_screenshot` | `mobile_list_elements_on_screen` |
| 任意技术栈，无可用 MCP | **CLI 快照 harness** | `mobile-snapshot.sh capture …` | `adb uiautomator dump`（Android）；仅像素（iOS） |

完整规则与平局判定：[`backend-detection.md`](skills/ux-ui-builder-mobile/references/backend-detection.md)。

## 提交门禁

`PreToolUse` 钩子会在每次 `Bash` 调用前运行 `ui-commit-gate.sh`。它会：

1. 放行任何不是 `git commit` 的操作（快速路径）。
2. 放行没有暂存 UI 文件的提交。
3. 对于 UI 提交，计算暂存 UI diff 的 sha256，并查找带有 `verdict: APPROVED` 的 `.ux-ui/approvals/<hash>.json`。
4. 找到 → 放行。否则 → **exit 2**，拦截提交，并提示你运行该循环。

由于批准绑定在 diff 哈希上，之后任何 UI 修改都会让它失效——门禁无法伪造，也永远不会过期。Web 与移动端 UI 共用同一个门禁。

可通过环境变量 `UX_UI_GLOBS` 覆盖哪些文件算作 UI。产物存放在 `.ux-ui/` 下；如果不想提交它们，把它加入 `.gitignore` 即可。

## FAQ

**为什么不直接让模型目测一下自己截的图？**
因为“截过一次图”算不上一种纪律。这个插件*强制要求*完整的 state × breakpoint 矩阵、a11y 快照以及控制台/网络/Lighthouse 信号，然后在独立的艺术总监智能体认可这些产物之前拦截提交。靠的是强制执行，而不是感觉。

**这是把浏览器自动化重新做成了一个自定义 MCP 吗？**
不是。浏览器自动化已经有现成的 `chrome-devtools-mcp`，本插件直接内置了它（移动端 MCP 同理）。本插件增加的价值在于*编排与强制执行*——measure → critique → iterate → gate——这部分由技能 + 智能体 + 钩子实现，因为 MCP 服务器无法启动 Claude Code 子智能体，也无法驱动评审循环。

**为什么要艺术总监，而不是直接让主模型来评审？**
为了分离。负责构建的智能体对自己的作品有感情投入；一个全新的智能体只看实测产物、也无法修改代码，能抓住构建者自我合理化放过的问题。这和设计工作室要设评审环节是同一个道理。

**它会拦截我的后端提交吗？**
不会。门禁只对 UI 文件类型触发，并且特意排除了单纯的 `.ts`/`.js`/`.java` 以及非布局的 `.xml`。纯后端提交会原样通过。

**可以批准一次之后继续修改吗？**
不可以——这正是关键所在。批准绑定在暂存 UI diff 的哈希上。哪怕只改一行 UI，哈希也会对不上，于是门禁会再次拦截，直到你重新运行该循环。

**我的移动端技术栈没有能截图的 MCP，怎么办？**
CLI 快照 harness（`mobile-snapshot.sh`）会通过 `simctl`/`adb` 直接从模拟器中捕获真实的 PNG，再由艺术总监评审这些截图。它唯一绝不会做的，就是评审想象出来的状态。

**如果它连不上开发服务器、Chrome 或已启动的设备呢？**
它会停下来告诉你，而不是退而求其次去评审想象中的状态。环境故障就是硬性停止，这是有意为之的设计。

## 许可证

MIT。详见 [LICENSE](../../LICENSE)。

## 致谢

先实测后评审的做法借鉴了 `frontend-design` 技能（美学方向）和 `chrome-devtools-mcp` 插件（浏览器实测）。硬门禁与 diff 绑定批准的模式沿用了作者在 harness-engineering 工作中的 review-gate 设计。
