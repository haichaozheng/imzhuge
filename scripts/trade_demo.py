#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""嗨皮诸葛预测市场 — 参与者链路演示（仅 Python 3 标准库）。

链路：读环境变量 → 列我参与的比赛 → 查市场详情 → 查余额 → 查持仓
      → （显式传参时）下单 → 复查持仓。

用法：
    # 只读模式（无任何写操作，可安全重复执行）
    python trade_demo.py

    # 下单模式（6 个位置参数齐备才交易；默认交互确认，--yes 跳过）
    python trade_demo.py <activity_id> <contract_id> <buy|sell> <share> <pred_proba> "<note>"
    python trade_demo.py 46994 95290 buy 1 0.6 "看好指数上涨，试水一份"

    # 大事件（activity_count > 100，如 sh50_5）不下拉市场列表，
    # 需从网页端市场页 URL 获取 project_id 后用 --project 指定：
    python trade_demo.py <activity_id> <contract_id> <buy|sell> <share> <pred_proba> "<note>" --project 47287 --yes

    # Base URL 为明文 HTTP 且非本机地址时，需显式确认风险：
    python trade_demo.py ... --allow-insecure

环境变量：
    IMZHUGE_API_KEY            必填，pm_ 开头的用户级 API Key
    IMZHUGE_BASE_URL           选填，默认 https://m.imzhuge.com（本地联调设 http://127.0.0.1:8000）

注意：
    - 下单无幂等保护：失败/超时后禁止自动重试，先查持仓确认实际状态。
    - note 必须大于 5 个字、不超过 1000 字；confidence 四选一（--confidence，默认"有点信心"）；pred_proba 为 0~1 数值。
    - 大事件防护：比赛活动数超过 100 时不调用 my_event_markets（响应过大会刷爆上下文）。
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

# Windows 控制台常为 GBK，打不出 emoji/部分中文会直接 UnicodeEncodeError 崩溃
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, 'reconfigure'):
        _stream.reconfigure(encoding='utf-8', errors='replace')

API_KEY = os.environ.get('IMZHUGE_API_KEY', '')
BASE = (os.environ.get('IMZHUGE_BASE_URL') or 'https://m.imzhuge.com').rstrip('/') \
    + '/startactivity/api/open'

