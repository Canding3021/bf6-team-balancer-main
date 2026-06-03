"""BF6 Team Balancer - UI 常量：字体、名称映射、页面导航。"""

FONT_FAMILY = "Microsoft YaHei UI, Microsoft YaHei, PingFang SC, sans-serif"

# Mode name mappings (shared across display, copy, history)
ALLOC_MODE_NAMES = {"balanced": "均衡", "random": "随机"}
GAME_MODE_NAMES = {"conquest": "征服", "breakthrough": "突破"}

# -- Page navigation ----------------------------------------------
# Page indices in the QStackedWidget. The wizard flows linearly through
# _MAIN_FLOW; HISTORY is a side branch (reachable from RESULT, returns to ACTION)
# and has no step indicator of its own.
PAGE_IMPORT = 0
PAGE_API = 1
PAGE_ALLOC = 2
PAGE_GAME = 3
PAGE_SQUAD = 4
PAGE_RESULT = 5
PAGE_HISTORY = 6
PAGE_ACTION = 7

# Linear wizard order (HISTORY excluded — it's a side branch).
_MAIN_FLOW = [PAGE_IMPORT, PAGE_API, PAGE_ALLOC, PAGE_GAME, PAGE_SQUAD, PAGE_RESULT, PAGE_ACTION]

# Page -> step indicator index. HISTORY shares RESULT's indicator slot.
NUM_STEPS = 7
PAGE_TO_STEP = {
    PAGE_IMPORT: 0, PAGE_API: 1, PAGE_ALLOC: 2, PAGE_GAME: 3,
    PAGE_SQUAD: 4, PAGE_RESULT: 5, PAGE_HISTORY: 5, PAGE_ACTION: 6,
}
# Step indicator index that gets struck through when game mode is skipped (random).
SKIPPED_STEP_RANDOM = PAGE_TO_STEP[PAGE_GAME]
