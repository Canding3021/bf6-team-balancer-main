"""
API 偏移/应用逻辑单测 - 纯逻辑，不打网络。
Run: python -m pytest test_api_logic.py -v

覆盖 api_query.py 中不依赖 HTTP 的部分:
- _compute_offsets: 样本充足 / 样本不足(<=50%) / 无可用 ratio
- apply_results_to_players: API命中 / 偏移修正 / 偏移冻结 三分支
"""

import pytest
from bf6balancer.core.api_query import _compute_offsets, apply_results_to_players, LEGACY_OFFSET


def _player(name, eaid="", kd_raw=1.0, kpm_raw=1.0):
    """构造 extract_players() 风格的玩家 dict。"""
    return {
        "name": name,
        "eaid": eaid,
        "kd_raw": kd_raw,
        "kpm_raw": kpm_raw,
        "kd": kd_raw,
        "kpm_adjusted": kpm_raw,
    }


# -- _compute_offsets --------------------------------------------

class TestComputeOffsets:
    def test_sample_sufficient_uses_avg_ratio(self):
        """查到 > 一半时，offset 直接取 ratio 均值。"""
        players = [_player(f"P{i}", eaid=f"e{i}", kd_raw=1.0, kpm_raw=1.0) for i in range(4)]
        # 4 人全查到，api = 2x excel → ratio 恒为 2.0
        api_results = {f"e{i}": {"kd": 2.0, "kpm": 2.0} for i in range(4)}
        stats = {"found": 4}

        offset_kd, offset_kpm, warning = _compute_offsets(players, api_results, stats)

        assert offset_kd == pytest.approx(2.0)
        assert offset_kpm == pytest.approx(2.0)
        assert warning is None

    def test_sample_insufficient_blends_with_legacy(self):
        """查到 <= 一半时，offset 与 legacy 取均值，并给出 warning。"""
        players = [_player(f"P{i}", eaid=f"e{i}", kd_raw=1.0, kpm_raw=1.0) for i in range(4)]
        # 只有 1 个查到 (<=2)，ratio = 3.0
        api_results = {"e0": {"kd": 3.0, "kpm": 3.0}}
        stats = {"found": 1}

        offset_kd, offset_kpm, warning = _compute_offsets(players, api_results, stats)

        expected = (3.0 + LEGACY_OFFSET) / 2
        assert offset_kd == pytest.approx(expected)
        assert offset_kpm == pytest.approx(expected)
        assert warning is not None and "1/4" in warning

    def test_no_usable_ratio_falls_back_to_legacy(self):
        """没有任何可计算 ratio 时，回退 legacy 偏移。"""
        players = [_player("P0", eaid="e0", kd_raw=None, kpm_raw=None)]
        api_results = {}  # 没查到
        stats = {"found": 0}

        offset_kd, offset_kpm, warning = _compute_offsets(players, api_results, stats)

        assert offset_kd == LEGACY_OFFSET
        assert offset_kpm == LEGACY_OFFSET
        assert warning is not None

    def test_zero_excel_value_skipped_in_ratio(self):
        """Excel 值为 0 的玩家不参与 ratio（避免除零）。"""
        players = [
            _player("P0", eaid="e0", kd_raw=0.0, kpm_raw=2.0),
            _player("P1", eaid="e1", kd_raw=1.0, kpm_raw=1.0),
        ]
        api_results = {
            "e0": {"kd": 5.0, "kpm": 4.0},  # kd_raw=0 → 跳过 kd ratio
            "e1": {"kd": 2.0, "kpm": 2.0},
        }
        stats = {"found": 2}

        offset_kd, offset_kpm, _ = _compute_offsets(players, api_results, stats)

        # kd ratio 仅来自 P1 = 2.0/1.0 = 2.0
        assert offset_kd == pytest.approx(2.0)
        # kpm ratio: P0=4/2=2.0, P1=2/1=2.0 → 均值 2.0
        assert offset_kpm == pytest.approx(2.0)


# -- apply_results_to_players ------------------------------------

class TestApplyResults:
    def test_api_hit_uses_real_values(self):
        players = [_player("P0", eaid="e0", kd_raw=1.0, kpm_raw=1.0)]
        result = {
            "api_results": {"e0": {"kd": 3.5, "kpm": 2.2}},
            "offset_kd": 1.3, "offset_kpm": 1.3,
        }
        apply_results_to_players(players, result)

        assert players[0]["kd"] == 3.5
        assert players[0]["kpm_adjusted"] == 2.2

    def test_api_miss_applies_dynamic_offset(self):
        players = [_player("P0", eaid="e0", kd_raw=2.0, kpm_raw=1.0)]
        result = {
            "api_results": {"e0": None},
            "offset_kd": 1.5, "offset_kpm": 2.0,
        }
        apply_results_to_players(players, result)

        assert players[0]["kd"] == pytest.approx(3.0)       # 2.0 * 1.5
        assert players[0]["kpm_adjusted"] == pytest.approx(2.0)  # 1.0 * 2.0

    def test_api_miss_frozen_offset_uses_raw(self):
        """偏移冻结 (offset 为 None) 时，未命中玩家用 Excel 原始值。"""
        players = [_player("P0", eaid="e0", kd_raw=2.5, kpm_raw=1.7)]
        result = {
            "api_results": {"e0": None},
            "offset_kd": None, "offset_kpm": None,
        }
        apply_results_to_players(players, result)

        assert players[0]["kd"] == 2.5
        assert players[0]["kpm_adjusted"] == 1.7

    def test_no_eaid_player_with_offset(self):
        """无 EAID 的玩家（不在 api_results 中）走偏移分支。"""
        players = [_player("P0", eaid="", kd_raw=1.0, kpm_raw=1.0)]
        result = {"api_results": {}, "offset_kd": 1.3, "offset_kpm": 1.3}
        apply_results_to_players(players, result)

        assert players[0]["kd"] == pytest.approx(1.3)
        assert players[0]["kpm_adjusted"] == pytest.approx(1.3)

    def test_none_raw_values_stay_none_with_offset(self):
        """kd_raw/kpm_raw 为 None 时，偏移分支保持 None 不报错。"""
        players = [_player("P0", eaid="e0", kd_raw=None, kpm_raw=None)]
        result = {"api_results": {"e0": None}, "offset_kd": 1.3, "offset_kpm": 1.3}
        apply_results_to_players(players, result)

        assert players[0]["kd"] is None
        assert players[0]["kpm_adjusted"] is None
