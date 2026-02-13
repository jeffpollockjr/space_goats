# Space Goats Rules

This file contains two rule views:
1. Code-specific rules (exact current engine behavior).
2. Tabletop rules (human-friendly gameplay guide).

## Code-Specific Rules

### Objective

- Win by being the last player with at least 1 ship.

### Setup

1. Player count determines starting ships:
- 2-3 players: 7 ships each.
- 4-5 players: 6 ships each.
- 6+ players: 5 ships each.
2. Each player starts with:
- personal `draw_pile` (starter deck, shuffled),
- personal `discard_pile`,
- `hand` (starts empty),
- `bank` (starts at 0 currency cards),
- fleet of ships.
3. Shared components:
- `AbilitiesPile` (combined Rocket/Shield/Special market cards),
- `market_display` of 3 face-up cards,
- `trash_pile`.
4. Fill empty market slots from `AbilitiesPile` whenever possible.

### Turn Flow

1. Draw to 5 cards.
2. Bank all currency cards from hand (AI behavior in current code).
3. Discard all debris cards from hand.
4. Choose exactly 1 action:
- buy 1 market card,
- play 1 rocket,
- play 1 shield,
- play 1 special,
- or pass if no valid action.
5. Hand persists between turns. There is no end-of-turn full-hand discard.

### Economy and Buying

- Currency can be spent from:
- `bank`,
- remaining currency cards in hand.
- Buy action:
- Buy exactly 1 face-up market card you can afford.
- Bought card goes to your personal `discard_pile`.
- Refill that market slot from `AbilitiesPile`.

### Rocket and Shield Resolution

- Rocket targeting is player-level first (attacker chooses opponent), then defender chooses which ship in their fleet the rocket lands on.
- Reactive block check occurs before rocket resolution:
- A defender may auto-play one card in hand with effect `reactive_block_1_rocket` or `cancel_1_rocket_targeting_you`.
- `Emergency Thrusters` and `Aegis Countermeasure` are trashed after reactive use.
- Other reactive blockers are discarded after use.
- Weak rocket (`destroy_1_unshielded_ship`) only works if target has at least one unshielded ship.
- Piercing interactions:
- `destroy_1_ship_ignore_shields` bypasses shields except `assign_to_ship_block_any`.
- On shield destruction from hits:
- `Hull Plating` goes to that player's `discard_pile`.
- Other destroyed assigned shields go to `trash_pile`.
- If a ship is destroyed while `Last Stand Protocol` is active and that ship is the final ship, the ship survives once and `last_stand` is consumed.

### Special Card Behavior (Current Engine)

- `draw_3_keep_2_discard_1`: draws up to 3, discards one drawn card, keeps two.
- `retrieve_1_card_from_discard`: retrieves one card from discard to hand.
- `negate_last_ship_loss_once`: enables one-time final-ship save.
- `add_1_ship_to_fleet`: adds one ship immediately; this card is trashed after play.
- `take_extra_turn`: grants one immediate extra turn after current turn.
- `look_at_top3_any_market_rearrange`: rearranges top 3 of `AbilitiesPile` by descending cost.
- `trash_1_card_from_discard`: trashes one low-value card from your discard.
- `trash_1_card_from_discard_draw_1`: same as above, then draw 1.

### Endgame Rules

- Win check runs after each player turn and extra turn.
- `Unavoidable Ship Wreckage`:
- If exactly 2 players are alive at end of round and no ships were destroyed that round, each duelist loses 1 ship unavoidably.
- Draw tiebreak:
- If mutual destruction happens, player with highest `bank` wins.
- If tied for highest `bank`, result stays `Draw`.
- Turn limit:
- `max_turns` default is 200.
- If limit is reached with survivors, winner is survivor with most ships.
- If no survivors at limit, bank draw tiebreak applies.

## Tabletop Rules

### Objective

- Be the last player with ships remaining.

### Components

- Personal areas per player:
- draw pile,
- discard pile,
- hand,
- banked currency pile,
- fleet of ships.
- Shared area:
- `AbilitiesPile`,
- 3-card face-up market display,
- trash pile.

### Setup

1. Give each player the same starter deck and shuffle it.
2. Set starting ships by player count:
- 2-3 players: 7 ships.
- 4-5 players: 6 ships.
- 6+ players: 5 ships.
3. Set each bank to 0.
4. Build `AbilitiesPile`, shuffle, reveal 3 face-up market cards.

### On Your Turn

1. Draw until you have 5 cards in hand.
2. Move any amount of currency from hand to bank.
3. You may discard debris from hand.
4. Take exactly one action:
- Buy 1 card from the market.
- Play 1 rocket.
- Play 1 shield.
- Play 1 special.
5. End turn. Keep unplayed cards in hand.

### Buying

- Spend from bank and/or currency in hand.
- Bought cards always go to your personal discard pile.
- Refill the bought market slot from `AbilitiesPile`.

### Combat Basics

- Rockets target opponents and try to destroy ships.
- When attacked, the defending player chooses which of their ships the rocket lands on.
- Shields absorb hits.
- Some shields can react from hand to block a rocket.
- Some rockets bypass normal shields.

### Trashing

- Trashed cards are removed from the game and never return to deck/discard.
- Some shields and specials are explicitly one-time and get trashed.

### Duel Anti-Stall Rule

- `Unavoidable Ship Wreckage` applies only when exactly 2 players remain:
- After both players finish a round, if no ship was destroyed that round, both players lose 1 ship.

### Draw Resolution

- If both sides are destroyed at once, compare bank currency:
- Highest bank wins.
- If bank is tied, it is a draw.
