#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""离线演示 fixture（--mock 模式专用）。

数据结构与真实 API 响应同构（见 references/api-reference.md §9-13），
用于无 API Key、无网络环境下演示完整参与者链路与输出格式。
所有 ID/价格均为演示值，不对应真实市场。
"""

# ---- my_participated_events/：2 场比赛（1 场进行中的小事件 + 1 场大事件）----
EVENTS = [
    {
        "id": 21, "name": "科创50指数11月涨跌幅预测",
        "start_time": "2026-11-01T00:00", "end_time": "2026-11-30T23:59",
        "award": 1000, "status": "进行中", "event_type": "",
        "is_owner": False, "joined": True,
        "is_PointsSegregated": 0, "coin_event": None,
        "is_special": False, "group_count": 1, "activity_count": 3,
    },
    {
        "id": 18521, "name": "上证50成分股5日股价涨跌预测",
        "start_time": "2026-11-03T00:00", "end_time": "2027-11-03T23:59",
        "award": 500, "status": "进行中", "event_type": "sh50_5",
        "is_owner": False, "joined": True,
        "is_PointsSegregated": 1, "coin_event": 100,
        "is_special": False, "group_count": 1, "activity_count": 5320,
    },
]

# ---- my_event_markets/?event_id=21：区间档 + 事件类合约（不止涨跌二元）----
MARKETS_21 = {
    "status": "success", "message": "",
    "data": {
        "event": {"id": 21, "name": "科创50指数11月涨跌幅预测", "status": "进行中",
                  "is_PointsSegregated": 0, "coin_event": None,
                  "start_time": "2026-11-01T00:00", "end_time": "2026-11-30T23:59"},
        "activities": [
            {
                "id": 46994, "name": "科创50指数11-20涨跌幅预测",
                "description": "以 11-20 收盘价相对 11-19 的涨跌幅结算",
                "start_date": "2026-11-18T00:00", "end_date": "2026-11-20T23:59",
                "status": 1, "status_label": "进行中", "can_trade": True, "is_show": True,
                "has_award": 0, "award": 0, "group_id": 132,
                "projects": [
                    {
                        "id": 47287, "title": "科创50指数2026-11-20收盘涨跌幅预测",
                        "desc": "三档区间：跌超5% / ±5%以内 / 涨超5%",
                        "start_time": "2026-11-18T09:00", "end_time": "2026-11-20T15:00",
                        "is_finished": False,
                        "contracts": [
                            {"id": 95290, "contract_text": "<-5.00%",
                             "origin_price": 0.3333, "update_price": 0.43, "contract_is_true": False},
                            {"id": 95291, "contract_text": "-5.00%~+5.00%",
                             "origin_price": 0.3333, "update_price": 0.47, "contract_is_true": False},
                            {"id": 95292, "contract_text": ">+5.00%",
                             "origin_price": 0.3334, "update_price": 0.11, "contract_is_true": False},
                        ],
                    },
                ],
            },
            {
                "id": 46995, "name": "某球员冬窗转会预测",
                "description": "事件类市场：转会成功与否",
                "start_date": "2026-11-10T00:00", "end_date": "2026-12-01T23:59",
                "status": 1, "status_label": "进行中", "can_trade": True, "is_show": True,
                "has_award": 0, "award": 0, "group_id": 132,
                "projects": [
                    {
                        "id": 47290, "title": "该球员2026冬窗是否转会成功",
                        "desc": "以官方公告为准",
                        "start_time": "2026-11-10T00:00", "end_time": "2026-12-01T23:59",
                        "is_finished": False,
                        "contracts": [
                            {"id": 95300, "contract_text": "转会成功",
                             "origin_price": 0.5, "update_price": 0.62, "contract_is_true": False},
                            {"id": 95301, "contract_text": "留队",
                             "origin_price": 0.5, "update_price": 0.38, "contract_is_true": False},
                        ],
                    },
                ],
            },
        ],
    },
}

# ---- my_balance/：46994 通用赛 / 46995 积分隔离赛 ----
BALANCE_46994 = {
    "status": "success", "message": "",
    "data": {"activity_id": 46994, "event_id": 21, "is_points_segregated": 0,
             "group_id": None, "joined": True, "balance": 30.0, "total_money": 36.17},
}

BALANCE_46995 = {
    "status": "success", "message": "",
    "data": {"activity_id": 46995, "event_id": 21, "is_points_segregated": 1,
             "group_id": None, "joined": True, "balance": 100.0, "coin_event": 100.0,
             "balance_label": "本比赛专属积分", "total_money": 36.17},
}

BALANCE_46996 = {  # 未加入的演示场景
    "status": "warning", "message": "您尚未加入该活动，暂无余额",
    "data": {"activity_id": 46996, "event_id": 21, "is_points_segregated": 0,
             "group_id": None, "joined": False, "balance": 0, "total_money": 36.17},
}

# ---- my_holdings/?activity_id=46994：此前买入 1 份区间档 ----
HOLDINGS_46994 = {
    "status": "success", "message": "",
    "data": {"activity_id": 46994, "event_id": 21, "is_points_segregated": 0,
             "joined": True, "balance": 29.53, "total_money": 35.70,
             "projects": [
                 {"id": 47287, "title": "科创50指数2026-11-20收盘涨跌幅预测",
                  "start_time": "2026-11-18T09:00", "end_time": "2026-11-20T15:00",
                  "is_finished": False,
                  "contracts": [
                      {"id": 95290, "contract_text": "<-5.00%",
                       "current_price": 0.43, "holding_share": 0, "contract_is_true": False},
                      {"id": 95291, "contract_text": "-5.00%~+5.00%",
                       "current_price": 0.47058, "holding_share": 1, "contract_is_true": False},
                      {"id": 95292, "contract_text": ">+5.00%",
                       "current_price": 0.11, "holding_share": 0, "contract_is_true": False},
                  ]},
             ]},
}

# ---- trade_confirm/：按请求体动态构造成交回报 ----
def trade_result(body):
    price = 0.47  # 成交前市价（区间档 95291）
    share = body.get("share", 1)
    if body.get("action") == "buy":
        payoff = round(-(share * price + 0.00058 * share), 5)
    else:
        payoff = round(share * price - 0.00058 * share, 5)
    balance_after = round(30.0 + payoff, 5)
    return {
        "status": "success", "message": "",
        "data": {
            "trade_id": 594212, "action": body.get("action", "buy"), "share": share,
            "activity_id": body.get("activity_id"), "project_id": body.get("project_id"),
            "contract_id": body.get("contract_id"), "contract_text": "-5.00%~+5.00%",
            "price": price, "payoff": payoff,
            "updated_prices": {"95290": 0.43, "95291": 0.47058, "95292": 0.11},
            "balance_after": balance_after, "total_money_after": round(36.17 + payoff, 5),
            "is_points_segregated": 0, "trade_time": "2026-11-18T14:30",
        },
    }


def mock_call(method, path, body=None):
    """离线路由：返回 (http_status, resp_dict)，与真实 call() 同签名语义。"""
    from urllib.parse import urlparse, parse_qs
    q = parse_qs(urlparse(path).query)
    if path.startswith('/my_participated_events'):
        return 200, {"status": "success", "message": "", "data": EVENTS}
    if path.startswith('/my_event_markets'):
        event_id = int(q.get('event_id', ['21'])[0])
        if event_id == 21:
            return 200, MARKETS_21
        return 200, {"status": "error", "message": "无权查看该比赛（mock 仅演示 event 21）"}
    if path.startswith('/my_balance'):
        aid = int(q.get('activity_id', ['46994'])[0])
        fixture = {46994: BALANCE_46994, 46995: BALANCE_46995, 46996: BALANCE_46996}.get(aid)
        if fixture is None:
            return 200, {"status": "error", "message": "活动不存在（mock 仅演示 46994/46995/46996）"}
        return 200, fixture
    if path.startswith('/my_holdings'):
        aid = int(q.get('activity_id', ['46994'])[0])
        if aid == 46994:
            return 200, HOLDINGS_46994
        return 200, {"status": "error", "message": "活动不存在（mock 仅演示 46994）"}
    if path.startswith('/trade_confirm'):
        return 200, trade_result(body or {})
    return 200, {"status": "error", "message": "mock 未覆盖该端点: %s" % path}
