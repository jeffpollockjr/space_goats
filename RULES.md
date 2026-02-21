# Space Goats Rules

This file contains two rule views:
1. Code-specific rules (exact current engine behavior).
2. Tabletop rules (human-friendly gameplay guide).

## Code-Specific Rules

### Objective

- Win by being the last player with at least 1 ship.

### Setup

1. Player count determines starting ships:
- 2 players: 6 ships each.
- 3 players: 5 ships each.
- 4 players: 4 ships each.
- 5+ players: 3 ships each.
2. Every starting ship begins on `starter_ship_shielded_side`.
3. Each player starts with:
- personal `draw_pile` (starter deck, shuffled),
- personal `discard_pile`,
- `hand` (starts empty),
- `bank` (starts at 0 currency cards),
- fleet of ships.
4. Shared components:
- `AbilitiesPile` (combined Rocket/Shield/Special market cards),
- `market_display` of 4 face-up cards,
- `trash_pile`.
5. Fill empty market slots from `AbilitiesPile` whenever possible.

### Turn Flow

1. Draw to 4 cards.
2. Bank all currency cards from hand (current engine behavior).
3. Discard all debris cards from hand.
4. Choose exactly 1 action:
- buy 1 market card,
- play 1 rocket,
- play 1 shield,
- play 1 special,
- or pass if no valid action.
5. Hand persists between turns. There is no end-of-turn full-hand discard.
6. If a player has `skip_next_turn`, they skip their next full turn (or queued extra turn), then clear the flag.

### Economy and Buying

- Currency can be spent from:
- `bank`,
- remaining currency cards in hand.
- Spending priority is bank first, then hand currency.
- Spent currency cards go to that player's personal `discard_pile`.
- Buy action:
- Buy exactly 1 face-up market card you can afford.
- Bought card normally goes to your personal `discard_pile`.
- Exception: `add_1_ship_to_fleet` (Reinforcement Shuttle) deploys immediately to your fleet as an unshielded ship.
- Refill the bought market slot from `AbilitiesPile`.

### Rocket and Shield Resolution

- Rocket targeting is player-level first (attacker chooses opponent), then defender chooses which ship in their fleet the rocket lands on.
- Reactive block check occurs before rocket resolution:
- A defender may auto-play one card in hand with effect `reactive_block_1_rocket`, `reactive_block_1_rocket_then_trash_1_card_from_hand_or_discard`, or `cancel_1_rocket_targeting_you`.
- All reactive blockers are one-time use and go to `trash_pile` after blocking.
- Piercing interactions:
- `destroy_1_ship_ignore_shields` bypasses assigned shields except `assign_to_ship_block_any`.
- Weak rocket interactions:
- `destroy_1_unshielded_ship` can be absorbed by assigned shields and can flip a starter shielded ship instead of destroying it.
- On assigned shield destruction from hits:
- Destroyed assigned shields go to `trash_pile`.
- `Decoy Drone` (`assign_to_ship_block_1_draw_1_discard_1`) resolves immediately on assignment: draw 1, then discard 1.
- `Salvo Rocket` (`destroy_up_to_2_ships_then_lose_one_1_bank_currency`) performs up to two hits, then the attacker loses 1 bank currency (if available).
- `Twin Salvo` (`destory_up_to_2_ships`) performs up to two hits with no bank-currency drawback.
- `Overload Barrage` (`each_opponent_blocks_2_or_loses_2_ships_and_you_skip_next_turn`) applies 2 hit checks to every opponent, then you skip your next turn.
- `Shatter Rocket` (`destroy_1_ship_then_discard_1_random_card_from_hand`) destroys 1 ship, then the attacker discards 1 random card from hand.
- `Aegis Countermeasure` (`reactive_block_1_rocket_then_trash_1_card_from_hand_or_discard`) blocks reactively, then trashes 1 card from the defender hand/discard (engine picks lowest-value card).
- If a ship has no blocking assigned shield but is on `starter_ship_shielded_side`, it flips to `starter_ship_unshielded_side` and survives.
- If a ship is destroyed while `Last Stand Protocol` is active and that ship is the final ship, the ship survives once and `last_stand` is consumed.
- `strip_all_shields_one_opponent` removes assigned shields from all ships of one opponent (does not change starter ship side).

### Special Card Behavior (Current Engine)