CONFIDENCE_LIST = ['完全瞎猜', '有点瞎猜', '有点信心', '很有信心']
BIG_EVENT_ACTIVITY_LIMIT = 100   # 活动数超过此值视为大事件，禁止全量下拉市场列表
MIN_CALL_INTERVAL = 1.1          # 最小调用间隔（秒），保守防 429（限流 60 次/分钟）
_last_call_ts = 0.0


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """跨主机重定向时剥掉 X-API-Key，防止 Key 被重定向目标收集。

    同主机重定向保留鉴权头（目标仍在受信服务内）。
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old_host = (urlparse(req.full_url).hostname or '').lower()
        new_host = (urlparse(newurl).hostname or '').lower()
        if old_host != new_host:
            safe = urllib.request.Request(newurl, data=req.data, method=req.get_method())
            for k, v in req.header_items():
                if k.lower() != 'x-api-key':
                    safe.add_header(k, v)
            print('⚠️  跨主机重定向（%s → %s）：已剥除 API Key，若响应为 401 属预期。'
                  % (old_host, new_host))
            return safe
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_SafeRedirectHandler)


def call(method, path, body=None):
    """调 open API，返回 (http_status, resp_dict)。

    网络层异常（超时/不可达/非 JSON 响应）不向上抛裸异常，
    统一转为 (0, {'status': 'error', ...})，由调用方决定如何提示。
    内置：最小调用间隔防 429；429 时按 Retry-After 等待后重发一次（业务未执行，安全）。
    """
    global _last_call_ts
    data = None
    headers = {'X-API-Key': API_KEY}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode('utf-8')
        headers['Content-Type'] = 'application/json'

    for attempt in (1, 2):  # 最多 2 次：常规 1 次 + 429 重试 1 次
        wait = MIN_CALL_INTERVAL - (time.monotonic() - _last_call_ts)
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
        try:
            _last_call_ts = time.monotonic()
            with _opener.open(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            _last_call_ts = time.monotonic()
            if e.code == 429 and attempt == 1:
                retry_after = e.headers.get('Retry-After') or '60'
                try:
                    pause = max(int(float(retry_after)), 1)
                except ValueError:
                    pause = 60
                print('⏳ 触发限流（429），等待 %ss 后重试一次（请求被拦截，未成交，安全）…' % pause)
                time.sleep(pause)
                continue
            try:
                return e.code, json.loads(e.read().decode('utf-8'))
            except ValueError:
                return e.code, {'status': 'error',
                                'message': 'HTTP %s，响应不是 JSON（可能被网关/代理拦截）' % e.code}
        except ValueError:
            return 0, {'status': 'error',
                       'message': '响应不是合法 JSON（可能被网关/代理拦截），结果未知，禁止自动重试；'
                                  '请先用只读接口核对实际状态'}
        except (urllib.error.URLError, OSError) as e:
            return 0, {'status': 'error',
                       'message': '网络异常（超时/不可达）：%s。结果未知，禁止自动重试；'
                                  '请先用只读接口（my_holdings/my_balance）核对实际状态' % e}


def die(msg):
    print('FATAL: %s' % msg)
    sys.exit(1)


def is_big_event(e):
    return (e.get('activity_count') or 0) > BIG_EVENT_ACTIVITY_LIMIT


def validate_trade_args(args):
    """下单模式参数完整性校验（在任何 API 调用之前执行）。"""
    need = [('activity_id', args.activity_id), ('contract_id', args.contract_id),
            ('action', args.action), ('share', args.share),
            ('pred_proba', args.pred_proba), ('note', args.note)]
    missing = [n for n, v in need if v is None]
    if missing:
        die('下单模式缺少参数: %s。\n完整用法: python trade_demo.py '
            '<activity_id> <contract_id> <buy|sell> <share> <pred_proba> "<note>" '
            '[--project P] [--confidence 四选一] [--yes]' % ', '.join(missing))
    if args.share < 1:
        die('share 必须为正整数。')
    if not (0.0 <= args.pred_proba <= 1.0):
        die('pred_proba 必须在 0~1 之间。')
    if len(args.note) <= 5:
        die('note 必须大于 5 个字（交易理由，不得编造模板套话）。')
    if len(args.note) > 1000:
        die('note 最长 1000 字，当前 %s 字，请精简。' % len(args.note))


def pick_target(events):
    """挑一场非大事件的比赛做只读演示（优先进行中）。"""
    small = [e for e in events if not is_big_event(e)]
    if not small:
        return None
    return next((e for e in small if e['status'] == '进行中'), small[0])


def resolve_project(args, events):
    """定位 project_id：优先 --project 显式指定；否则经 my_balance 反查 event 再搜市场。

    大事件（活动数 > 100）禁止调 my_event_markets（响应会刷爆上下文）。
    """
    if args.project:
        return args.project
    s, r = call('GET', '/my_balance/?activity_id=%s' % args.activity_id)
    if r.get('status') != 'success':
        die('活动 %s 不可用（%s）：未加入或不存在，请先在网页端确认。'
            % (args.activity_id, r.get('message')))
    event_id = r['data']['event_id']
    ev = next((e for e in events if e['id'] == event_id), None)
    if ev is not None and is_big_event(ev):
        die('比赛 %s「%s」有 %s 个活动（大事件），脚本不下拉其市场列表。\n'
            '请从网页端市场页 URL 获取 project_id 后加 --project <id> 重试。'
            % (event_id, ev['name'], ev['activity_count']))
    s, r = call('GET', '/my_event_markets/?event_id=%s' % event_id)
    if r.get('status') != 'success':
        die('my_event_markets 失败: %s' % r.get('message'))
    for a in r['data']['activities']:
        if a['id'] != args.activity_id:
            continue
        for p in a['projects']:
            if any(c['id'] == args.contract_id for c in p['contracts']):
                return p['id']
    die('合约 %s 不在活动 %s 中（activity/contract ID 有误，或不在你有权限的比赛里）。'
        % (args.contract_id, args.activity_id))


def main():
    # ---- 环境检查 ----
    if not API_KEY:
        die('环境变量 IMZHUGE_API_KEY 未设置。\n'
            '获取：网页端 https://m.imzhuge.com → 登录 → 个人中心 → API Key → 生成（pm_ 开头）\n'
            '设置：macOS/Linux  export IMZHUGE_API_KEY="pm_你的key"\n'
            '      PowerShell  $env:IMZHUGE_API_KEY = "pm_你的key"\n'
            '      Windows永久 setx IMZHUGE_API_KEY "pm_你的key"（重开终端生效）\n'
            '注意：Key 可交易积分，勿粘贴进对话/代码/笔记；泄露立即网页端轮换。')
    if not API_KEY.startswith('pm_'):
        die('API Key 格式不对，应以 pm_ 开头。')

    # ---- 命令行参数（先校验，再发起任何 API 调用）----
    ap = argparse.ArgumentParser(
        description='嗨皮诸葛参与者链路演示（不传下单参数 = 只读模式，可安全重复执行）')
    ap.add_argument('activity_id', type=int, nargs='?', help='活动 ID（下单模式必填）')
    ap.add_argument('contract_id', type=int, nargs='?', help='合约 ID（下单模式必填）')
    ap.add_argument('action', choices=['buy', 'sell'], nargs='?', help='方向（下单模式必填）')
    ap.add_argument('share', type=int, nargs='?', help='份数，正整数（下单模式必填）')
    ap.add_argument('pred_proba', type=float, nargs='?', help='预测概率 0~1（下单模式必填）')
    ap.add_argument('note', nargs='?', help='交易理由，>5 个字且 ≤1000 字（下单模式必填）')
    ap.add_argument('--project', type=int, default=None,
                    help='project_id（大事件必填：从网页端 URL 获取，脚本将跳过市场列表搜索）')
    ap.add_argument('--confidence', default='有点信心', choices=CONFIDENCE_LIST,
                    help='自信程度四选一（默认：%(default)s）')
    ap.add_argument('--allow-insecure', action='store_true',
                    help='放行明文 HTTP 的非本机 Base URL（Key 将明文穿网，仅限受信网络联调）')
    ap.add_argument('--yes', action='store_true', help='跳过交互确认（默认需输入 yes）')
    args = ap.parse_args()

    # ---- Base URL 协议校验：非 https 且非本机地址时 Key 会明文穿网 ----
    from urllib.parse import urlparse
    _parsed = urlparse(BASE)
    _local_hosts = {'localhost', '127.0.0.1', '::1'}
    if _parsed.scheme != 'https' and (_parsed.hostname or '') not in _local_hosts:
        print('⚠️  警告：IMZHUGE_BASE_URL 指向明文 HTTP 的非本机地址（%s）。' % _parsed.hostname)
        print('    API Key（含交易能力）将以明文穿越网络，可被中间人截获，')
        print('    仅应在私有/受信网络中联调时使用。')
        if args.allow_insecure and args.yes:
            # 明文传输 + 跳过确认 + 自动下单是最坏组合，禁止静默通过
            die('安全中止：--allow-insecure 与 --yes 不可同时使用（明文网络 + 免确认下单风险过大）。'
                '\n请二选一：去掉 --yes 保留人工确认，或改用 https:// 地址。')
        if not args.allow_insecure:
            die('已中止。确认风险后加 --allow-insecure 重试，或改用 https:// 地址。')
        print('🚨 已确认风险：本次会话的 API Key 以明文传输，任务结束后建议立即轮换（网页端 个人中心 → API Key）。')

    trade_mode = any(x is not None for x in
                     [args.activity_id, args.contract_id, args.action,
                      args.share, args.pred_proba, args.note]) or args.project
    if trade_mode:
        validate_trade_args(args)

    # ---- Step 1: 列我参与的比赛 ----
    s, r = call('GET', '/my_participated_events/')
    if s == 401:
        die('API Key 无效或已过期（HTTP 401）。')
    if r.get('status') != 'success':
        die('my_participated_events 失败: %s' % r.get('message'))
    events = r['data']
    print('== 我参与/发起/受邀的比赛：共 %s 场 ==' % len(events))
    for e in events[:10]:
        print('  [%s] event=%-4s %s ~ %s joined=%s owner=%s seg=%s acts=%s %s' % (
            e['status'], e['id'], e['start_time'], e['end_time'],
            e['joined'], e['is_owner'], e['is_PointsSegregated'],
            e.get('activity_count'), e['name']))
    big = [e for e in events if is_big_event(e)]
    if big:
        print('  （另有 %s 场大事件已跳过市场详情：%s）'
              % (len(big), '、'.join(str(e['id']) for e in big)))
    if not events:
        print('（无比赛。先在网页端加入比赛，或用 create_event API 创建。）')
        return

    if trade_mode:
        return do_trade(args, events)

    # ---- Step 2: 只读演示，挑一场非大事件的比赛看市场 ----
    target = pick_target(events)
    if target is None:
        print('\n（所有比赛均为大事件（活动数 > %s），不下拉市场列表；'
              '下单请显式传 activity_id 等参数）' % BIG_EVENT_ACTIVITY_LIMIT)
        return
    print('\n== 比赛 %s「%s」的市场 ==' % (target['id'], target['name']))
    s, r = call('GET', '/my_event_markets/?event_id=%s' % target['id'])
    if r.get('status') != 'success':
        print('my_event_markets: %s %s' % (s, r.get('message')))
        return
    first_act = r['data']['activities'][0] if r['data']['activities'] else None
    if not first_act:
        print('（该比赛暂无活动）')
        return
    print('  活动 %s「%s」can_trade=%s' % (first_act['id'], first_act['name'], first_act['can_trade']))
    for p in first_act['projects'][:3]:
        print('    项目 %s「%s」窗口 %s ~ %s' % (
            p['id'], p['title'], p['start_time'], p['end_time']))
        for c in p['contracts']:
            print('      合约 %s %-6s 价=%s' % (c['id'], c['contract_text'], c['update_price']))

    # ---- Step 3: 余额 ----
    print('\n== 我的余额（活动 %s）==' % first_act['id'])
    s, r = call('GET', '/my_balance/?activity_id=%s' % first_act['id'])
    if r.get('status') == 'warning':
        print('  [未加入] %s（需先在网页端加入活动）' % r.get('message'))
    else:
        d = r['data']
        label = d.get('balance_label') or ('活动诸葛贝' if not d['is_points_segregated'] else '专属积分')
        print('  %s: %s | 全局诸葛贝: %s' % (label, d['balance'], d['total_money']))

    # ---- Step 4: 持仓 ----
    print('\n== 我的持仓（活动 %s）==' % first_act['id'])
    s, r = call('GET', '/my_holdings/?activity_id=%s' % first_act['id'])
    if r.get('status') == 'success':
        for p in r['data']['projects'][:3]:
            held = [c for c in p['contracts'] if c['holding_share'] != 0]
            if held:
                for c in held:
                    print('    项目%s 合约%s「%s」 持仓%s份 现价%s' % (
                        p['id'], c['id'], c['contract_text'], c['holding_share'], c['current_price']))
            else:
                print('    项目%s：无持仓' % p['id'])

    print('\n（只读演示结束。下单用法: python trade_demo.py '
          '<activity_id> <contract_id> <buy|sell> <share> <pred_proba> "<note>"）')


def do_trade(args, events):
    """下单模式：定位 project → 参数确认 → 提交（仅一次）→ 复查。"""
    project_id = resolve_project(args, events)

    # ---- 下单确认（交易无幂等，默认要求人工输入 yes）----
    print('\n== 下单确认 ==')
    print('  活动 %s | 项目 %s | 合约 %s' % (args.activity_id, project_id, args.contract_id))
    print('  %s %s 份 | pred_proba=%s | confidence=%s' % (
        args.action, args.share, args.pred_proba, args.confidence))
    print('  note: %s' % args.note)
    print('  （交易无幂等：确认后只提交一次；失败/超时禁止自动重试）')
    if not args.yes:
        ans = input('确认下单请输入 yes 回车，其他任意输入取消: ').strip().lower()
        if ans != 'yes':
            print('已取消，未发送任何请求。')
            return

    body = {
        'activity_id': args.activity_id, 'project_id': project_id,
        'contract_id': args.contract_id,
        'action': args.action, 'share': args.share,
        'note': args.note,
        'pred_proba': args.pred_proba, 'confidence': args.confidence,
    }
    print('\n== 提交 %s %s 份合约 %s ==' % (args.action, args.share, args.contract_id))
    s, r = call('POST', '/trade_confirm/', body)
    print('HTTP %s | status=%s' % (s, r.get('status')))
    if r.get('status') == 'success':
        d = r['data']
        print('  成交！trade_id=%s 价=%s payoff=%s' % (d['trade_id'], d['price'], d['payoff']))
        print('  余额=%s 全局=%s' % (d['balance_after'], d['total_money_after']))
    else:
        print('  失败：%s' % r.get('message'))
        print('  （注意：执行类失败禁止自动重试；请先查持仓确认实际状态）')
        sys.exit(2)

    # ---- 复查 ----
    s, r = call('GET', '/my_holdings/?activity_id=%s' % args.activity_id)
    if r.get('status') == 'success':
        for p in r['data']['projects']:
            for c in p['contracts']:
                if c['id'] == args.contract_id:
                    print('\n== 复查：合约 %s 持仓=%s 现价=%s ==' % (
                        args.contract_id, c['holding_share'], c['current_price']))


if __name__ == '__main__':
    main()
