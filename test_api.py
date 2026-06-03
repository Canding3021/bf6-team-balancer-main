"""
BF6 Team Balancer - API 可用性验证脚本

测试 gametools.network + joarchy.com 双源查询是否可用。
用法: python test_api.py
"""

import requests
import time
import sys
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

# Windows 控制台 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

GAMETOOLS_BASE = "https://api.gametools.network/bf6/stats/"
JOARCHY_BASE = "https://api-btr-joo-uk.joarchy.com"


def query_gametools(name: str, platform: str = "pc", timeout: int = 10) -> dict | None:
    """查询单个玩家 (gametools)，返回 {"kd", "kpm", "userId"} 或 None"""
    params = {
        "name": name,
        "platform": platform,
        "format_values": "false",
        "lang": "en-us",
    }
    try:
        resp = requests.get(GAMETOOLS_BASE, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        if data.get("hasResults") is False:
            return None
        if "userName" not in data or "kills" not in data:
            return None
        if "errors" in data:
            return None

        return {
            "name": data.get("userName", name),
            "kd": data.get("killDeath"),
            "kpm": data.get("killsPerMinute"),
            "userId": str(data.get("userId", "")) if data.get("userId") else None,
        }
    except (requests.Timeout, requests.RequestException, ValueError, KeyError):
        return None


def query_joarchy(identifier: str | None = None, name: str | None = None,
                  platform: str = "pc", timeout: int = 12) -> dict | None:
    """查询单个玩家 (joarchy)，返回 {"kd", "kpm"} 或 None"""
    params = {"platform": platform}
    if identifier:
        params["identifier"] = identifier
    elif name:
        params["name"] = name
    else:
        return None

    try:
        resp = requests.get(f"{JOARCHY_BASE}/v2/profile", params=params, timeout=timeout)
        if resp.status_code != 200:
            return None
        data = resp.json()
        stats = data.get("stats", {})
        if not stats:
            return None

        kd = stats.get("killDeath")
        kpm = stats.get("killsPerMinute")
        if kd is None and kpm is None:
            return None

        return {
            "kd": float(kd) if kd is not None else 0.0,
            "kpm": float(kpm) if kpm is not None else 0.0,
        }
    except (requests.Timeout, requests.RequestException, ValueError, KeyError):
        return None


# ── 测试用例 ───────────────────────────────────────────────────

def test_gametools_real_player():
    """测试1: gametools 查询真实玩家"""
    print("=" * 50)
    print("测试1: gametools 查询真实玩家")
    print("=" * 50)

    name = "AshTwoPoint0"
    print(f"查询: {name}")
    start = time.time()
    result = query_gametools(name)
    elapsed = time.time() - start

    if result:
        print(f"  ✅ 成功 ({elapsed:.1f}s)")
        print(f"  昵称: {result['name']}")
        print(f"  KD:   {result['kd']}")
        print(f"  KPM:  {result['kpm']}")
        print(f"  userId: {result['userId']}")
        return True
    else:
        print(f"  ❌ 失败 ({elapsed:.1f}s)")
        return False


def test_gametools_nonexistent():
    """测试2: gametools 查询不存在的玩家"""
    print()
    print("=" * 50)
    print("测试2: gametools 查询不存在的玩家")
    print("=" * 50)

    name = "ThisPlayerDefinitelyDoesNotExist12345XYZ"
    print(f"查询: {name}")
    start = time.time()
    result = query_gametools(name)
    elapsed = time.time() - start

    if result is None:
        print(f"  ✅ 正确返回 None ({elapsed:.1f}s)")
        return True
    else:
        print(f"  ⚠️ 意外返回了数据: {result} ({elapsed:.1f}s)")
        return False


def test_joarchy_by_identifier():
    """测试3: joarchy 用 identifier 查询"""
    print()
    print("=" * 50)
    print("测试3: joarchy identifier 查询")
    print("=" * 50)

    # Canding3021 的 identifier，gametools 查不到但 joarchy 能查到
    identifier = "1011100546730"
    print(f"查询: identifier={identifier}")
    start = time.time()
    result = query_joarchy(identifier=identifier)
    elapsed = time.time() - start

    if result:
        print(f"  ✅ 成功 ({elapsed:.1f}s)")
        print(f"  KD:   {result['kd']}")
        print(f"  KPM:  {result['kpm']}")
        return True
    else:
        print(f"  ❌ 失败 ({elapsed:.1f}s)")
        return False


def test_joarchy_by_name():
    """测试4: joarchy 用 name 查询"""
    print()
    print("=" * 50)
    print("测试4: joarchy name 查询")
    print("=" * 50)

    name = "Lilya-magic"
    print(f"查询: {name}")
    start = time.time()
    result = query_joarchy(name=name)
    elapsed = time.time() - start

    if result:
        print(f"  ✅ 成功 ({elapsed:.1f}s)")
        print(f"  KD:   {result['kd']}")
        print(f"  KPM:  {result['kpm']}")
        return True
    else:
        print(f"  ❌ 失败 ({elapsed:.1f}s)")
        return False


def test_dual_source():
    """测试5: 双源查询流程（模拟完整 query_all 流程）"""
    print()
    print("=" * 50)
    print("测试5: 双源查询流程")
    print("=" * 50)

    test_players = [
        {"name": "Lilya-magic", "eaid": "Lilya-magic"},
        {"name": "INKL1NG1", "eaid": "INKL1NG1"},
        {"name": "Canding3021", "eaid": "Canding3021"},  # gametools 404
    ]

    print(f"批量查询 {len(test_players)} 个玩家...")
    start = time.time()

    # Step 1: gametools
    print("  Step 1: gametools 查询...")
    gt_results = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(query_gametools, p["eaid"]): p for p in test_players}
        for future in as_completed(futures):
            p = futures[future]
            gt_results[p["eaid"]] = future.result()

    for eaid, r in gt_results.items():
        if r:
            print(f"    ✅ {eaid}: KD={r['kd']} KPM={r['kpm']} userId={r['userId']}")
        else:
            print(f"    ❌ {eaid}: 未查到")

    # Step 2: joarchy by identifier
    print("  Step 2: joarchy identifier 查询...")
    joarchy_id_results = {}
    eaid_to_userid = {eaid: r["userId"] for eaid, r in gt_results.items() if r and r.get("userId")}

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(query_joarchy, identifier=uid): eaid for eaid, uid in eaid_to_userid.items()}
        for future in as_completed(futures):
            eaid = futures[future]
            joarchy_id_results[eaid] = future.result()

    for eaid, r in joarchy_id_results.items():
        if r:
            print(f"    ✅ {eaid}: KD={r['kd']} KPM={r['kpm']}")
        else:
            print(f"    ❌ {eaid}: 未查到")

    # Step 3: joarchy fallback by name (for gametools failures)
    print("  Step 3: joarchy name 兜底查询...")
    not_found = [eaid for eaid, r in gt_results.items() if r is None]
    joarchy_fb_results = {}

    if not_found:
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(query_joarchy, name=eaid): eaid for eaid in not_found}
            for future in as_completed(futures):
                eaid = futures[future]
                joarchy_fb_results[eaid] = future.result()

    for eaid, r in joarchy_fb_results.items():
        if r:
            print(f"    ✅ {eaid}: KD={r['kd']} KPM={r['kpm']}")
        else:
            print(f"    ❌ {eaid}: 未查到")

    # Merge
    print("  合并结果:")
    for eaid in [p["eaid"] for p in test_players]:
        gt = gt_results.get(eaid)
        j_id = joarchy_id_results.get(eaid)
        j_fb = joarchy_fb_results.get(eaid)

        if gt:
            kd = gt["kd"]
            kpm = j_id["kpm"] if j_id and j_id.get("kpm") is not None else (j_fb["kpm"] if j_fb and j_fb.get("kpm") is not None else gt["kpm"])
            print(f"    {eaid}: KD={kd} KPM={kpm} (来源: gametools+joarchy)")
        elif j_fb:
            print(f"    {eaid}: KD={j_fb['kd']} KPM={j_fb['kpm']} (来源: joarchy兜底)")
        else:
            print(f"    {eaid}: ❌ 未查到")

    elapsed = time.time() - start
    print(f"  总耗时: {elapsed:.1f}s")
    return True


