---
name: init-project
description: "初始化项目 AI 上下文，生成/更新轻量 CLAUDE.md 索引与分文件详情"
---

## 目标

以"CLAUDE.md 只做索引，细节写入同目录 claude/ 子目录"的策略初始化项目 AI 上下文。

必须避免把所有分析内容塞进单个 `CLAUDE.md`。`packages/web/CLAUDE.md` 这类长文档只能作为需要拆分的反例参考：其中的"模块职责、入口与启动、对外接口、依赖与配置、数据模型、测试与质量、FAQ、相关文件清单、变更记录"等内容，都应拆成独立 Markdown 文件。

## 文档结构

对仓库根目录和每个识别出的模块目录，生成/更新以下结构：

```text
<target>/
  CLAUDE.md
  claude/
    overview.md
    conventions.md
    module-responsibilities.md
    entrypoints.md
    public-interfaces.md
    dependencies-and-config.md
    data-model.md
    testing-and-quality.md
    file-map.md
    faq.md
    changelog.md
```

说明：

- `<target>/CLAUDE.md` 是索引文件，只保留当前目录最重要的导航信息。
- `<target>/claude/*.md` 是详情文件，承载原本会写进 `CLAUDE.md` 的长内容。
- 如果某个章节没有事实依据，不要编造；可省略对应详情文件，或在索引中标记"未扫描/未发现"。
- 文件名使用小写 kebab-case，便于跨平台和链接稳定。

## CLAUDE.md 内容规范

每份 `CLAUDE.md` 必须按以下顺序组织，且保持简洁：

1. **项目简单介绍**
   - 1 到 3 段，说明该目录/模块是什么、解决什么问题、关键技术栈。
   - 只写摘要，不展开组件清单、接口细节或依赖表。

2. **约定的规则**
   - 列出对 Agent 最有用的工作约定，例如启动命令、测试命令、设计规范、禁止事项、重要兼容性提醒。
   - 规则应短句化，避免把 FAQ 或长解释混入此处。
   - 如规则较多，`CLAUDE.md` 只保留高优先级规则，并链接 `claude/conventions.md`。

3. **文件索引**
   - 用表格列出 `claude/` 下的详情文件。
   - 每行包含：文件、用途、何时阅读。
   - 链接必须使用相对路径，例如 `[入口与启动](claude/entrypoints.md)`。

4. **模块索引**（仅根目录或聚合目录需要）
   - 列出识别出的模块路径、职责摘要、对应 `CLAUDE.md` 链接。
   - 可包含 Mermaid 结构图，但结构图必须简短，只表达模块关系，不承载详情。

5. **扫描状态**
   - 记录更新时间、已扫描范围、跳过范围、下一步建议。

`CLAUDE.md` 不应包含大段表格、完整 API 列表、完整组件清单、完整 Store 列表或 FAQ 全量内容；这些内容必须进入 `claude/*.md`。

## 详情文件职责

- `claude/overview.md`：架构总览、边界、运行时形态、重要设计取舍。
- `claude/conventions.md`：开发约定、命令、代码风格、设计规范、注意事项。
- `claude/module-responsibilities.md`：模块职责、核心能力、子域划分。
- `claude/entrypoints.md`：入口文件、启动流程、构建流程、运行时初始化。
- `claude/public-interfaces.md`：页面路由、REST API、WebSocket、SDK、CLI 或对外暴露的接口。
- `claude/dependencies-and-config.md`：关键依赖、配置文件、环境变量、框架版本差异。
- `claude/data-model.md`：领域模型、状态管理、数据库表、缓存、消息结构。
- `claude/testing-and-quality.md`：测试命令、覆盖情况、Lint/类型检查、质量风险。
- `claude/file-map.md`：重要目录和关键文件清单。
- `claude/faq.md`：常见问题及定位路径。
- `claude/changelog.md`：本次索引生成/更新记录，避免和产品 Changelog 混用；只保留最近 5 条记录，新增记录后删除更早记录。

## 执行策略（由 Agent 自适应决定，不需要用户传参）

- **阶段 A：全仓清点（轻量）**
  快速统计文件与目录，识别模块根（`package.json`、`pyproject.toml`、`go.mod`、`apps/*`、`packages/*`、`services/*` 等）。
- **阶段 B：模块优先扫描（中等）**
  对每个模块做"入口/接口/依赖/测试/数据模型/质量工具"的定点读取与样本抽取。
- **阶段 C：详情拆分写入**
  先写详情文件，再写索引文件，确保 `CLAUDE.md` 中的链接都能落到真实文件。
- **阶段 D：覆盖率度量与可续跑**
  输出"已扫描文件数 / 估算总文件数、已覆盖模块占比、被忽略/跳过原因"，并列出"建议下一步深挖的子路径"。重复运行 `/init-project` 时按上次索引做增量更新与断点续扫。
  更新 `claude/changelog.md` 时必须按时间倒序保留最近 5 条记录，不得无限追加。

## 安全与边界

- 只读/写文档与索引，不改源代码。
- 默认忽略常见生成物与二进制大文件。
- 不主动执行 git 提交、分支、reset、checkout 等操作。
- 结果在主对话打印摘要，全文写入仓库。

## 输出要求

在主对话中打印"初始化结果摘要"，包含：

- 根级 `CLAUDE.md` 是否创建/更新，以及它是否保持为轻量索引。
- 识别的模块数量及其路径列表。
- 每个目标目录生成/更新的 `CLAUDE.md` 与 `claude/*.md` 文件列表。
- 已生成的文件索引数量、模块索引数量，以及是否生成 Mermaid 结构图。
- 覆盖率与主要缺口。
- 若未读全：说明"为何到此为止"，并列出推荐的下一步，例如"建议优先补扫：packages/auth/src/controllers"。
