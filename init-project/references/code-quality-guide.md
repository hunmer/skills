---
description: "代码质量检查指导：死代码、上帝文件、文件层级的好坏示例。扫描时必须阅读。"
---

# 代码质量指导（Code Quality Guide）

扫描项目并生成 `claude/code-health.md` 时，使用本文件判断什么是好的、什么是坏的。只报告事实依据充分的问题，不编造。

## 1. 死代码（Dead Code）

### 坏的例子

```typescript
// src/utils/legacy.ts
export function calculateOldDiscount(price: number) {  // 从未被 import
  return price * 0.9;
}

export function unusedHelper() { /* ... */ }  // 同文件内也未被调用

// 注释掉的大段旧实现
// function oldFlow() { ... 200 lines ... }

import { unused } from 'lodash';  // 导入后未使用
```

- 未导出且未被同文件调用的函数/类
- 导出但全仓库无 import 的符号（需排除动态引用、反射、入口点）
- 孤儿文件（从未被任何文件引用）
- 未使用的依赖（package.json 中声明但代码未 import）

### 好的例子

```typescript
// src/utils/pricing.ts
export function calculateDiscount(price: number, rate: number) {
  return price * (1 - rate);
}

// 被多个模块 import 使用
// 无未使用导入
// 无注释掉的废弃代码块
```

**检查建议**：
- 优先使用工具输出：`knip`、`ts-prune`、`vulture`、`depcheck`、`staticcheck` 等。
- 对候选结果必须用全仓库 grep 验证（包括字符串动态引用、配置、测试、CI）。
- 公共 API、生成代码、框架约定入口标记为“需人工确认”。
- 一次只报告高置信度项，并建议逐个删除后跑测试。

## 2. 上帝文件（God Files）

### 坏的例子

```typescript
// src/services/OrderService.ts  （1800+ 行）
export class OrderService {
  // HTTP 路由处理
  async handleCreate(req, res) { ... }
  // 业务规则
  validateOrder() { ... }
  // 数据库操作
  async saveToDb() { ... }
  // 邮件通知
  sendEmail() { ... }
  // 工具函数
  formatCurrency() { ... }
  // 还有 10 个不相关方法...
}
```

特征：
- 文件 > 800–1000 行
- 混合多种职责（处理请求 + 业务逻辑 + 持久化 + 工具 + 通知）
- 难以测试、难以复用、改一处影响多处

### 好的例子

```text
src/features/order/
  ├── types.ts          // 领域类型
  ├── order.service.ts  // 纯业务逻辑（<300 行）
  ├── order.repository.ts
  ├── order.controller.ts
  ├── order.validator.ts
  └── index.ts          // 统一导出
```

**拆分原则**：
- 按职责（cohesion）拆，不按行数硬切。
- 先提取共享类型和纯函数到叶子模块。
- 一次移动一个职责簇，保持原文件可作临时 re-export。
- 目标：每个文件单一职责、可独立测试。

## 3. 文件层级与目录结构

### 坏的例子

```text
src/
  ├── utils.ts          // 什么都往里扔
  ├── helpers.ts
  ├── stuff.ts
  ├── auth-login.ts
  ├── auth-register.ts
  ├── payment.ts
  ├── order-create.ts
  ├── order-cancel.ts
  └── components/
      ├── Button.tsx
      ├── UserProfile.tsx
      ├── PaymentForm.tsx   // 混合了页面级与通用组件
```

问题：
- 过度扁平，职责边界不清
- 相关文件散落各处（shotgun surgery）
- 通用工具与业务逻辑混放
- 缺乏清晰的模块/功能边界

### 好的例子

```text
src/
  ├── features/
  │   ├── auth/
  │   │   ├── components/
  │   │   ├── hooks/
  │   │   ├── services/
  │   │   └── index.ts
  │   └── orders/
  ├── shared/
  │   ├── components/     // 真正通用的 UI
  │   ├── utils/
  │   └── types/
  └── app/                // 入口、路由、全局配置
```

**检查要点**：
- 是否存在明确的功能/领域边界？
- 相关文件是否聚集在一起？
- 是否有过度深层嵌套（>4–5 层）？
- 是否有“万能 utils”目录？
- 模块间依赖方向是否合理（避免循环）？

## 报告格式建议（写入 code-health.md）

```markdown
# 代码健康检查

## 死代码候选
| 位置 | 类型 | 置信度 | 说明 | 建议 |
|------|------|--------|------|------|
| src/utils/legacy.ts:12 | unused-export | 高 | calculateOldDiscount 无任何引用 | 确认后删除 |

## 上帝文件
| 文件 | 行数 | 混合职责 | 建议拆分方向 |
|------|------|----------|--------------|
| src/services/OrderService.ts | 1820 | HTTP + 业务 + DB + 邮件 | 拆成 controller / service / repository |

## 文件层级问题
- src/ 过度扁平，auth 与 order 相关文件混在一起。
- 建议按 features/ 重新组织。

## 下一步建议
1. 优先处理高置信度死代码。
2. 选择最大的上帝文件进行试点拆分。
```

扫描时优先报告影响最大的问题，并在 CLAUDE.md 索引中给出简短提示。
