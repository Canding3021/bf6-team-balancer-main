# BF6 Team Balancer

English | [中文](README.md)

A team balancing tool for Battlefield 6 in-house matches. Automatically balances teams and squads based on player KD and KPM data, with an option for pure random allocation.

## Features

- Import player data from Excel files (Nickname, KD, KPM, EAID)
- **API Auto Query**: Automatically fetch real KD/KPM via EAID — no need to manually enter accurate stats (dual sources: gametools.network + joarchy.com)
- **Dynamic Offset Correction**: Auto-calculate offset coefficient from queried data; players without API data use Excel data with correction
- **Offset Coefficient Freeze**: Auto-freeze offset when API coverage ≥ 80%, avoiding inaccurate offset from small samples
- **Two Allocation Modes**: Balanced (by skill) / Random (pure random)
- Two game modes: Conquest (KD-focused) / Rush (KPM-focused)
- Custom squad binding (lock two players to the same team)
- Greedy algorithm for balanced team allocation (Balanced mode)
- Standby team auto-draft (ABAB from head/tail)
- Allocation results + balance analysis report
- 5 color themes (Midnight Gray / Ocean Blue / Dark Green / Crimson / Monochrome), selection auto-saved

## Usage

### Option 1: Run the EXE

1. Open `dist\BF6TeamBalancer\BF6TeamBalancer.exe`
2. Follow the UI: Import Excel → API Query → Choose Allocation Mode → Set Bindings → View Results

### Option 2: Run from Source

```bash
pip install PyQt5 openpyxl requests
python ui_prototype.py
```

## Excel Format

Fixed 4 columns, first row is the header, data starts from the second row:

| Col 1 | Col 2 | Col 3 | Col 4 |
|-------|-------|-------|-------|
| Nickname | KD | KPM | EAID |

- **Nickname**: Player's in-game name
- **KD / KPM**: Data from platforms like Xiaoheihe (used as fallback)
- **EAID**: Player's EA username (used for API stat lookup)

Example:
```
Nickname    KD      KPM     EAID
Jin         3.47    2.31    JinBF6
SanSan      0.20    0.10    SanSanBF6
```

## Project Structure

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
├── README.md            # Chinese documentation
├── README_EN.md         # This file
├── TECH_DOC.md          # Technical documentation
└── .gitignore           # Git ignore rules
```

## Tech Stack

- Python 3.9+
- PyQt5 (GUI)
- openpyxl (Excel parsing)
- requests (HTTP requests for API queries)
- PyInstaller (packaging)
