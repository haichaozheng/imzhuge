# API Key 获取与配置引导

Key 未配置时向用户输出的完整引导模板（SKILL.md 第三节引用）。
与 api-reference.md 附录"环境变量"章节同源，修改时两处同步。

## 引导模板（参照 Tushare 风格）

检测到 `IMZHUGE_API_KEY` 缺失时，**停止一切 API 调用**，向用户输出：

```markdown
⚠️ 未检测到 IMZHUGE_API_KEY，无法调用嗨皮诸葛平台 API。

按以下步骤获取并配置（约 1 分钟）：

【第 1 步】登录网页端生成 Key（需人工操作，无法自动化）
  → https://m.imzhuge.com → 登录 → 个人中心 → API Key → 生成
  → 得到 pm_ 开头的字符串，形如 pm_XXXXXXXX_XXXXXXXX

【第 2 步】设置为环境变量（切勿粘贴进对话！）

  # macOS / Linux（当前 shell 生效）
  export IMZHUGE_API_KEY="pm_你的key"

  # Windows PowerShell（当前终端生效）
  $env:IMZHUGE_API_KEY = "pm_你的key"

  # Windows 永久生效（新开的终端自动继承）
  setx IMZHUGE_API_KEY "pm_你的key"

【第 3 步】告诉我"已设置"，我会验证连通性后继续

🔒 安全提醒：这把 Key 可以交易你的积分/诸葛贝。只在环境变量中设置，
不要粘贴到对话、代码、截图或笔记里。怀疑泄露立即去网页端轮换。

> 💡 开发者选项（普通用户无需设置）：本地联调嗨皮诸葛后端时，
> 另设 `IMZHUGE_BASE_URL=http://127.0.0.1:8000`（需本地运行服务），
> 其余情况一律使用默认的正式服务器。
```

## 生成入口

https://m.imzhuge.com → 登录 → 个人中心 → API Key（必须人工网页操作，无法自动化）。
