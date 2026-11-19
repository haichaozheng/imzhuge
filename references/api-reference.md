# 嗨皮诸葛 Open API 参考（全量 13 端点）

- **Base URL**：`${IMZHUGE_BASE_URL:-https://m.imzhuge.com}/startactivity/api/open`（正式服务器；本地联调设 `IMZHUGE_BASE_URL=http://127.0.0.1:8000`）
- **鉴权**：所有请求必须带 `X-API-Key: pm_前缀8位_密文` header（session/cookie 无效）
- **响应格式**：`{"status": "success|error|warning", "message": "...", "data": ...}`，UTF-8，中文不转义
- **时间格式**：naive `YYYY-MM-DDTHH:MM`（Asia/Shanghai，无时区后缀）
- **URL 规则**：所有路径带尾部斜杠（历史配置 APPEND_SLASH=False；实测 2026-11 服务端对缺斜杠已宽容返回 200，仍统一带斜杠以兼容严格模式环境）
- **HTTP 状态**：200（业务响应含 error/warning）、401（鉴权失败）、403（权限）、404（实体不存在）、405（方法不允许）、429（限流）
- **限流**：2026-11-03 起，所有端点按 API Key 归属用户限流 **60 次/分钟**（固定窗口，Redis 计数）。超限返回 429 + `Retry-After` 头 + `{"status": "error", "message": "请求过于频繁，请稍后重试"}`。**429 意味着请求被拦截、业务未执行——等待后可安全重试，不会重复成交**（与超时不同：超时结果未知，禁止重试）。Redis 故障时限流自动失效放行（fail-open）

---

## 目录

