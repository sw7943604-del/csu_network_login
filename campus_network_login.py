#!/usr/bin/env python3
"""
校园网自动登录保活脚本 (中南大学 Dr.COM 认证系统)

功能:
  - 每 30 秒检测网络是否在线
  - 检测到认证过期时自动重新登录
  - 支持断线重连（WiFi / 有线均适用）

使用方法:
  1. 修改下面的 USERNAME 和 PASSWORD
  2. python campus_network_login.py
  3. 保持窗口运行即可 (Ctrl+C 退出)

提示: 如果不确定用户名要不要加运营商后缀，登录页面上"校园用户"就不需要加；
     选"校园电信"需要加 @dx，"校园联通"加 @lt，移动用户看你实际登录时显示的用户名。
"""

import time
import sys
import requests
from urllib.parse import urlparse, parse_qs, urlencode

# ============================================================
# 改这里 ↓
# ============================================================
USERNAME = "123"       

PASSWORD = "123"
# ============================================================
# 改这里 ↑
# ============================================================

# 检测间隔 (秒)
CHECK_INTERVAL = 30

# Dr.COM 认证服务器
AUTH_HOST = "http://portal.csu.edu.cn:801"

# 外网探测地址 (用来触发 portal 重定向)
PROBE_URL = "http://www.msftconnecttest.com/connecttest.txt"


def is_online() -> bool:
    """
    检测是否已通过校园网认证。
    直接访问百度，如果返回 200 说明已认证；如果被重定向到 portal 则说明认证过期。
    """
    try:
        r = requests.get(PROBE_URL, timeout=5, allow_redirects=False)
        if r.status_code == 200:
            return True
        # 被重定向 = 认证过期
        if r.status_code in (301, 302, 303, 307, 308):
            loc = r.headers.get("Location", "")
            if "portal" in loc.lower() or "eportal" in loc.lower():
                return False
        return True
    except requests.RequestException:
        # 网络完全不通（可能 WiFi 断了）
        return False


def get_redirect_params() -> dict | None:
    """
    访问外网触发 portal 重定向，从 Location 头中提取认证参数。
    返回解析后的 query 参数字典。
    """
    try:
        r = requests.get(PROBE_URL, timeout=5, allow_redirects=False)
        if r.status_code in (301, 302, 303, 307, 308):
            location = r.headers.get("Location", "")
            if "portal" in location.lower() or "eportal" in location.lower():
                parsed = urlparse(location)
                params = {k: v[0] if isinstance(v, list) else v
                          for k, v in parse_qs(parsed.query, keep_blank_values=True).items()}
                return params
        return None
    except Exception:
        return None


def do_login() -> bool:
    """
    执行 Dr.COM 登录。
    1. 获取 portal 重定向参数
    2. 构造登录 URL
    3. 发送请求
    """
    # 步骤1: 获取 portal 重定向 URL 中的参数
    params = get_redirect_params()
    if not params:
        print(f"  [{_timestamp()}] 无法获取认证参数 (可能网络未通或已在线)")
        return False

    # 提取关键参数
    user_ip = params.get("wlanuserip", "")
    ac_name = params.get("wlanacname", "")
    # 有些部署用 wlanacip 而不是 wlanacname
    ac_ip = params.get("wlanacip", "")

    if not user_ip:
        print(f"  [{_timestamp()}] 缺少 wlanuserip 参数，可能参数名不同")

    # 步骤2: 构造登录请求
    # Dr.COM EPortal 认证接口: /eportal/?c=Portal&a=login
    login_params = {
        "c": "Portal",
        "a": "login",
        "callback": "dr1003",
        "login_method": "1",
        "user_account": USERNAME,
        "user_password": PASSWORD,
        "wlan_user_ip": user_ip,
        "wlan_user_ipv6": "",
        "wlan_user_mac": "000000000000",
        "wlan_ac_ip": ac_ip,
        "wlan_ac_name": ac_name,
        "jsVersion": "4.1",
        "terminal_type": "1",
        "lang": "zh-cn",
        "v": str(int(time.time() * 1000)),
    }

    login_url = f"{AUTH_HOST}/eportal/?" + urlencode(login_params)

    try:
        r = requests.get(login_url, timeout=10,
                         headers={"User-Agent": "Mozilla/5.0"})
        # 响应是 JSONP 格式: dr1003({...})
        text = r.text
        if '"result":1' in text or '"result":"1"' in text:
            return True
        elif '"result":0' in text or '"result":"0"' in text:
            # 提取错误信息
            import re
            match = re.search(r'"msg"\s*:\s*"([^"]*)"', text)
            msg = match.group(1) if match else "未知错误"
            print(f"  [{_timestamp()}] 登录失败: {msg}")
            return False
        else:
            print(f"  [{_timestamp()}] 未知响应: {text[:200]}")
            return False
    except requests.RequestException as e:
        print(f"  [{_timestamp()}] 请求失败: {e}")
        return False


def _timestamp() -> str:
    return time.strftime("%H:%M:%S")


def main():
    print("=" * 55)
    print("  中南大学 校园网自动登录保活脚本")
    print("  Dr.COM EPortal")
    print("=" * 55)
    print(f"  用户名:   {USERNAME}")
    print(f"  检测间隔: {CHECK_INTERVAL} 秒")
    print(f"  认证地址: {AUTH_HOST}")
    print("=" * 55)

    if USERNAME == "你的学号":
        print("\n  [!!] 请先打开脚本修改 USERNAME 和 PASSWORD！\n")
        return

    print(f"\n[{_timestamp()}] 开始监控... (Ctrl+C 停止)\n")
    consecutive_failures = 0

    while True:
        try:
            if is_online():
                if consecutive_failures > 0:
                    print(f"[{_timestamp()}] ✓ 网络已恢复")
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                print(f"[{_timestamp()}] ✗ 网络不可达 (连续 {consecutive_failures} 次)")

                # 连续 2 次确认断开后才尝试登录，减少误判
                if consecutive_failures >= 2:
                    print(f"[{_timestamp()}] → 尝试重新认证...")
                    if do_login():
                        # 等 2 秒后验证
                        time.sleep(2)
                        if is_online():
                            print(f"[{_timestamp()}] ✓ 认证成功！")
                            consecutive_failures = 0
                        else:
                            print(f"[{_timestamp()}] 认证请求已发送，下次检测时验证")
                            consecutive_failures = 0
                    else:
                        print(f"[{_timestamp()}] 下次检测时重试")

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print(f"\n[{_timestamp()}] 已退出")
            break


if __name__ == "__main__":
    main()
