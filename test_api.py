"""
BF6 Team Balancer - API 可用性验证脚本

测试 gametools.network 的 /bf6/stats/ 接口是否可用。
用法: python test_api.py
"""

import requests
import time
import sys
import io

# Windows 控制台 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

API_BASE = "https://api.gametools.network/bf6/stats/"


def query_player(name: str, platform: str = "pc", timeout: int = 10) -> dict | None:
    """查询单个玩家，返回 {"name", "kd", "kpm"} 或 None"""
    params = {
        "name": name,
        "platform": platform,
        "format_values": "false",
        "lang": "en-us",
    }
    try:
        resp = requests.get(API_BASE, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        # 检查是否查到
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
        }
    except requests.Timeout:
        print(f"  ⏱ 超时 ({timeout}s)")
        return None
    except requests.RequestException as e:
        print(f"  ❌ 网络错误: {e}")
        return None
    except (ValueError, KeyError) as e:
        print(f"  ❌ 解析错误: {e}")
        return None


def test_real_player():
    """测试1: 查询一个真实玩家"""
    print("=" * 50)
    print("测试1: 查询真实玩家")
    print("=" * 50)

    name = "AshTwoPoint0"
    print(f"查询: {name}")
    start = time.time()
    result = query_player(name)
    elapsed = time.time() - start

    if result:
        print(f"  ✅ 成功 ({elapsed:.1f}s)")
        print(f"  昵称: {result['name']}")
        print(f"  KD:   {result['kd']}")
        print(f"  KPM:  {result['kpm']}")
        return True
    else:
        print(f"  ❌ 失败 ({elapsed:.1f}s)")
        return False


def test_nonexistent_player():
    """测试2: 查询一个不存在的玩家"""
    print()
    print("=" * 50)
    print("测试2: 查询不存在的玩家")
    print("=" * 50)

    name = "ThisPlayerDefinitelyDoesNotExist12345XYZ"
    print(f"查询: {name}")
    start = time.time()
    result = query_player(name)
    elapsed = time.time() - start

    if result is None:
        print(f"  ✅ 正确返回 None ({elapsed:.1f}s)")
        return True
    else:
        print(f"  ⚠️ 意外返回了数据: {result} ({elapsed:.1f}s)")
        return False


def test_timeout():
    """测试3: 超时测试（用极短超时模拟）"""
    print()
    print("=" * 50)
    print("测试3: 超时测试 (0.001s 超时)")
    print("=" * 50)

    name = "AshTwoPoint0"
    print(f"查询: {name}")
    start = time.time()
    result = query_player(name, timeout=0.001)
    elapsed = time.time() - start

    if result is None:
        print(f"  ✅ 正确超时 ({elapsed:.1f}s)")
        return True
    else:
        print(f"  ⚠️ 居然没超时: {result} ({elapsed:.1f}s)")
        return True  # 网络极快也不算错


def test_multiple():
    """测试4: 批量查询（模拟8路并发）"""
    print()
    print("=" * 50)
    print("测试4: 批量查询 (模拟并发)")
    print("=" * 50)

    from concurrent.futures import ThreadPoolExecutor, as_completed

    names = [
        "AshTwoPoint0",
        "ThisPlayerDoesNotExist1",
        "ThisPlayerDoesNotExist2",
    ]
    print(f"批量查询 {len(names)} 个玩家...")
    start = time.time()

    results = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(query_player, name): name for name in names}
        for future in as_completed(futures):
            name = futures[future]
            result = future.result()
            results[name] = result
            status = "✅" if result else "❌"
            kd = result["kd"] if result else "N/A"
            print(f"  {status} {name}: KD={kd}")

    elapsed = time.time() - start
    found = sum(1 for v in results.values() if v is not None)
    print(f"  完成: {found}/{len(names)} 查到 ({elapsed:.1f}s)")
    return True


if __name__ == "__main__":
    print("BF6 API 可用性测试")
    print(f"API: {API_BASE}")
    print()

    results = []
    results.append(("真实玩家", test_real_player()))
    results.append(("不存在玩家", test_nonexistent_player()))
    results.append(("超时测试", test_timeout()))
    results.append(("批量查询", test_multiple()))

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
        print("🎉 全部通过！API 可用。")
    else:
        print("⚠️ 部分测试失败，请检查网络或 API 状态。")

    sys.exit(0 if all_pass else 1)