**组织者（管理比赛/市场）**
1. [GET event_group_options/](#1-比赛+小组列表)
2. [POST create_event/](#2-创建比赛)
3. [POST create_activity_pros/](#3-创建市场活动项目合约)
4. [POST update_activity_pros/](#4-更新市场字段)
5. [GET activity_list/](#5-指定比赛小组的市场列表组织者视角)
6. [GET project_contracts/](#6-项目合约列表)
7. [GET my_events/](#7-我发起的比赛列表)
8. [GET my_event_detail/](#8-比赛详情含统计)

**参与者（查询/交易）**
9. [GET my_participated_events/](#9-我参与的含受邀比赛列表)
10. [GET my_event_markets/](#10-我有权查看的比赛市场详情)
11. [GET my_balance/](#11-我在指定活动的余额)
12. [GET my_holdings/](#12-我在指定活动的持仓)
13. [POST trade_confirm/](#13-下单交易)

---

## 1. 比赛+小组列表

`GET /event_group_options/?status=all|ongoing|ended`

返回当前 Key 用户**可管理**的比赛（非管理员仅 owner 是自己的）。用于创建市场前拿 event_id/group_id。

**响应 data**：数组，每项：

```json
{
  "id": 121, "name": "上证50成分股5日股价涨跌预测",
  "start_time": "2026-11-03T00:00", "end_time": "2026-11-10T23:59",
  "status": "进行中",              // 未开始/进行中/已结束/时间未设置
  "groups": [{"id": 132, "name": "默认小组"}]
}
```

- `status=ongoing`：进行中+未开始+时间未设置；`status=ended`：已结束；`all`（默认）不过滤

## 2. 创建比赛

`POST /create_event/`

**请求体**：

```json
{
  "event": {
    "name": "比赛名",                    // 必填非空
    "start_time": "2026-11-03T00:00",    // 必填
    "end_time": "2026-11-10T23:59",      // 必填，须晚于 start_time
    "group_count": 1,                    // 必填整数
    "award": 100,                        // 必填整数
    "is_special": false,                 // 必填布尔；true=特邀赛（白名单准入）
    "event_type": "",                    // 必填键，可为空串
    "is_PointsSegregated": 0,            // 可选；1=积分隔离赛
    "coin_event": 100                    // 隔离赛必填，1~999（专属积分初始发放额）
  },
  "group": {
    "name": "小组名",                    // 必填非空
    "desc": "比赛简介",                  // 必填非空，≤1000字
    "award": 100,                        // 必填键（整数）
    "group_type": "experiment"           // 可选，默认 "experiment"
  }
}
```

**规则**：非管理员只能创建 `is_special: true` 的特邀赛。事务原子（EventList + EventGroup 同建）。

**响应 data**：`{"event_id": 121, "group_id": 132}`

## 3. 创建市场（活动→项目→合约）

`POST /create_activity_pros/`

**请求体**：

```json
{
  "event_id": 121, "group_id": 132,
  "activities": [{
    "name": "上证指数11月5日涨跌预测",
    "description": "...",
    "start_date": "2026-11-03T00:00",    // 须落在 event 时间范围内
    "end_date": "2026-11-08T23:59",
    "has_award": false,                  // 可选
    "award": 0,                          // 可选
    "start_from": 0,                     // 可选
    "status": 1,                         // 可选；缺省按时间自动派生：未开始0/进行中1/已结束2
    "can_trade": true,                   // 可选，默认 true（是否通过预热可交易）
    "stock_id": null,                    // 可选
    "label": "",                         // 可选
    "projects": [{
      "title": "上证指数2026-11-05收盘涨跌预测",
      "desc": "...",
      "start_time": "2026-11-03T00:00",  // 须落在 activity 时间范围内（交易时间窗！）
      "end_time": "2026-11-06T23:59",
      "contract_num": 2,                 // 可选
      "is_finished": false,              // 可选
      "contracts": [
        {"contract_text": "上涨"},
        {"contract_text": "下跌"}
      ]
    }]
  }]
}
```

**规则**：事务原子；合约初始价自动 = `round(1/合约数, 8)`（2 合约 → 0.5）。权限：仅比赛发起人/管理员。积分隔离赛创建成功后自动给发起人发放 coin_event 专属积分。

**响应 data**：`{"event_id": 121, "group_id": 132, "activity_ids": [46994]}`

## 4. 更新市场字段

`POST /update_activity_pros/`

按 `event_id + group_id + activity_id` 定位，**部分更新**（只改 payload 中出现的字段）。

```json
{
  "event_id": 121, "group_id": 132, "activity_id": 46994,
  "activity": {"can_trade": false, "name": "新活动名"},
  "projects": [
    {"id": 47287, "end_time": "2026-11-06T15:00", "title": "新标题"},
    {"id": 47288, "contracts": [{"id": 95290, "contract_text": "新文案"}]}
  ]
}
```

**可改字段**：
- activity：`name / description / start_date / end_date / has_award / award / start_from / status / can_trade / is_show / label / stock_id`
- project：`title / desc / start_time / end_time / contract_num / is_finished / has_update_account`
- contract：**仅** `contract_text`（`origin_price / update_price / contract_is_true` 禁止改，返回 error）

**时间约束**：改动后的时间仍须满足 event ⊇ activity ⊇ project 嵌套。

**响应 data**：`{"updated_project_ids": [...], "updated_contract_ids": [...]}`

## 5. 指定比赛+小组的市场列表（组织者视角）

`GET /activity_list/?event_id=121&group_id=132`

权限：仅比赛发起人/管理员。返回该 event+group 下全部活动，结构与 my_event_markets 的 activities 相同（含 projects/contracts、origin_price/update_price/contract_is_true）。

## 6. 项目合约列表

`GET /project_contracts/?project_id=47287`

权限：比赛发起人/管理员（活动归属比赛时）。**响应 data**：

```json
{"project_id": 47287, "contracts": [
  {"id": 95290, "contract_text": "上涨", "contract_is_true": false}
]}
```

## 7. 我发起的比赛列表

`GET /my_events/`

返回当前用户 owner 的全部比赛。每项含 id/name/start_time/end_time/award/status/event_type/is_special/group_count 等。

## 8. 比赛详情（含统计）

`GET /my_event_detail/?event_id=121`

权限：发起人/管理员。返回 event 元信息 + activities（含 projects/contracts）+ statistics（participant_total/trade_total/activity_total/project_total/finished_projects/pending_projects）。

## 9. 我参与的（含受邀）比赛列表

`GET /my_participated_events/`

**参与者视角核心发现端点**。返回"与我有关"的三类比赛：
- `joined: true`：已加入（UserGroup 有记录）
- `joined: false` + 在列表中：被邀请（特邀赛白名单命中）或自己发起（is_owner: true），尚未加入

**响应 data**（数组）：

```json
{
  "id": 21, "name": "上证50成分股5日股价涨跌预测",
  "start_time": "2024-06-06T09:00", "end_time": "2044-04-20T09:00",
  "award": 1000, "status": "进行中",
  "event_type": "", "is_owner": false, "joined": true,
  "is_PointsSegregated": 0, "coin_event": null,
  "is_special": false,
  "group_count": 1, "activity_count": 10
}
```

## 10. 我有权查看的比赛市场详情

`GET /my_event_markets/?event_id=121`

权限：管理员 / 比赛发起人 / 已加入该比赛（UserGroup）。未参与返回 403。

**响应 data**：

```json
{
  "event": {"id": 121, "name": "...", "status": "进行中",
            "is_PointsSegregated": 0, "coin_event": null,
            "start_time": "...", "end_time": "..."},
  "activities": [{
    "id": 46994, "name": "...", "description": "...",
    "start_date": "...", "end_date": "...",
    "status": 1, "status_label": "进行中",
    "can_trade": true, "is_show": true,
    "has_award": 0, "award": 0, "group_id": 132,
    "projects": [{
      "id": 47287, "title": "...", "desc": "...",
      "start_time": "2026-11-03T00:00", "end_time": "2026-11-06T23:59",
      "is_finished": false,
      "contracts": [
        {"id": 95290, "contract_text": "上涨",
         "origin_price": 0.5, "update_price": 0.5, "contract_is_true": false},
        {"id": 95291, "contract_text": "下跌",
         "origin_price": 0.5, "update_price": 0.5, "contract_is_true": false}
      ]
    }]
  }]
}
```

**status 枚举**（activity.status）：`0` 未开始 / `1` 进行中 / `2` 已结束。

## 11. 我在指定活动的余额

`GET /my_balance/?activity_id=46994`

**响应 data**：

```json
{
  "activity_id": 46994, "event_id": 121,
  "is_points_segregated": 0,        // 1=积分隔离赛
  "group_id": null,                 // event 类市场恒为 null（正常形态）
  "joined": true,
  "balance": 30.0,                  // 活动诸葛贝；隔离赛时为比赛专属积分
  "coin_event": 100.0,              // 仅隔离赛返回
  "balance_label": "本比赛专属积分",   // 仅隔离赛返回
  "total_money": 36.17              // 全局诸葛贝（User.money）
}
```

- 未加入：`status: "warning"`，message="您尚未加入该活动，暂无余额"（隔离赛文案不同），data 中 balance=0
- **口径**：隔离赛读 `EventUserAccount.money`（不联动全局）；通用赛读 `ActivityUserAccount.money`（交易联动 total_money）

## 12. 我在指定活动的持仓

`GET /my_holdings/?activity_id=46994`

**响应 data**：余额摘要（同 my_balance）+ `projects` 数组：

```json
{
  "activity_id": 46994, "...": "（余额字段同 my_balance）",
  "projects": [{
    "id": 47287, "title": "...",
    "start_time": "...", "end_time": "...", "is_finished": false,
    "contracts": [
      {"id": 95290, "contract_text": "上涨",
       "current_price": 0.50125,      // 做市商当前价（含本组历史成交影响）
       "holding_share": 1,            // 净持仓（买-卖）
       "contract_is_true": false},
      {"id": 95291, "contract_text": "下跌",
       "current_price": 0.49875, "holding_share": 0, "contract_is_true": false}
    ]
  }]
}
```

## 13. 下单交易

`POST /trade_confirm/`

**请求体**（JSON）：

```json
{
  "activity_id": 46994,          // 必填整数
  "project_id": 47287,           // 必填整数
  "contract_id": 95290,          // 必填整数（须属于该 project）
  "action": "buy",               // 必填 "buy" | "sell"
  "share": 1,                    // 必填正整数（不可 0/负/"01" 前导零）
  "note": "看好指数上涨，因此买入一份",  // 必填，>5 个字且 ≤1000 字（UTF-8 字符数）
  "pred_proba": 0.6,             // 必填数值，用户预测概率
  "confidence": "很有信心"        // 必填四选一：完全瞎猜/有点瞎猜/有点信心/很有信心
}
```

**校验链**（与网页版 trade_confirm 语义一致，顺序大致为）：

| # | 校验 | 失败文案 |
|---|---|---|
| 1 | activity/project/contract 存在且归属正确 | 404 各自文案 |
| 2 | 特邀赛白名单（is_special） | "您不在当前活动的邀请名单"（403） |
| 3 | 已加入（通用赛须有活动账户；隔离赛须已获专属积分） | "您尚未加入该活动/比赛…请先在网页端加入" |
| 4 | share 正整数 | "交易份额格式出错，请填写正整数。" |
| 5 | note >5 字 / pred_proba 数值 / confidence 四选一 | 各自中文文案 |
| 6 | 卖出不得超持仓 | "卖出的份额超于拥有的份额！" |
| 7 | project 时间窗（start_time ≤ now ≤ end_time） | "不在交易时间内！" |
| 8 | 余额足够（act_new_money ≥ 0） | "您的余额不足！" |
| 9 | 活动预热 can_trade | "活动没有通过预热无法交易" |

**账务语义**（与网页版一致）：
- 通用赛：`ActivityUserAccount.money += payoff`，`User.money += payoff`，写 UserAccount 双流水（ACT_PROJECT_SUCESS_EARNINGS 初始化 + ACT_TRADE 交易流水）
- 积分隔离赛：`BalanceAccount.update_balance` → `EventUserAccount.money += payoff` + `EventUserAccountLog` 流水；**不动 User.money**
- 每笔成交写 Trade + 2 条 AutoMarketMaker（首次成交额外 1 条初始化），并更新 ProjectContracts.update_price（LMSR 定价）

**成功响应 data**：

```json
{
  "trade_id": 594212, "action": "buy", "share": 1,
  "activity_id": 46994, "project_id": 47287, "contract_id": 95290,
  "contract_text": "上涨",
  "price": 0.5,                    // 本笔成交价（成交前市价）
  "payoff": -0.50062,              // 买为负（花费），卖为正（收入）
  "updated_prices": {"95290": 0.50125, "95291": 0.49875},
  "balance_after": 29.49938,       // 活动账户/专属积分余额
  "total_money_after": 35.66918,   // 全局诸葛贝（隔离赛不变）
  "is_points_segregated": 0,
  "trade_time": "2026-11-03T11:06"
}
```

**⚠️ 无幂等保护**：与网页版一致。同一请求重复提交 = 重复成交。调用方（agent/脚本）**禁止对失败/超时请求自动重试**；应先查 my_holdings / my_balance 确认实际状态。

**并发**：atomic 块内对 Project 行 `select_for_update()`，API-vs-API 并发下单串行化；与网页版共存不阻塞（网页路径为 MVCC 快照读）。

---

## 附：环境变量

| 变量 | 必填 | 说明 |
|---|---|---|
| `IMZHUGE_API_KEY` | ✅ | 用户级 API Key（网页端"个人中心 → API Key"生成）。**敏感**：可交易积分，只在环境变量中设置，禁止粘贴进对话/代码/笔记，泄露立即重置 |
| `IMZHUGE_BASE_URL` | ❌ | 开发者选项，普通用户无需设置。默认 `https://m.imzhuge.com`（正式服务器）；本地联调后端时覆盖为 `http://127.0.0.1:8000` |

**Key 未配置时的获取引导**（参照 Tushare 风格）：

```bash
# macOS / Linux
export IMZHUGE_API_KEY="pm_你的key"
# macOS / Linux 永久生效（以 zsh 为例；bash 用户换成 ~/.bashrc）
echo 'export IMZHUGE_API_KEY="pm_你的key"' >> ~/.zshrc && source ~/.zshrc
# Windows PowerShell（当前终端）
$env:IMZHUGE_API_KEY = "pm_你的key"
# Windows 永久生效
setx IMZHUGE_API_KEY "pm_你的key"
```

生成入口：https://m.imzhuge.com → 登录 → 个人中心 → API Key（必须人工网页操作，无法自动化）。

**Windows 调用注意**：PowerShell 的 `curl` 是 `Invoke-WebRequest` 别名，须用 `curl.exe`；含中文的 JSON 请求体不要内联 `-d`（编码损坏报"请求体不是合法的JSON"），先写 UTF-8 文件再 `--data-binary "@file"` 发送。
