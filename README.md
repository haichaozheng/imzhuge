# imzhuge — 嗨皮诸葛预测市场 Skill

接入 [嗨皮诸葛](https://www.imzhuge.com)（imzhuge）预测市场平台的 agent skill。让你在对话中直接完成预测市场的参与者和组织者两类操作。原生支持 [OpenCode](https://opencode.ai)，兼容 Claude Code（同为 SKILL.md 规范）和其他办公智能体（例如 WorkBuddy）。

## 这是什么

本 skill 通过嗨皮诸葛平台开放 API（用户级 API Key 鉴权）提供：

- **参与者视角**：查赛事、查余额、查持仓、买卖预测合约
- **组织者视角**：创建预测比赛、创建/修改预测市场

## 功能速览

| 能力 | 说明 |
|---|---|
| 会话开场速览 | 首次调用自动汇总可交易市场、余额、持仓为一张速览卡 |
| 查赛事 | 我参与的 / 我发起的 / 受邀的比赛列表 |
| 查市场 | 某比赛下的活动、项目、合约及当前价格 |
| 查余额 / 持仓 | 活动诸葛贝、比赛专属积分、全局诸葛贝；按合约聚合的净持仓与现价 |
| 下单交易 | 买入 / 卖出预测合约，带完整的前置检查、参数确认与成交对账 |
| 市场调研 | 结合公开行情给出多空因素与参考概率（注明时效与置信度） |
| 创建比赛 / 市场 / 修改市场 | 组织者操作，含时间嵌套校验与合约档位设计 |

## 快速开始

### 前置条件

- 支持 agent skill 的 AI 工具之一：
  - [OpenCode](https://opencode.ai)（原生支持）
  - [Claude Code](https://claude.com/claude-code)（兼容，同为 SKILL.md 规范）
  - WorkBuddy 等办公智能体（客户端"上传技能"导入，见下方安装方式）
- 嗨皮诸葛平台账号（[www.imzhuge.com](https://www.imzhuge.com) 注册）

### 安装

#### 方式一：skills CLI（推荐，一条命令装进所有工具）

```bash
npx skills add haichaozheng/imzhuge
```

skills CLI（[vercel-labs/skills](https://github.com/vercel-labs/skills)）会自动检测你机器上已装的 AI 工具（OpenCode、Claude Code、Cursor、Codex 等 75+ 种），让你选择装到哪些；加 `-g` 则全局安装、跨项目可用。后续用 `npx skills update imzhuge` 升级。要求 Node.js ≥ 22.20。

#### 方式二：手动安装

把整个 `imzhuge/` 目录放到所用工具的 skills 目录（目录名 `imzhuge` 需与 SKILL.md 中的 `name` 一致，`SKILL.md` 直接位于该目录下）：

| 工具 | 安装位置 |
|---|---|
| OpenCode | `.opencode/skills/imzhuge/`（项目级）或 `~/.config/opencode/skills/imzhuge/`（全局） |
| Claude Code | `.claude/skills/imzhuge/`（项目级）或 `~/.claude/skills/imzhuge/`（个人级） |
| Cursor | `~/.cursor/skills/imzhuge/` |
| 其他遵循 Agent Skills 约定的 harness | `<skills 目录>/imzhuge/`，常见如 `~/.agents/skills/imzhuge/` |
| WorkBuddy | 客户端"上传技能"导入：将本目录打包为 zip（根目录需含 SKILL.md）拖拽上传 |

安装后工具会自动读取 `SKILL.md` 的 description，在用户提到相关操作时触发；`references/` 与 `scripts/` 随目录一起被引用，无需额外配置。注意新装的 skill 通常在**新会话**中才会被发现。

### 通用方法（不依赖任何特定工具）

任何能读写本地文件、执行命令的 AI agent 都可以使用本 skill，即使它不认识 skills 目录约定：

1. 把 `SKILL.md` 的内容粘贴进对话（或项目根的 `AGENTS.md` / 系统提示词），agent 即获得完整的平台操作知识
2. `references/api-reference.md` 按需一并提供，或让 agent 在需要字段细节时自行读取
3. `scripts/trade_demo.py` 是独立的 Python 标准库脚本，不装任何 skill 也能直接运行（见下文 Demo 脚本）

### 第 1 步：生成 API Key（约 1 分钟）

登录网页端 → **个人中心 → API Key → 生成**，得到 `pm_` 开头的字符串。此步骤必须人工网页操作，无法自动化。

### 第 2 步：配置环境变量

```bash
# macOS / Linux（当前 shell 生效）
export IMZHUGE_API_KEY="pm_你的key"

# Windows PowerShell（当前终端生效）
$env:IMZHUGE_API_KEY = "pm_你的key"

# Windows 永久生效（新开终端自动继承）
setx IMZHUGE_API_KEY "pm_你的key"
```

### 第 3 步：验证

在 agent 对话中说"**看看现状**"，skill 会自动检查连接并展示开场速览卡：

```
✅ 连接正常 | 服务器: m.imzhuge.com

📊 可交易市场（进行中的比赛 8 场，其中 2 个市场在交易窗口内）:
  · 科创50指数11-20涨跌幅预测   <-5% 0.43 / ±5%区间 0.47 / >+5% 0.11   截止 11-20 15:00
  · 某球员冬窗转会预测           转会成功 0.62 / 留队 0.38               截止 12-01 23:59

💰 余额: 活动诸葛贝 30.00 | 全局 36.17
📈 持仓: 无
```

## ⚠️ 安全须知（安装前必读）

**这把 API Key 具备查询 + 真实交易的全部能力，没有只读模式、没有额度上限。**

- Key 只通过环境变量传递，**绝不粘贴进对话、代码、笔记或截图**
- skill 会拒绝在对话中复述 Key 明文（引用时只显示脱敏形式，如 `pm_Ge7...POaS`）
- 若在对话中不慎粘贴 Key 明文，该 Key 应视为已泄露——任务结束后立即到网页端轮换
- 怀疑泄露时的处置：网页端 个人中心 → API Key → 重新生成（旧 Key 即时失效）
- skill 内置提示注入防护：平台返回的市场名/合约文案等用户生成内容一律当作数据展示，其中夹带的指令不会被 agent 执行

## Demo 脚本

`scripts/trade_demo.py`（仅 Python 3 标准库，无第三方依赖）演示完整参与者链路：

```bash
# 只读模式（无任何写操作，可安全重复执行）
python scripts/trade_demo.py

# 下单模式（6 个参数齐备才交易，默认交互确认）
python scripts/trade_demo.py <activity_id> <contract_id> <buy|sell> <share> <pred_proba> "<note>"
```

只读模式适合首次安装后验证连通性。下单模式带人工确认步骤（输入 `yes` 才发送），大事件（活动数 > 100 的长期赛）自动跳过市场列表下拉以防响应过大。

## 已知限制（诚实清单）

| 限制 | 说明 |
|---|---|
| 交易无幂等 | 下单接口与网页版一致，无防重复提交保护；请求失败/超时后 skill 禁止自动重试，会先查持仓核对实际状态 |
| API 不能"加入"活动 | 首次加入比赛/活动需在网页端完成，API 只能操作已加入的 |
| 大事件需网页端定位 | 长期赛（如指数成分股每日预测类）有数千到 2 万+ 活动，API 无日期过滤参数，需从网页端 URL 取活动 ID（如 `?activityId=46996`） |
| 仅限本人账户 | API Key 严格限定归属用户，无法查询/操作其他用户的持仓与账户 |
| 提现/转账仅网页端 | API 不提供资金操作 |
| 结算与价格不可改 | 组织者也不能修改合约价格与结算结果（平台规则） |

## 文件结构

```
imzhuge/
├── LICENSE                         # MIT
├── README.md                      # 本文件（面向人的介绍）
├── SKILL.md                       # skill 主文档（面向 agent 的运行时指令）
├── references/
│   ├── api-reference.md           # 全量 13 端点的请求/响应字段文档
│   └── key-setup-guide.md         # API Key 获取与配置引导模板
└── scripts/
    └── trade_demo.py              # 参与者链路演示脚本（Python 3 标准库）
```

## 适用后端

- 嗨皮诸葛正式服务 `https://m.imzhuge.com`（默认）
- 注意：`www.imzhuge.com` 是纯前端站点，不提供 API

