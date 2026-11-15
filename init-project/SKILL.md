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

## 功能依赖图谱（docs/feature_map.json + feature_map.html）

每次 init-project 扫描（阶段 C 收尾）必须生成/更新功能依赖图谱，输出到项目 `docs/` 目录（无则创建）。这是硬性交付物，与 `claude/*.md` 同级重要。

### JSON 结构（docs/feature_map.json）

```json
{
  "project": "项目名",
  "description": "一句话说明图谱用途",
  "generated": "YYYY-MM-DD",
  "head_commit": "短 SHA",
  "legend": { "types": "type 枚举说明", "note": "shared 语义说明" },
  "tree": [
    { "id": "world", "name": "世界", "icon": "🌍", "children": [
      { "id": "world.terrain", "name": "地形", "desc": "职责描述",
        "files": [ { "path": "scripts/world/x.gd", "type": "gd", "lines": 123, "role": "源码头部职责注释" } ],
        "tests": [ { "path": "tests/x_contract.gd", "type": "gd", "note": "覆盖点" } ] }
    ]}
  ],
  "vendored": [ { "path": "addons/x", "name": "x", "version": "1.0", "files": 10, "role": "…" } ],
  "unmapped": [ { "path": "…", "reason": "排除原因" } ]
}
```

规则：

- 分类可多层级：`tree[]` 是大类（带 icon），其 `children` 是功能节点；viewer 渲染两级。
- `type` ∈ gd/tscn/shader/config/data/mjs/sh/py/md/dir，按项目语言自适应，viewer 按 type 着色。
- 一个文件可归属多个功能（shared），viewer 自动标 shared 徽章。
- 测试挂在对应功能的 `tests[]`，不单独成类；fixtures 与测试基础设施归 quality/infra 类节点。
- vendored 第三方目录按模块级收录（不展开单文件）；`unmapped` 显式列出排除项与原因。
- `lines` 用真实行数统计；`role` 优先取源码头部职责注释，无则一句话概括。
- 覆盖目标："哪些功能用到哪些文件"全量可查，尽量覆盖所有代码文件。

### 硬性校验（缺一不可，未过不算完成）

全部由 `scripts/feature_map.py check`（`all` 内含）自动执行，不再手写校验代码：

1. **覆盖率 100%**：双向 diff——`git ls-files` 的项目自有代码文件（排除 vendored 与引擎生成物）必须全部出现在 JSON 引用路径里；JSON 里的路径必须全部真实存在，幽灵路径清零。
2. JSON 可被 `json.load` 解析。
3. HTML 注入后：seed 段重新解析通过、与 JSON 文件内容同步、主脚本 `node --check` 0 错误、占位符残留 0。

### HTML 生成与数据维护（内置 python 脚本，禁止手写管线）

viewer 页面与数据刷新统一走本 skill 内置脚本 `scripts/feature_map.py`（单文件、仅标准库），**不逐项目手写 python**——skill 升级（模板/管线变化）后各项目重跑脚本即可同步最新产物：

```
python3 <本 skill 目录>/scripts/feature_map.py scan   --root <项目根>   # 差异报告：新增未归类/消失文件（只读）
python3 <本 skill 目录>/scripts/feature_map.py all    --root <项目根>   # build + render + check 一条龙
# 亦可单独跑 build（机械刷新 lines/gd 头注释 role/时间戳/git 提交、移除消失文件）
#              render（模板注入产物 html）   check（覆盖率双向 diff + 产物同步校验）
```

**职责分工（重要）**：机械部分全归脚本——`.gd` 头部 `## xxx — 职责` 注释提取、行数统计、`git ls-files` 口径的代码文件清单（排除 addons/.claude/.godot）、消失文件清理、`generated`/`head_commit` 刷新、模板双占位符注入（`__JSON_SEED__`/`__VIS_LIB__` 各恰 1 次 + payload 无 `</script` 断言 + seed 重解析 + 主脚本 `node --check`）。**语义部分仍归模型**——功能归属（path → feature）以项目现有 `docs/feature_map.json` 为唯一基准，脚本不自动收编新文件：`scan` 报出未归类清单后，由模型编辑 JSON 把新文件挂到对应功能节点（可 `import feature_map` 复用 `head_role/line_count` 填 lines/role），再跑 `all`。

