# Space Goats Simulation

A Python simulation for the Space Goats card game.

Current rules model:
- One shared `AbilitiesPile` market deck (3 face-up cards).
- Players draw to 5, may bank currency, then take exactly one action each turn.
- Actions: buy 1 card, play 1 shield, play 1 rocket, or play 1 special.

## Setup

1. **Install dependencies:**
   ```bash
   pip install pandas openpyxl
   ```

2. **Add your data file:**
   Place `Space_Goats_V1_Card_Deck2.xlsx` inside the `data/` folder.

## File Structure

```
space_goats_sim/
├── data/
│   └── Space_Goats_V1_Card_Deck2.xlsx
├── cards.py        # Loads starter deck + AbilitiesPile data from Excel
├── game.py         # Turn logic, market display, combat/effect resolution
├── simulation.py   # Runs N games and prints win statistics
├── main.py         # Runs a single game with full log output
├── update_abilities_pile.py  # Rebalances Rocket/Shield/Special market sheets
└── README.md
```

## Usage

**Run a single game (with full log):**
```bash
python main.py
```

**Run a full simulation (1000 games, 4 players):**
```bash
python simulation.py
```

You can edit `simulation.py` to change the number of games or players:
```python
run_simulation(num_games=500, num_players=3)
```
