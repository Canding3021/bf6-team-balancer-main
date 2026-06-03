"""
pytest 配置：把仓库根目录加入 sys.path，使 tests/ 下的用例能 import bf6balancer 包。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
