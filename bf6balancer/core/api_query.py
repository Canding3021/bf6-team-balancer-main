"""
BF6 Team Balancer - API 查询模块

通过 gametools.network 查询玩家真实 KD/KPM，
并通过 joarchy.com 获取修正后的 KPM（去除非战斗时间）。

查询策略:
1. gametools 作为主查询源（稳定，KD 准确）
2. joarchy 作为 KPM 修正源（KPM 更准确，去掉了挂机/菜单时间）
3. gametools 查不到的玩家，用 joarchy 兜底
"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable

# gametools.network
GAMETOOLS_BASE = "https://api.gametools.network/bf6/stats/"
GAMETOOLS_TIMEOUT = 10

# joarchy.com (BF6 Tracker API)
JOARCHY_BASE = "https://api-btr-joo-uk.joarchy.com"
JOARCHY_BACKUP = "https://api-btr-joo-us.joarchy.com"
JOARCHY_TIMEOUT = 12

DEFAULT_BATCH_SIZE = 8
LEGACY_OFFSET = 1.313


# ── gametools.network 查询 ────────────────────────────────────────

def _query_gametools(eaid: str, platform: str = "pc",
                     timeout: int = GAMETOOLS_TIMEOUT) -> Optional[dict]:
    """
    通过 gametools.network 查询单个玩家。

    Returns:
        成功: {"kd": float, "kpm": float, "userId": str | None}
        失败: None
    """
    params = {
        "name": eaid,
        "platform": platform,
        "format_values": "false",
        "lang": "en-us",
    }
    try:
        resp = requests.get(GAMETOOLS_BASE, params=params, timeout=timeout)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()

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
            "userId": str(data.get("userId", "")) if data.get("userId") else None,
        }
    except (requests.Timeout, requests.RequestException, ValueError, KeyError):
        return None


# ── joarchy.com 查询 ─────────────────────────────────────────────

def _query_joarchy(identifier: Optional[str] = None,
                   name: Optional[str] = None,
                   platform: str = "pc",
                   timeout: int = JOARCHY_TIMEOUT) -> Optional[dict]:
    """
    通过 joarchy.com 查询单个玩家，获取修正后的 KPM。

    Args:
        identifier: EA platformUserIdentifier（优先，稳定）
        name: 玩家名（identifier 没有时用这个）
        platform: 平台
        timeout: 超时秒数

    Returns:
        成功: {"kd": float, "kpm": float}
        失败: None
    """
    params = {"platform": platform}
    if identifier:
        params["identifier"] = identifier
    elif name:
        params["name"] = name
    else:
        return None

    # 先试主节点，失败试备用节点
    for base in [JOARCHY_BASE, JOARCHY_BACKUP]:
        try:
            resp = requests.get(f"{base}/v2/profile", params=params, timeout=timeout)
            if resp.status_code != 200:
                continue
            data = resp.json()
            stats = data.get("stats", {})
            if not stats:
                continue

            kd = stats.get("killDeath")
            kpm = stats.get("killsPerMinute")

            if kd is None and kpm is None:
                continue

            return {
                "kd": float(kd) if kd is not None else 0.0,
                "kpm": float(kpm) if kpm is not None else 0.0,
            }
        except (requests.Timeout, requests.RequestException, ValueError, KeyError):
            continue

    return None


# ── 批量查询 ─────────────────────────────────────────────────────

def query_all(
    players_data: list[dict],
    platform: str = "pc",
    batch_size: int = DEFAULT_BATCH_SIZE,
    timeout: int = GAMETOOLS_TIMEOUT,
    progress_callback: Optional[Callable[[int, int, dict], None]] = None,
) -> dict:
    """
    批量查询所有玩家，计算偏移系数。

    查询策略:
    1. 并发查 gametools，获取 KD + userId
    2. 用 userId 并发查 joarchy，获取修正 KPM
    3. gametools 查不到的，用 joarchy name 查询兜底
    4. 合并结果: KD 取 gametools，KPM 优先取 joarchy

    Args:
        players_data: extract_players() 返回的 dict 列表
        platform: 平台
        batch_size: 并发数
        timeout: 单个请求超时秒数
        progress_callback: 回调函数 (已完成数, 总数, stats_dict)

    Returns:
        {
            "api_results": {eaid: {"kd": float, "kpm": float} | None, ...},
            "offset_kd": float,
            "offset_kpm": float,
            "found": int,
            "not_found": int,
            "no_eaid": int,
            "warning": str | None,
        }
    """
    total = len(players_data)
    api_results: dict[str, Optional[dict]] = {}
    stats = {"found": 0, "not_found": 0, "no_eaid": 0}
    completed = 0

    # ── Step 1: gametools 并发查询 ────────────────────────────
    gametools_results: dict[str, Optional[dict]] = {}
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
            future = executor.submit(_query_gametools, eaid, platform, timeout)
            futures[future] = p

        for future in as_completed(futures):
            p = futures[future]
            eaid = p.get("eaid", "")
            result = future.result()
            gametools_results[eaid] = result

            if result is not None:
                stats["found"] += 1
            else:
                stats["not_found"] += 1

            completed += 1
            if progress_callback:
                progress_callback(completed, total, stats)

    # ── Step 2: joarchy 并发查询（用 userId） ─────────────────
    # 收集 gametools 查到的 userId
    joarchy_by_id: dict[str, Optional[dict]] = {}  # eaid -> joarchy result
    eaid_to_userid: dict[str, str] = {}

    for eaid, gt_result in gametools_results.items():
        if gt_result and gt_result.get("userId"):
            eaid_to_userid[eaid] = gt_result["userId"]

    joarchy_total = len(eaid_to_userid) + len([
        eaid for eaid, gt in gametools_results.items() if gt is None
    ])
    joarchy_completed = 0

    if eaid_to_userid:
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = {}
            for eaid, userid in eaid_to_userid.items():
                future = executor.submit(
                    _query_joarchy, identifier=userid, platform=platform
                )
                futures[future] = eaid

            for future in as_completed(futures):
                eaid = futures[future]
                joarchy_by_id[eaid] = future.result()
                joarchy_completed += 1
                if progress_callback:
                    progress_callback(
                        total + joarchy_completed, total + joarchy_total,
                        {**stats, "phase": "joarchy_id"}
                    )

    # ── Step 3: joarchy 兜底查询（gametools 查不到的，用 name） ──
    joarchy_fallback: dict[str, Optional[dict]] = {}
    not_found_eaids = [
        eaid for eaid, gt in gametools_results.items() if gt is None
    ]

    if not_found_eaids:
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = {}
            for eaid in not_found_eaids:
                future = executor.submit(
                    _query_joarchy, name=eaid, platform=platform
                )
                futures[future] = eaid

            for future in as_completed(futures):
                eaid = futures[future]
                result = future.result()
                joarchy_fallback[eaid] = result
                joarchy_completed += 1
                if result is not None:
                    # joarchy 兜底成功，更新统计
                    stats["found"] += 1
                    stats["not_found"] -= 1
                if progress_callback:
                    progress_callback(
                        total + joarchy_completed, total + joarchy_total,
                        {**stats, "phase": "joarchy_fb"}
                    )

    # ── Step 4: 合并结果 ─────────────────────────────────────
    # KD 取 gametools，KPM 优先取 joarchy
    # 同时保留 gametools 原始 KPM 用于偏移系数计算（不混入 joarchy 值）
    gametools_only_results: dict[str, Optional[dict]] = {}

    for eaid, gt_result in gametools_results.items():
        joarchy_id_result = joarchy_by_id.get(eaid)
        joarchy_fb_result = joarchy_fallback.get(eaid)

        if gt_result is not None:
            # gametools 查到了
            kd = gt_result["kd"]
            # KPM: joarchy (by identifier) > joarchy (by name) > gametools
            if joarchy_id_result and joarchy_id_result.get("kpm") is not None:
                kpm = joarchy_id_result["kpm"]
            elif joarchy_fb_result and joarchy_fb_result.get("kpm") is not None:
                kpm = joarchy_fb_result["kpm"]
            else:
                kpm = gt_result["kpm"]
            api_results[eaid] = {"kd": kd, "kpm": kpm}
            # 保留 gametools 原始值用于偏移计算
            gametools_only_results[eaid] = gt_result
        elif joarchy_fb_result is not None:
            # gametools 查不到，joarchy 兜底成功
            api_results[eaid] = {
                "kd": joarchy_fb_result["kd"],
                "kpm": joarchy_fb_result["kpm"],
            }
            gametools_only_results[eaid] = None
        else:
            # 两边都没查到
            api_results[eaid] = None
            gametools_only_results[eaid] = None

    # ── Step 5: 计算偏移系数 ──────────────────────────────────
    # 如果 joarchy 覆盖率 ≥ 80%，冻结偏移系数（不参与计算）
    total_with_eaid = total - stats["no_eaid"]
    found_total = stats["found"]
    coverage = found_total / total_with_eaid if total_with_eaid > 0 else 0

    if coverage >= 0.8:
        # 覆盖率足够高，冻结偏移系数
        offset_kd, offset_kpm = None, None
        warning = None
        if coverage < 1.0:
            unfound = total_with_eaid - found_total
            warning = f"已查到 {found_total}/{total_with_eaid} 人（{coverage:.0%}），{unfound} 人使用 Excel 原始数据"
    else:
        # 覆盖率不足，正常计算偏移系数（仅用 gametools 数据）
        offset_kd, offset_kpm, warning = _compute_offsets(
            players_data, gametools_only_results, stats
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


def apply_results_to_players(players_data: list[dict], result: dict) -> None:
    """
    将 query_all() 的结果写回玩家数据（原地修改 players_data）。

    对每个玩家更新 kd / kpm_adjusted 字段，规则:
    - API 查到了: 直接用真实值
    - 没查到且偏移系数有效: 用 Excel 原始值 × 动态偏移
    - 没查到且偏移系数冻结 (offset 为 None): 直接用 Excel 原始值

    这是 _on_api_finished 里原本内联的业务逻辑，抽出来便于脱离 UI 单测。
    """
    offset_kd = result.get("offset_kd")
    offset_kpm = result.get("offset_kpm")
    api_results = result.get("api_results", {})

    for p in players_data:
        eaid = p.get("eaid", "")
        api = api_results.get(eaid)
        if api is not None:
            # API 查到了: 用真实值
            p["kd"] = api["kd"]
            p["kpm_adjusted"] = api["kpm"]
        elif offset_kd is not None:
            # 未查到，偏移系数有效: Excel 原始值 × 偏移
            p["kd"] = round(p["kd_raw"] * offset_kd, 2) if p["kd_raw"] is not None else None
            p["kpm_adjusted"] = round(p["kpm_raw"] * offset_kpm, 2) if p["kpm_raw"] is not None else None
        else:
            # 未查到，偏移冻结: 用 Excel 原始值
            p["kd"] = p["kd_raw"]
            p["kpm_adjusted"] = p["kpm_raw"]


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