模板与 vendor：`templates/feature_map.html` + `templates/vendor/vis-network.min.js`（9.1.9，约 476KB，完全离线内嵌，双击 file:// 打开也有知识图谱）。坑（脚本已断言防护）：模板任何注释/文案不得包含 `__JSON_SEED__` 或 `__VIS_LIB__` 字面量，否则占位符计数断言失败。

模板已内置能力：**总览页为交互式知识图谱**（vis-network 内嵌：节点 = 功能（按分类着色、大小=文件数）+ 分类枢纽（菱形）；边 = 分类→功能层级边 + 功能间「共享文件」边；控制条支持分类过滤下拉 / 按分类折叠 / 展开全部 / 适配视野；点功能节点与分类枢纽都在**最右侧第三列**（内容区右缘，默认 560px、`max-width:60vw`）展示完整信息（不离开图谱：分类列 = 统计+功能清单+文件目录树+契约测试表+其他分类 chips；功能列 = 描述+统计+文件目录树+契约测试+同级功能 chips；列内 chips/清单用 `data-dr` 就地切换，↗ 整页打开、✕ 或 Esc 关闭、目录树折叠状态与整页共享；列内目录树行 `width:max-content` + 树容器 `overflow-x:auto` 横向滚动看全名、路径单元格 `word-break:break-all`，其余区域截断不溢出；**列内点击文件不跳转详情页**（图谱不消失），只在本列内高亮该文件约 2.6 秒）；**三列宽度可拖拽调整**：侧栏右缘与第三列左缘各一条 6px `col-resize` 分隔条，拖动实时调宽（侧栏 220–560px、第三列 300–860px，中间内容区弹性填充），松手后按项目前缀持久化到 `localStorage`（`fmCols:<project>`），下次打开自动恢复；双击集群展开；库缺失时自动回退列表总览）；**整页分类详情**：功能视图分类头部的 ↗ 按钮与功能页面包屑里的分类链接打开（`renderCategory`：统计行+功能清单表，chip 可跳功能）；功能视图 / 文件夹目录树视图 / 行数 Top100 排行三视图切换；品牌名取自 JSON `project` 字段（模板不硬编码项目名）；文件夹页内过滤框（快捷键 `/` 聚焦、`Esc` 清除，只过滤当前文件夹树，按路径/职责匹配）；功能详情页文件清单按目录树展示（可折叠）、头部右上角「复制信息」按钮把功能描述+文件清单复制为 JSON；点击任意文件不再进独立文件详情页，而是跳到所属功能页并在目录树里高亮+滚动定位该文件（约 2.6 秒后自动取消高亮）；目录树文件行 hover 出现「⧉ 复制相对路径」与「↗ 新标签打开文件」（`window.open('../'+路径)`，HTML 在 docs/ 下故上一级即仓库根）两个图标；「展开全部」按钮位于功能 tab 内部顶部；按功能名哈希生成的彩色功能徽章（定位放错位置的文件）；覆盖率报告。产物双击可开（数据与库全部内嵌）；经 http 服务打开时自动 fetch 同目录 json 热更新。

### 登记

- `claude/file-map.md` 的 docs 段登记 feature_map.json/.html。
- `claude/changelog.md` 记录图谱生成结果（功能节点数、收录文件数、覆盖率、shared/vendored/unmapped 计数）。

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
- 功能依赖图谱：`docs/feature_map.json` + `feature_map.html` 的功能节点数、收录文件数、覆盖率（应达 100%）、shared/vendored/unmapped 计数。
- 若未读全：说明"为何到此为止"，并列出推荐的下一步，例如"建议优先补扫：packages/auth/src/controllers"。