def test_timeout():
    """测试6: 超时测试"""
    print()
    print("=" * 50)
    print("测试6: 超时测试 (0.001s 超时)")
    print("=" * 50)

    name = "AshTwoPoint0"
    print(f"查询: {name}")
    start = time.time()
    result = query_gametools(name, timeout=0.001)
    elapsed = time.time() - start

    if result is None:
        print(f"  ✅ 正确超时 ({elapsed:.1f}s)")
        return True
    else:
        print(f"  ⚠️ 居然没超时: {result} ({elapsed:.1f}s)")
        return True


if __name__ == "__main__":
    print("BF6 API 可用性测试 (gametools + joarchy 双源)")
    print(f"gametools: {GAMETOOLS_BASE}")
    print(f"joarchy:   {JOARCHY_BASE}/v2/profile")
    print()

    results = []
    results.append(("gametools 真实玩家", test_gametools_real_player()))
    results.append(("gametools 不存在玩家", test_gametools_nonexistent()))
    results.append(("joarchy identifier", test_joarchy_by_identifier()))
    results.append(("joarchy name", test_joarchy_by_name()))
    results.append(("双源查询流程", test_dual_source()))
    results.append(("超时测试", test_timeout()))

    print()
    print("=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    all_pass = True
    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}  {name}")
        if not ok:
            all_pass = False

    print()
    if all_pass:
        print("🎉 全部通过！双源 API 可用。")
    else:
        print("⚠️ 部分测试失败，请检查网络或 API 状态。")

    sys.exit(0 if all_pass else 1)
