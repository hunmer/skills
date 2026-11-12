---
name: x_web_search
description: "通过本机已登录的 Grok CLI（headless 模式）进行实时网页搜索，返回带来源链接的中文摘要。需要时效性信息、新闻、最新事件时使用。"
---

# x_web_search — 通过 Grok CLI 进行网页搜索

## 用途
当需要实时网页搜索（新闻、最新事件、时效性信息）时，使用本机已登录的 Grok CLI headless 模式执行搜索并获取带来源链接的中文摘要。

## 前置条件
- Grok CLI 已安装并登录：`~/.grok/bin/grok`（`grok --version` 可验证）
- **必须走本机代理 `http://127.0.0.1:7890`**，否则请求会卡死直到超时

## 调用方式

首选：直接用现成脚本（已验证可用）：

```bash
python3 /Users/Zhuanz/grok_web_search.py "搜索关键词"
```

返回 JSON：`{"answer": "<带来源链接的中文摘要>", "session_id": "..."}`。

或在 bash 中直接调用 CLI（等价）：

```bash
export http_proxy=http://127.0.0.1:7890 https_proxy=http://127.0.0.1:7890 all_proxy=http://127.0.0.1:7890
~/.grok/bin/grok -p "使用网页搜索工具搜索：<关键词>，并用中文总结要点（附来源链接）" \
  --always-approve \
  --output-format json \
  --permission-mode bypassPermissions \
  < /dev/null
```

## 关键参数
- `-p`：单次提示（headless），必须重定向 `< /dev/null` 避免 TUI 等待输入
- `--always-approve`：自动批准 web_search 等工具调用
- `--output-format json`：结构化输出，取 `text` 字段为回答正文
- `-m <model>`：可选，指定模型
- 超时给足：搜索类请求建议 ≥ 300 秒

## 注意
- 不加代理环境变量时 grok 会无输出挂起直到超时——这是最常见的失败原因
- 单次搜索成本约 $0.04，别对琐碎问题滥用
- 输出内容由模型基于搜索结果生成，引用来源前如需核实请打开链接确认