- `draw_3_keep_2_discard_1`: draws up to 3, discards one drawn card, keeps two.
- `retrieve_1_card_from_discard`: retrieves one card from discard to hand (engine auto-selects best by priority).
- `look_at_top3_any_market_rearrange`: rearranges top 3 of `AbilitiesPile` by descending cost.
- `negate_last_ship_loss_once`: enables one-time final-ship save.
- `add_1_ship_to_fleet`: if played from hand (legacy fallback), adds one unshielded ship and the special is trashed.
- `take_extra_turn`: grants one immediate extra turn after current turn and the special is trashed.
- `trash_1_card_from_discard`: trashes one low-value card from your hand or discard (engine auto-selects).
- `trash_1_card_from_discard_draw_1`: trashes one low-value card from your discard only, then draw 1.

### Endgame Rules

- Win check runs after each player turn and extra turn.
- `Unavoidable Ship Wreckage`:
- If exactly 2 players are alive at end of round and no ships were destroyed that round, each duelist takes 1 unavoidable hit (shield HP down, starter side flips, or ship loss if already fully unshielded).
- Draw tiebreak:
- If mutual destruction happens (or no survivors at turn limit), player with highest `bank` wins.
- If tied for highest `bank`, result stays `Draw`.
- Turn limit:
- `max_turns` default is 200.
- If limit is reached with survivors, winner is survivor with most ships.
- If tied on ships at turn limit, current engine keeps Python `max` tie behavior (earliest survivor in player order).

## Tabletop Rules

### Objective

- Be the last player with ships remaining.

### Components

- Personal area per player:
- draw pile,
- discard pile,
- hand,
- banked currency pile,
- fleet of ships.
- Shared area:
- `AbilitiesPile` (combined Rocket/Shield/Special market deck),
- 4-card face-up market display (refilled from `AbilitiesPile`),
- trash pile.
- Physical box target (current build):
- 45 starter cards (9 per player x up to 5 players),
- 16 ship cards,
- 43 market cards,
- 104 total cards.

### Setup

1. Give each player the same 9-card starter deck and shuffle it.
2. Set starting ships by player count:
- 2 players: 6 ships each.
- 3 players: 5 ships each.
- 4 players: 4 ships each.
- 5 players: 3 ships each.
3. Put all starting ships in play on their shielded side.
4. Set each bank to 0.
5. Build `AbilitiesPile`, shuffle, reveal 4 face-up market cards.

### On Your Turn

1. Draw until you have 4 cards in hand.
2. Move currency cards from hand to your bank.
3. Discard debris in hand.
4. Take exactly one action:
- Buy 1 card from the market.
- Play 1 rocket.
- Play 1 shield.
- Play 1 special.
- Pass.
5. End turn. Keep unplayed cards in hand.

### Buying

- Spend from bank and/or currency in hand.
- Spent currency goes to your personal discard pile.
- Bought cards go to your personal discard pile, except Reinforcement Shuttle.
- Reinforcement Shuttle is deployed immediately to your fleet as an unshielded ship.
- Refill the bought market slot from `AbilitiesPile`.

### Combat Basics

- Rockets target opponents.
- The defending player chooses which of their ships the rocket lands on.
- Ships on shielded starter side absorb one hit by flipping to unshielded side.
- Assigned shields absorb hits first.
- Broken assigned shields are trashed.
- Reactive shield cards from hand block a rocket, then are trashed.
- Aegis Countermeasure additionally trashes 1 card from your hand/discard after it blocks.
- Some rockets bypass normal shields.
- Salvo Rocket now has a drawback: after resolving its two hits, you lose 1 bank currency if possible.
- Twin Salvo remains the clean double-strike (no bank-currency loss).
- Overload Barrage pressures all opponents with two hits each, but you skip your next turn.
- Decoy Drone draws 1 then discards 1 immediately when assigned.
- Shatter Rocket destroys 1 ship, then the attacker discards 1 random card from hand.

### Specials and Trashing

- Trashed cards are removed from the game and do not return to deck/discard.
- Warp Drive is one-time use (trashed after play).
- Reinforcement Shuttle is effectively one-time use as a direct fleet deploy purchase.
- Deck Purge trashes 1 card from your hand or discard (chosen by engine priority in simulation).

### Duel Anti-Stall Rule

- `Unavoidable Ship Wreckage` applies only when exactly 2 players remain.
- After both players finish a round, if no ship was destroyed that round, each player must take 1 unavoidable hit on their own fleet.

### Draw Resolution

- If both sides are destroyed at once, compare bank currency:
- Highest bank wins.
- If bank is tied, it is a draw.
