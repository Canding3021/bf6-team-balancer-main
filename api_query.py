"""
BF6 Team Balancer - API 查询模块

通过 gametools.network 查询玩家真实 KD/KPM，
并根据查询结果动态计算偏移系数。
"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable

API_BASE = "https://api.gametools.network/bf6/stats/"
DEFAULT_TIMEOUT = 10
DEFAULT_BATCH_SIZE = 8
LEGACY_OFFSET = 1.313


def query_single(eaid: str, platform: str = "pc",
                 timeout: int = DEFAULT_TIMEOUT) -> Optional[dict]:
    """
    查询单个玩家的真实 KD/KPM。

    Args:
        eaid: EA 用户名
        platform: 平台 (pc/ea/psn/xbox)
        timeout: 请求超时秒数

    Returns:
        成功: {"kd": float, "kpm": float}
        失败: None (超时/404/网络错误/解析错误)
    """
    params = {
        "name": eaid,
        "platform": platform,
        "format_values": "false",
        "lang": "en-us",
    }
    try:
        resp = requests.get(API_BASE, params=params, timeout=timeout)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()

        # 检查是否有有效数据
        if data.get("hasResults") is False:
            return None
        if "userName" not in data or "kills" not in data:
            return None
        if data.get("errors"):
            return None

        kd = data.get("killDeath")
        kpm = data.get("killsPerMinute")

        if kd is None and kpm is None:
            return None

        return {
            "kd": float(kd) if kd is not None else 0.0,
            "kpm": float(kpm) if kpm is not None else 0.0,
        }
    except (requests.Timeout, requests.RequestException, ValueError, KeyError):
        return None


def query_all(
    players_data: list[dict],
    platform: str = "pc",
    batch_size: int = DEFAULT_BATCH_SIZE,
    timeout: int = DEFAULT_TIMEOUT,
    progress_callback: Optional[Callable[[int, int, dict], None]] = None,
) -> dict:
    """
    批量查询所有玩家，计算偏移系数。

    Args:
        players_data: extract_players() 返回的 dict 列表，
                      每个 dict 必须有 "name", "kd", "kpm_raw", "eaid" 键
        platform: 平台
        batch_size: 并发数
        timeout: 单个请求超时秒数
        progress_callback: 回调函数 (已完成数, 总数, {"found": n, "not_found": n, "failed": n})

    Returns:
        {
            "api_results": {eaid: {"kd": float, "kpm": float} | None, ...},
            "offset_kd": float,
            "offset_kpm": float,
            "found": int,
            "not_found": int,
            "failed": int,
            "warning": str | None,
        }
    """
    total = len(players_data)
    # Keyed by EAID to avoid collision when duplicate player names exist
    api_results: dict[str, Optional[dict]] = {}
    stats = {"found": 0, "not_found": 0, "no_eaid": 0}
    completed = 0

    # 用线程池并发查询
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        futures = {}
        for p in players_data:
            eaid = p.get("eaid", "")
            if not eaid:
                stats["no_eaid"] += 1
                completed += 1
                if progress_callback:
                    progress_callback(completed, total, stats)
                continue
            future = executor.submit(query_single, eaid, platform, timeout)
            futures[future] = p

        for future in as_completed(futures):
            p = futures[future]
            eaid = p.get("eaid", "")
            result = future.result()
            api_results[eaid] = result

            if result is not None:
                stats["found"] += 1
            else:
                stats["not_found"] += 1

            completed += 1
            if progress_callback:
                progress_callback(completed, total, stats)

    # 计算偏移系数
    offset_kd, offset_kpm, warning = _compute_offsets(
        players_data, api_results, stats
    )

    return {
        "api_results": api_results,
        "offset_kd": offset_kd,
        "offset_kpm": offset_kpm,
        "found": stats["found"],
        "not_found": stats["not_found"],
        "no_eaid": stats["no_eaid"],
        "warning": warning,
    }


def _compute_offsets(
    players_data: list[dict],
    api_results: dict[str, Optional[dict]],
    stats: dict,
) -> tuple[float, float, Optional[str]]:
    """
    根据 API 查询结果计算 KD/KPM 偏移系数。

    规则:
    - 收集所有"API查到了且Excel有值"的玩家，算 ratio = api / excel
    - 能查到的 > 50%: offset = avg(ratios)（样本充足，直接用）
    - 能查到的 ≤ 50%: offset = (avg(ratios) + 1.313) / 2（样本不足，与legacy混合）

    Returns:
        (offset_kd, offset_kpm, warning_or_None)
    """
    ratios_kd = []
    ratios_kpm = []

    for p in players_data:
        eaid = p.get("eaid", "")
        api = api_results.get(eaid)
        if api is None:
            continue

        excel_kd = p.get("kd_raw")
        excel_kpm = p.get("kpm_raw")

        # KD 偏移
        if api["kd"] is not None and excel_kd is not None and excel_kd > 0:
            ratios_kd.append(api["kd"] / excel_kd)

        # KPM 偏移
        if api["kpm"] is not None and excel_kpm is not None and excel_kpm > 0:
            ratios_kpm.append(api["kpm"] / excel_kpm)

    total = len(players_data)
    found = stats["found"]
    warning = None

    # 没有任何可计算的 ratio，直接用 legacy 偏移
    if not ratios_kd and not ratios_kpm:
        return LEGACY_OFFSET, LEGACY_OFFSET, "无法计算偏移系数，使用默认值 1.313"

    # 计算平均 ratio
    avg_kd = sum(ratios_kd) / len(ratios_kd) if ratios_kd else LEGACY_OFFSET
    avg_kpm = sum(ratios_kpm) / len(ratios_kpm) if ratios_kpm else LEGACY_OFFSET

    # 判断是否超过一半查不到
    if found <= total // 2:
        warning = f"仅查到 {found}/{total} 人，偏移系数可能不准"
        offset_kd = (avg_kd + LEGACY_OFFSET) / 2
        offset_kpm = (avg_kpm + LEGACY_OFFSET) / 2
    else:
        offset_kd = avg_kd
        offset_kpm = avg_kpm

    return offset_kd, offset_kpm, warning
