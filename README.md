# BF6 Team Balancer

[English](README_EN.md) | 中文

战地风云6服务器内战分队工具。根据玩家的KD和KPM数据，自动均衡分配阵营和小队，也支持纯随机分配。

## 功能

- 从Excel文件导入玩家数据（昵称、KD、KPM、EAID）
- **API 自动查询**：通过 EAID 自动获取玩家真实 KD/KPM，无需手动填入准确数据（双源查询：gametools.network + joarchy.com）
- **动态偏移修正**：根据查到的玩家数据自动计算偏移系数，查不到的玩家用 Excel 数据自动修正
- **偏移系数冻结**：API 覆盖率 ≥ 80% 时自动冻结偏移系数，避免小样本偏移不准
- **两种分配模式：均衡（按实力）/ 随机（纯随机）**
- 支持两种游戏模式：征服（侧重KD）/ 突破（侧重KPM）
- 自定义小队绑定（两人绑定到同一阵营）
- 贪心算法均衡分配阵营（均衡模式）
- 候补队伍自动抽取（首尾ABAB）
- 分队结果 + 均衡性分析报告
- 5 套颜色主题（暗夜灰 / 深海蓝 / 墨绿 / 暗红 / 黑白纯色），选择自动保存

## 使用方法

### 方式一：直接运行exe

1. 打开 `dist\BF6TeamBalancer\BF6TeamBalancer.exe`
2. 按界面提示操作：导入Excel → API查询 → 选择分配模式 → 设置绑定 → 查看结果

### 方式二：源码运行

```bash
pip install PyQt5 openpyxl requests
python ui_prototype.py
```

## Excel格式要求

固定四列，第一行为表头，数据从第二行开始：

| 列1 | 列2 | 列3 | 列4 |
|---|---|---|---|
| 昵称 | KD | KPM | EAID |

- **昵称**：玩家游戏昵称
- **KD / KPM**：来自小黑盒等平台的数据（作为 fallback）
- **EAID**：玩家的 EA 用户名（用于 API 查询真实战绩）

示例：
```
昵称    KD      KPM     EAID
阿金    3.47    2.31    JinBF6
叁叁    0.20    0.10    SanSanBF6
```

## 项目结构

```
bf6-team-balancer/
├── ui_prototype.py      # GUI main (PyQt5)
├── extract.py           # Excel parser (4-column format)
├── api_query.py         # API query module (gametools.network + joarchy.com)
├── history.py           # History & config storage
├── test_algorithm.py    # Algorithm tests (pytest)
├── test_api.py          # API availability test
├── core/
│   ├── __init__.py
│   └── algorithm.py     # Core allocation algorithm
├── requirements.txt     # Runtime dependencies
├── requirements-dev.txt # Dev dependencies (pyinstaller, pytest)
├── CHANGELOG.md         # Version changelog
├── README.md            # This file (Chinese)
├── README_EN.md         # English documentation
├── TECH_DOC.md          # Technical documentation
└── .gitignore           # Git ignore rules
```

## 技术栈

- Python 3.9+
- PyQt5（GUI）
- openpyxl（Excel解析）
- requests（HTTP 请求，用于 API 查询）
- PyInstaller（打包）
