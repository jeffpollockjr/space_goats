import random
from cards import build_starter_deck, build_market_pile

HAND_SIZE = 5
MARKET_DISPLAY_SIZE = 3
STARTER_SHIP_SHIELDED_SIDE = "starter_ship_shielded_side"
STARTER_SHIP_UNSHIELDED_SIDE = "starter_ship_unshielded_side"


class Ship:
    """A single ship with optional assigned shield and starter-side state."""

    def __init__(self, starter_side=STARTER_SHIP_UNSHIELDED_SIDE):
        self.shield = None
        self.shield_hp = 0
        self.starter_side = starter_side

    def has_shield(self):
        return self.shield is not None

    def assign_shield(self, card):
        self.shield = card
        effect = card.get("effect", "")
        if effect == "assign_to_ship_block_2":
            self.shield_hp = 2
        else:
            self.shield_hp = 1

    def absorb_hit(self):
        destroyed_shield = None
        self.shield_hp -= 1
        if self.shield_hp <= 0:
            destroyed_shield = self.shield
            self.shield = None
        return destroyed_shield

    def strip_shield(self):
        self.shield = None
        self.shield_hp = 0

    def is_on_starter_shielded_side(self):
        return self.starter_side == STARTER_SHIP_SHIELDED_SIDE

    def flip_starter_shield_side(self):
        if not self.is_on_starter_shielded_side():
            return False
        self.starter_side = STARTER_SHIP_UNSHIELDED_SIDE
        return True

    def __repr__(self):
        side = "starter-shielded" if self.is_on_starter_shielded_side() else "starter-unshielded"
        if self.shield:
            return f"[Ship: {side}, shield={self.shield['name']} hp={self.shield_hp}]"
        return f"[Ship: {side}, no assigned shield]"


class Player:
    def __init__(self, name, num_ships, starter_df):
        self.name = name
        self.fleet = [Ship(starter_side=STARTER_SHIP_SHIELDED_SIDE) for _ in range(num_ships)]
        self.draw_pile = build_starter_deck(starter_df)
        self.discard_pile = []
        self.hand = []
        self.bank_pile = []
        self.last_stand = False
        self.extra_turn = False

    def is_alive(self):
        return len(self.fleet) > 0

    @property
    def ship_count(self):
        return len(self.fleet)

    @property
    def bank(self):
        return len(self.bank_pile)

    def shielded_ships(self):
        return [s for s in self.fleet if s.has_shield()]

    def unshielded_ships(self):
        return [s for s in self.fleet if not s.has_shield()]

    def draw_one(self):
        if not self.draw_pile:
            if self.discard_pile:
                self.draw_pile = self.discard_pile[:]
                self.discard_pile.clear()
                random.shuffle(self.draw_pile)
            else:
                return
        self.hand.append(self.draw_pile.pop())

    def draw_to_hand_size(self):
        while len(self.hand) < HAND_SIZE:
            before = len(self.hand)
            self.draw_one()
            if len(self.hand) == before:
                break

    def bank_currency_from_hand(self, max_cards=None):
        scout_draws = 0
        banked = 0
        max_cards = None if max_cards is None else max(0, max_cards)

        # Keep banking until no currency remains in hand.
        # This allows Scout Ship draws to be banked immediately in the same step.
        while True:
            if max_cards is not None and banked >= max_cards:
                break

            idx = next((i for i, c in enumerate(self.hand) if c.get("type") == "currency"), None)
            if idx is None:
                break

            card = self.hand.pop(idx)
            self.bank_pile.append(card)
            banked += 1

            if card.get("effect") == "gain_1_currency_draw_1":
                before = len(self.hand)
                self.draw_one()
                if len(self.hand) > before:
                    scout_draws += 1

        return banked, scout_draws

    def discard_debris_from_hand(self):
        debris_cards = [c for c in self.hand if c.get("type") == "debris"]
        for card in debris_cards:
            self.hand.remove(card)
            self.discard_pile.append(card)
        return len(debris_cards)

    def available_currency(self):
        hand_currency = sum(1 for c in self.hand if c.get("type") == "currency")
        return self.bank + hand_currency

    def spend_currency(self, amount):
        if amount > self.available_currency():
            raise ValueError("Not enough currency to spend")

        spent_from_bank = 0
        spent_from_hand = 0

        while amount > 0 and self.bank_pile:
            card = self.bank_pile.pop()
            self.discard_pile.append(card)
            spent_from_bank += 1
            amount -= 1

        while amount > 0:
            hand_currency = next(
                (c for c in self.hand if c.get("type") == "currency"), None
            )
            if hand_currency is None:
                break
            self.hand.remove(hand_currency)
            self.discard_pile.append(hand_currency)
            spent_from_hand += 1
            amount -= 1

        if amount != 0:
            raise ValueError("Currency spending failed to satisfy cost")

        return spent_from_bank, spent_from_hand

    def __repr__(self):
        shielded = len(self.shielded_ships())
        return (
            f"{self.name} | Ships:{self.ship_count}({shielded} shielded) "
            f"| Hand:{len(self.hand)} | Bank:{self.bank} "
            f"| Deck:{len(self.draw_pile)} Discard:{len(self.discard_pile)}"
        )


class Game:
    def __init__(self, player_names, starter_df, abilities_df):
        n = len(player_names)
        if n == 2:
            starting_ships = 6
        elif n == 3:
            starting_ships = 5
        elif n == 4:
            starting_ships = 4
        else:
            starting_ships = 3

        self.players = [Player(name, starting_ships, starter_df) for name in player_names]
        self.abilities_pile = build_market_pile(abilities_df)
        self.market_display = [None] * MARKET_DISPLAY_SIZE
        self.trash_pile = []
        self.turn_number = 0
        self.log = []
        self.attack_counts = {name: 0 for name in player_names}
        self.ships_destroyed_this_round = 0
        self.refill_market_display()

    def _draw_ability(self):
        if not self.abilities_pile:
            return None
        return self.abilities_pile.pop()

    def refill_market_display(self):
        for i in range(MARKET_DISPLAY_SIZE):
            if self.market_display[i] is None:
                self.market_display[i] = self._draw_ability()

    def _card_cost(self, card):
        return int(card.get("cost", 0))

    def _alive_opponents(self, player):
        return [p for p in self.players if p != player and p.is_alive()]

    def _card_intrinsic_value(self, card):
        card_type = card.get("type", "")
        effect = card.get("effect", "")
        if card_type == "rocket":
            return {
                "destroy_1_ship": 8.0,
                "destroy_1_weakest_ship": 8.5,
                "destroy_1_ship_ignore_shields": 9.2,
                "strip_all_shields_one_opponent": 7.8,
                "each_opponent_blocks_or_loses_ship": 10.0,
                "destroy_up_to_2_ships": 10.5,
                "destroy_1_unshielded_ship": 6.0,
            }.get(effect, 7.5)
        if card_type == "shield":
            return {
                "assign_to_ship_block_1": 6.2,
                "assign_to_ship_block_2": 8.2,
                "assign_to_ship_block_any": 9.0,
                "reactive_block_1_rocket": 7.0,
                "cancel_1_rocket_targeting_you": 7.0,
            }.get(effect, 5.5)
        if card_type == "special":
            return {
                "draw_3_keep_2_discard_1": 6.5,
                "retrieve_1_card_from_discard": 7.0,
                "look_at_top3_any_market_rearrange": 5.0,
                "negate_last_ship_loss_once": 7.5,
                "add_1_ship_to_fleet": 8.2,
                "take_extra_turn": 9.8,
            }.get(effect, 5.0)
        if card_type == "currency":
            return 2.0
        if card_type == "debris":
            return -4.0
        return 0.0

    def market_options(self):
        return [(idx, card) for idx, card in enumerate(self.market_display) if card is not None]

    def _score_special_card(self, player, card):
        if card.get("type") != "special":
            return -999.0
        effect = card.get("effect", "")

        if effect == "take_extra_turn":
            followup_rockets = sum(
                1 for c in player.hand if c is not card and c.get("type") == "rocket"
            )
            followup_buy = min(player.available_currency(), 5)
            return 8.5 + 1.8 * followup_rockets + 0.4 * followup_buy

        if effect == "add_1_ship_to_fleet":
            return 5.0 + max(0, 6 - player.ship_count) * 1.5

        if effect == "negate_last_ship_loss_once":
            if player.last_stand:
                return -1.0
            if player.ship_count <= 2:
                return 9.0
            if player.ship_count == 3:
                return 6.5
            return 3.5

        if effect == "retrieve_1_card_from_discard":
            pool = [c for c in player.discard_pile if c is not card]
            if not pool:
                return -1.0
            best = max(pool, key=self._card_intrinsic_value)
            return 4.5 + 0.7 * self._card_intrinsic_value(best)

        if effect == "draw_3_keep_2_discard_1":
            clutter = sum(
                1 for c in player.hand if c is not card and c.get("type") in ("currency", "debris")
            )
            return 5.0 + 0.9 * clutter

        if effect == "look_at_top3_any_market_rearrange":
            high_visible = any(
                c is not None and self._card_cost(c) >= 4 for c in self.market_display
            )
            return 3.5 + (1.0 if high_visible else 0.0)

        if effect == "trash_1_card_from_discard":
            # Deck Purge can trash from either discard or hand.
            # Include this card itself because it will be in discard after play.
            pool = list(player.discard_pile) + [c for c in player.hand if c is not card] + [card]
            worst = min(pool, key=self._card_intrinsic_value)
            # Higher score when we can remove low-value cards (debris/currency).
            return 4.0 + max(0.0, 4.0 - self._card_intrinsic_value(worst)) * 0.8

        if effect == "trash_1_card_from_discard_draw_1":
            pool = [c for c in player.discard_pile if c is not card]
            if not pool:
                return 1.0
            worst = min(pool, key=self._card_intrinsic_value)
            return 5.0 + max(0.0, 4.0 - self._card_intrinsic_value(worst)) * 0.8

        return 2.0

    def _score_buy_card(self, player, card):
        score = self._card_intrinsic_value(card) + 0.45 * self._card_cost(card)
        card_type = card.get("type", "")
        effect = card.get("effect", "")

        if card_type == "rocket":
            if not self._alive_opponents(player):
                score -= 6.0
            if not any(c.get("type") == "rocket" for c in player.hand):
                score += 1.2
        elif card_type == "shield":
            unshielded = len(player.unshielded_ships())
            if "assign_to_ship" in str(effect):
                if unshielded == 0:
                    score -= 3.0
                else:
                    score += min(unshielded, 3) * 0.8
            if player.ship_count <= 3:
                score += 0.8
        elif card_type == "special":
            score += 0.8 * self._score_special_card(player, card)

        if player.bank >= self._card_cost(card):
            score += 0.4
        if player.available_currency() - self._card_cost(card) == 0:
            score += 0.3

        return score

    def pick_buy_option(self, player):
        affordable = []
        for idx, card in self.market_options():
            if self._card_cost(card) <= player.available_currency():
                score = self._score_buy_card(player, card)
                affordable.append((idx, card, score))
        if not affordable:
            return None, None, -999.0
        affordable.sort(
            key=lambda x: (x[2], self._card_cost(x[1]), x[1].get("name", "")),
            reverse=True,
        )
        return affordable[0]

    def buy_from_market(self, player, slot_idx):
        card = self.market_display[slot_idx]
        if card is None:
            return False

        cost = self._card_cost(card)
        if cost > player.available_currency():
            return False

        spent_bank, spent_hand = player.spend_currency(cost)

        if card.get("effect") == "add_1_ship_to_fleet":
            # Reinforcement Shuttle: immediate fleet deploy on buy.
            player.fleet.append(Ship(starter_side=STARTER_SHIP_UNSHIELDED_SIDE))
            destination_note = "deployed to fleet (unshielded)"
        else:
            player.discard_pile.append(card)
            destination_note = "to discard"

        self.market_display[slot_idx] = None
        self.refill_market_display()
        self.log.append(
            f"  {player.name} buys '{card['name']}' (cost {cost}) "
            f"[spent bank:{spent_bank}, hand:{spent_hand}, bank left:{player.bank}; {destination_note}]"
        )
        return True

    def _fire_at(self, attacker, target, effect):
        self.attack_counts[target.name] += 1

        emergency = next(
            (
                c
                for c in target.hand
                if c.get("effect") in ("reactive_block_1_rocket", "cancel_1_rocket_targeting_you")
            ),
            None,
        )
        if emergency:
            target.hand.remove(emergency)
            # Reactive shields are one-time use.
            self.trash_pile.append(emergency)
            self.log.append(
                f"    -> {target.name} plays '{emergency['name']}' out of turn - rocket blocked (trashed)!"
            )
            return

        self.fire_rocket(attacker, target, effect)

    def _choose_landing_ship(self, target, effect):
        """
        Defender chooses where the rocket lands on their fleet.
        In simulation this choice is made by defensive AI to minimize damage.
        """
        assigned_shielded = target.shielded_ships()
        starter_shielded = [s for s in target.fleet if s.is_on_starter_shielded_side()]
        starter_shielded_no_assigned = [s for s in starter_shielded if not s.has_shield()]
        fully_unshielded = [
            s for s in target.fleet if (not s.has_shield()) and (not s.is_on_starter_shielded_side())
        ]

        weak_rocket = effect == "destroy_1_unshielded_ship"
        ignore_shields = effect == "destroy_1_ship_ignore_shields"

        def lowest_hp_shield_ship(ships):
            return min(ships, key=lambda s: s.shield_hp)

        # Weak rockets are best routed into any shield layer first.
        if weak_rocket:
            if assigned_shielded:
                return lowest_hp_shield_ship(assigned_shielded)
            if starter_shielded_no_assigned:
                return starter_shielded_no_assigned[0]
            if fully_unshielded:
                return fully_unshielded[0]
            return target.fleet[0]

        # Piercing rockets can still be blocked by block_any assigned shields.
        if ignore_shields:
            block_any = [
                s
                for s in assigned_shielded
                if s.shield and s.shield.get("effect") == "assign_to_ship_block_any"
            ]
            if block_any:
                return lowest_hp_shield_ship(block_any)
            if starter_shielded_no_assigned:
                return starter_shielded_no_assigned[0]
            if starter_shielded:
                return starter_shielded[0]
            if fully_unshielded:
                return fully_unshielded[0]
            if assigned_shielded:
                return lowest_hp_shield_ship(assigned_shielded)
            return target.fleet[0]

        # Normal rockets: route into assigned shields, then starter-shielded side.
        if assigned_shielded:
            return lowest_hp_shield_ship(assigned_shielded)
        if starter_shielded_no_assigned:
            return starter_shielded_no_assigned[0]
        if fully_unshielded:
            return fully_unshielded[0]
        return target.fleet[0]

    def _estimate_hit_value(self, target, effect):
        if not target.is_alive():
            return 0.0

        shielded = target.shielded_ships()
        if effect == "strip_all_shields_one_opponent":
            return len(shielded) * 2.8 + (1.0 if shielded else 0.0)

        landing_ship = self._choose_landing_ship(target, effect)
        weak_rocket = effect == "destroy_1_unshielded_ship"
        ignore_shields = effect == "destroy_1_ship_ignore_shields"
        landing_shield = landing_ship.shield
        landing_effect = landing_shield.get("effect", "") if landing_shield else ""
        starter_side_shielded = landing_ship.is_on_starter_shielded_side()

        assigned_shield_blocks = (
            landing_shield is not None
            and (weak_rocket or (not ignore_shields) or landing_effect == "assign_to_ship_block_any")
        )

        if assigned_shield_blocks:
            ship_loss = False
            starter_flip = False
        elif starter_side_shielded:
            ship_loss = False
            starter_flip = True
        else:
            ship_loss = True
            starter_flip = False

        if ship_loss:
            value = 6.0 + (7 - target.ship_count) * 0.9
            if target.ship_count == 1:
                value += 3.0
                if target.last_stand:
                    value = 2.4
            return value

        if assigned_shield_blocks:
            if weak_rocket and landing_shield is not None:
                return 0.0
            return 1.8 + (1.0 if landing_ship.shield_hp == 1 else 0.4)

        if starter_flip:
            return 2.0
        return 0.0

    def _pick_best_target(self, attacker, alive_opponents, effect):
        if not alive_opponents:
            return None
        scored = []
        for opp in alive_opponents:
            score = self._estimate_hit_value(opp, effect)
            scored.append((score, -opp.ship_count, opp))
        max_score = max(s[0] for s in scored)
        top = [s[2] for s in scored if abs(s[0] - max_score) < 1e-9]
        return random.choice(top)

    def _score_rocket_card(self, player, card):
        if card.get("type") != "rocket":
            return -999.0
        alive_opponents = self._alive_opponents(player)
        if not alive_opponents:
            return -999.0

        effect = card.get("effect", "")
        if effect == "each_opponent_blocks_or_loses_ship":
            return (
                sum(self._estimate_hit_value(opp, "destroy_1_ship") for opp in alive_opponents)
                + 1.2 * len(alive_opponents)
            )
        if effect == "destroy_up_to_2_ships":
            hits = sorted(
                [self._estimate_hit_value(opp, "destroy_1_ship") for opp in alive_opponents],
                reverse=True,
            )
            return sum(hits[:2]) + 1.2
        if effect == "strip_all_shields_one_opponent":
            return max(self._estimate_hit_value(opp, effect) for opp in alive_opponents) + 0.6
        if effect == "destroy_1_weakest_ship":
            return max(self._estimate_hit_value(opp, "destroy_1_ship") for opp in alive_opponents) + 0.5
        return max(self._estimate_hit_value(opp, effect) for opp in alive_opponents)

    def _select_best_rocket_card(self, player):
        rocket_cards = [c for c in player.hand if c.get("type") == "rocket"]
        if not rocket_cards:
            return None, -999.0
        scored = [(self._score_rocket_card(player, c), c) for c in rocket_cards]
        scored.sort(key=lambda x: (x[0], self._card_intrinsic_value(x[1])), reverse=True)
        return scored[0][1], scored[0][0]

    def fire_rocket(self, attacker, target, effect):
        if not target.is_alive():
            return

        ignore_shields = effect == "destroy_1_ship_ignore_shields"
        weak_rocket = effect == "destroy_1_unshielded_ship"

        hit_ship = self._choose_landing_ship(target, effect)
        landing_shield = hit_ship.shield
        landing_effect = landing_shield.get("effect", "") if landing_shield else ""
        starter_side_shielded = hit_ship.is_on_starter_shielded_side()

        if landing_shield:
            impact_zone = "assigned_shield"
        elif starter_side_shielded:
            impact_zone = STARTER_SHIP_SHIELDED_SIDE
        else:
            impact_zone = STARTER_SHIP_UNSHIELDED_SIDE

        self.log.append(
            f"    -> {target.name} chooses impact ship ({impact_zone})"
        )

        if weak_rocket and landing_shield is not None:
            self.log.append(
                f"    -> {target.name}'s chosen shielded ship blocks the weak rocket"
            )
            return

        shield_blocks = (
            landing_shield is not None
            and (not ignore_shields or landing_effect == "assign_to_ship_block_any")
        )

        if shield_blocks:
            destroyed_shield = hit_ship.absorb_hit()
            if hit_ship.shield:
                self.log.append(
                    f"    -> {target.name} absorbs with shield "
                    f"({hit_ship.shield_hp} hits remaining)"
                )
            else:
                if destroyed_shield is not None:
                    if destroyed_shield.get("name") == "Hull Plating":
                        target.discard_pile.append(destroyed_shield)
                        shield_zone = "discarded"
                    else:
                        self.trash_pile.append(destroyed_shield)
                        shield_zone = "trashed"
                else:
                    shield_zone = "removed"
                self.log.append(
                    f"    -> {target.name} shield destroyed! Ship survives. "
                    f"[{target.ship_count} ships, shield {shield_zone}]"
                )
            return

        if hit_ship.flip_starter_shield_side():
            self.log.append(
                f"    -> {target.name}'s ship flips to {STARTER_SHIP_UNSHIELDED_SIDE} and survives"
            )
            return

        ship_to_lose = hit_ship
        if target.ship_count == 1 and target.last_stand:
            target.last_stand = False
            self.log.append(
                f"    -> {target.name} triggers Last Stand Protocol - final ship survives!"
            )
            return
        ship_to_lose.strip_shield()
        target.fleet.remove(ship_to_lose)
        self.ships_destroyed_this_round += 1
        self.log.append(
            f"    -> {target.name} loses a ship! ({target.ship_count} remaining)"
        )

    def _apply_unavoidable_ship_wreckage(self, duel_players):
        """
        Duel-only end-of-round pressure rule:
        if no ships were destroyed in the round, each of the 2 remaining players
        loses 1 ship unavoidably.
        """
        self.log.append(
            "  !! Unavoidable Ship Wreckage: no ships destroyed this round, "
            "each duelist loses 1 ship."
        )
        for player in duel_players:
            if not player.is_alive():
                continue
            ship_to_lose = player.unshielded_ships()[0] if player.unshielded_ships() else player.fleet[0]
            ship_to_lose.strip_shield()
            player.fleet.remove(ship_to_lose)
            self.log.append(
                f"    -> {player.name} loses 1 ship to wreckage! ({player.ship_count} remaining)"
            )

    def _resolve_draw_by_bank(self, candidates):
        """
        Draw tiebreak:
        highest bank currency wins. If tied for highest bank, result remains Draw.
        """
        if not candidates:
            self.log.append("\nDraw: no eligible players for bank tiebreak.")
            return "Draw"
        max_bank = max(p.bank for p in candidates)
        leaders = [p for p in candidates if p.bank == max_bank]
        if len(leaders) == 1:
            winner = leaders[0]
            self.log.append(
                f"\nBank tiebreak: {winner.name} wins with {winner.bank} bank currency."
            )
            return winner.name
        self.log.append(
            f"\nDraw: bank tiebreak tied at {max_bank} currency among "
            f"{', '.join(p.name for p in leaders)}."
        )
        return "Draw"

    def _score_shield_card(self, player, card):
        if card.get("type") != "shield":
            return -999.0
        effect = card.get("effect", "")
        if effect not in ("assign_to_ship_block_1", "assign_to_ship_block_2", "assign_to_ship_block_any"):
            return -999.0
        unshielded = len(player.unshielded_ships())
        if unshielded <= 0:
            return -2.0
        base = {
            "assign_to_ship_block_1": 5.0,
            "assign_to_ship_block_2": 7.2,
            "assign_to_ship_block_any": 8.0,
        }.get(effect, 4.0)
        urgency = 1.8 if player.ship_count <= 3 else 0.0
        return base + min(unshielded, 3) * 0.7 + urgency

    def _select_best_shield_card(self, player):
        shields = [c for c in player.hand if c.get("type") == "shield"]
        if not shields:
            return None, -999.0
        scored = [(self._score_shield_card(player, c), c) for c in shields]
        scored.sort(key=lambda x: (x[0], self._card_intrinsic_value(x[1])), reverse=True)
        return scored[0][1], scored[0][0]

    def _select_best_special_card(self, player):
        specials = [c for c in player.hand if c.get("type") == "special"]
        if not specials:
            return None, -999.0
        scored = [(self._score_special_card(player, c), c) for c in specials]
        scored.sort(key=lambda x: (x[0], self._card_intrinsic_value(x[1])), reverse=True)
        return scored[0][1], scored[0][0]

    def play_one_special(self, player, card=None):
        if card is None:
            card, score = self._select_best_special_card(player)
            if card is None or score <= 0:
                return False
        elif card not in player.hand or card.get("type") != "special":
            return False

        effect = card.get("effect", "")
        player.hand.remove(card)
        if effect in ("add_1_ship_to_fleet", "take_extra_turn"):
            # One-time use specials are trashed when played.
            self.trash_pile.append(card)
        else:
            player.discard_pile.append(card)

        if effect == "draw_3_keep_2_discard_1":
            drawn = []
            for _ in range(3):
                before = len(player.hand)
                player.draw_one()
                if len(player.hand) > before:
                    drawn.append(player.hand[-1])
            if drawn:
                to_discard = next(
                    (c for c in drawn if c.get("type") in ("debris", "currency")),
                    drawn[0],
                )
                if to_discard in player.hand:
                    player.hand.remove(to_discard)
                    player.discard_pile.append(to_discard)
            self.log.append(f"  {player.name} plays 'Deep Space Recon' (drew 3, kept 2)")

        elif effect == "retrieve_1_card_from_discard":
            pool = [c for c in player.discard_pile if c is not card]
            if pool:
                rank = {"rocket": 0, "shield": 1, "special": 2, "currency": 3, "debris": 4}
                retrieve = min(pool, key=lambda c: (rank.get(c.get("type", ""), 9), c.get("name", "")))
                player.discard_pile.remove(retrieve)
                player.hand.append(retrieve)
                self.log.append(
                    f"  {player.name} plays 'Salvage Operation' - retrieves '{retrieve['name']}'"
                )
            else:
                self.log.append(f"  {player.name} plays 'Salvage Operation' (discard empty)")

        elif effect == "negate_last_ship_loss_once":
            player.last_stand = True
            self.log.append(
                f"  {player.name} plays 'Last Stand Protocol' - final ship protected!"
            )

        elif effect == "add_1_ship_to_fleet":
            # Legacy fallback: normally this card deploys directly when bought.
            player.fleet.append(Ship(starter_side=STARTER_SHIP_UNSHIELDED_SIDE))
            self.log.append(
                f"  {player.name} plays 'Reinforcement Shuttle' from hand (legacy) - "
                f"fleet grows to {player.ship_count} ships!"
            )

        elif effect == "take_extra_turn":
            player.extra_turn = True
            self.log.append(f"  {player.name} plays 'Warp Drive' - extra turn queued!")

        elif effect == "look_at_top3_any_market_rearrange":
            top3 = self.abilities_pile[-3:] if len(self.abilities_pile) >= 3 else self.abilities_pile[:]
            top3.sort(key=lambda c: self._card_cost(c), reverse=True)
            for i, c in enumerate(top3):
                self.abilities_pile[len(self.abilities_pile) - len(top3) + i] = c
            self.log.append(f"  {player.name} plays 'Arms Dealer' - rearranged market deck")

        elif effect == "trash_1_card_from_discard":
            # Deck Purge can trash one card from either discard or hand.
            candidates = []
            for idx, c in enumerate(player.discard_pile):
                candidates.append(("discard", idx, c))
            for idx, c in enumerate(player.hand):
                candidates.append(("hand", idx, c))

            if candidates:
                zone, idx, to_trash = min(
                    candidates,
                    key=lambda t: self._card_intrinsic_value(t[2]),
                )
                if zone == "discard":
                    player.discard_pile.pop(idx)
                else:
                    player.hand.pop(idx)
                self.trash_pile.append(to_trash)
                self.log.append(
                    f"  {player.name} plays 'Deck Purge' - trashes '{to_trash['name']}' from {zone}"
                )
            else:
                self.log.append(f"  {player.name} plays 'Deck Purge' (no cards to trash)")

        elif effect == "trash_1_card_from_discard_draw_1":
            pool = [c for c in player.discard_pile if c is not card]
            if pool:
                to_trash = min(pool, key=self._card_intrinsic_value)
                player.discard_pile.remove(to_trash)
                self.trash_pile.append(to_trash)
                self.log.append(
                    f"  {player.name} plays 'Deep Clean' - trashes '{to_trash['name']}' and draws 1"
                )
            else:
                self.log.append(f"  {player.name} plays 'Deep Clean' (discard empty, draws 1)")
            player.draw_one()

        else:
            self.log.append(f"  {player.name} plays '{card['name']}' (no effect handler)")

        return True

    def play_one_shield(self, player, card=None):
        if card is None:
            card, score = self._select_best_shield_card(player)
            if card is None or score <= 0:
                return False
        elif card not in player.hand or card.get("type") != "shield":
            return False

        player.hand.remove(card)
        targets = player.unshielded_ships()
        if targets:
            targets[0].assign_shield(card)
            self.log.append(
                f"  {player.name} assigns '{card['name']}' "
                f"({len(player.shielded_ships())}/{player.ship_count} shielded)"
            )
        else:
            player.discard_pile.append(card)
            self.log.append(
                f"  {player.name} discards '{card['name']}' (no unshielded ships)"
            )
        return True

    def play_one_rocket(self, player, card=None):
        alive_opponents = self._alive_opponents(player)
        if not alive_opponents:
            return False

        if card is None:
            card, score = self._select_best_rocket_card(player)
            if card is None or score <= 0:
                return False
        elif card not in player.hand or card.get("type") != "rocket":
            return False

        effect = card.get("effect", "")
        player.hand.remove(card)
        player.discard_pile.append(card)

        if effect == "each_opponent_blocks_or_loses_ship":
            self.log.append(f"  {player.name} fires '{card['name']}' at ALL opponents!")
            for opp in alive_opponents:
                self._fire_at(player, opp, effect)

        elif effect == "destroy_up_to_2_ships":
            self.log.append(f"  {player.name} fires '{card['name']}' (salvo - up to 2 hits)")
            target = self._pick_best_target(player, alive_opponents, "destroy_1_ship")
            self._fire_at(player, target, "destroy_1_ship")
            alive_opponents = [p for p in alive_opponents if p.is_alive()]
            if alive_opponents:
                target2 = self._pick_best_target(player, alive_opponents, "destroy_1_ship")
                self._fire_at(player, target2, "destroy_1_ship")

        elif effect == "strip_all_shields_one_opponent":
            target = self._pick_best_target(player, alive_opponents, effect)
            self.log.append(f"  {player.name} fires EMP at {target.name}")
            for ship in target.fleet:
                ship.strip_shield()
            self.attack_counts[target.name] += 1
            self.log.append(
                f"    -> All shields stripped from {target.name}! "
                f"({target.ship_count} unshielded ships remain)"
            )

        elif effect == "destroy_1_weakest_ship":
            target = self._pick_best_target(player, alive_opponents, "destroy_1_ship")
            self.log.append(f"  {player.name} fires '{card['name']}' at {target.name}")
            self._fire_at(player, target, "destroy_1_ship")

        else:
            target = self._pick_best_target(player, alive_opponents, effect)
            self.log.append(f"  {player.name} fires '{card['name']}' at {target.name}")
            self._fire_at(player, target, effect)

        return True

    def _market_status_text(self):
        slots = []
        for i, card in enumerate(self.market_display, start=1):
            if card is None:
                slots.append(f"{i}: empty")
            else:
                slots.append(f"{i}: {card['name']} (${self._card_cost(card)})")
        return " | ".join(slots)

    def _choose_action(self, player):
        actions = []

        buy_slot, buy_card, buy_score = self.pick_buy_option(player)
        if buy_card is not None:
            actions.append(("buy", buy_score, buy_slot, buy_card))

        rocket_card, rocket_score = self._select_best_rocket_card(player)
        if rocket_card is not None and rocket_score > 0:
            actions.append(("rocket", rocket_score, None, rocket_card))

        shield_card, shield_score = self._select_best_shield_card(player)
        if shield_card is not None and shield_score > 0:
            actions.append(("shield", shield_score, None, shield_card))

        special_card, special_score = self._select_best_special_card(player)
        if special_card is not None and special_score > 0:
            actions.append(("special", special_score, None, special_card))

        if not actions:
            return "pass", 0.0, None, None

        # Tie-breaks favor immediate tactical impact over economy.
        priority = {"rocket": 4, "special": 3, "shield": 2, "buy": 1}
        best = max(
            actions,
            key=lambda a: (
                a[1],
                priority[a[0]],
                self._card_cost(a[3]) if a[3] is not None else 0,
            ),
        )
        return best

    def play_turn(self, player):
        player.draw_to_hand_size()
        self.log.append(
            f"  {player.name} draws to {len(player.hand)} cards "
            f"(deck:{len(player.draw_pile)} discard:{len(player.discard_pile)} bank:{player.bank})"
        )

        banked, scout_draws = player.bank_currency_from_hand()
        if banked:
            draw_note = f" | scout draws: {scout_draws}" if scout_draws else ""
            self.log.append(
                f"  {player.name} banks {banked} currency card(s) [bank: {player.bank}{draw_note}]"
            )

        debris_discarded = player.discard_debris_from_hand()
        if debris_discarded:
            self.log.append(
                f"  {player.name} discards {debris_discarded} debris card(s)"
            )

        self.log.append(f"  Market: {self._market_status_text()}")

        action, score, slot_idx, chosen_card = self._choose_action(player)
        if action == "buy":
            self.log.append(
                f"  {player.name} chooses BUY '{chosen_card['name']}' "
                f"(score {score:.1f})"
            )
            self.buy_from_market(player, slot_idx)
        elif action == "rocket":
            self.log.append(
                f"  {player.name} chooses ROCKET '{chosen_card['name']}' "
                f"(score {score:.1f})"
            )
            self.play_one_rocket(player, chosen_card)
        elif action == "shield":
            self.log.append(
                f"  {player.name} chooses SHIELD '{chosen_card['name']}' "
                f"(score {score:.1f})"
            )
            self.play_one_shield(player, chosen_card)
        elif action == "special":
            self.log.append(
                f"  {player.name} chooses SPECIAL '{chosen_card['name']}' "
                f"(score {score:.1f})"
            )
            self.play_one_special(player, chosen_card)
        else:
            self.log.append(f"  {player.name} passes (no valid action)")

    def run(self, max_turns=200):
        self.log.append("=== Game Start ===")
        for p in self.players:
            self.log.append(f"  {p}")

        while True:
            self.turn_number += 1
            self.attack_counts = {p.name: 0 for p in self.players}
            self.ships_destroyed_this_round = 0
            self.log.append(f"\n-- Turn {self.turn_number} --")

            for player in list(self.players):
                if not player.is_alive():
                    continue

                alive_before_turn = [p for p in self.players if p.is_alive()]
                self.play_turn(player)

                alive = [p for p in self.players if p.is_alive()]
                if len(alive) == 1:
                    self.log.append(f"\nWinner: {alive[0].name} on turn {self.turn_number}.")
                    return alive[0].name
                if not alive:
                    self.log.append(f"\nMutual destruction on turn {self.turn_number}.")
                    return self._resolve_draw_by_bank(alive_before_turn)

                if player.extra_turn and player.is_alive():
                    player.extra_turn = False
                    self.log.append(f"  * {player.name} takes an extra turn (Warp Drive)!")
                    alive_before_extra = [p for p in self.players if p.is_alive()]
                    self.play_turn(player)

                alive = [p for p in self.players if p.is_alive()]
                if len(alive) == 1:
                    self.log.append(f"\nWinner: {alive[0].name} on turn {self.turn_number}.")
                    return alive[0].name
                if not alive:
                    self.log.append(f"\nMutual destruction on turn {self.turn_number}.")
                    return self._resolve_draw_by_bank(alive_before_extra)

            # End-of-round duel pressure:
            # when exactly 2 players remain and no ships were destroyed this round,
            # both players lose 1 ship unavoidably.
            alive = [p for p in self.players if p.is_alive()]
            if len(alive) == 2 and self.ships_destroyed_this_round == 0:
                duel_before_wreckage = alive[:]
                self._apply_unavoidable_ship_wreckage(alive)
                alive = [p for p in self.players if p.is_alive()]
                if len(alive) == 1:
                    self.log.append(f"\nWinner: {alive[0].name} on turn {self.turn_number}.")
                    return alive[0].name
                if not alive:
                    self.log.append(f"\nMutual destruction on turn {self.turn_number}.")
                    return self._resolve_draw_by_bank(duel_before_wreckage)

            if self.turn_number >= max_turns:
                alive = [p for p in self.players if p.is_alive()]
                if not alive:
                    self.log.append(f"\nNo players alive at turn limit ({max_turns}).")
                    return self._resolve_draw_by_bank(self.players)
                winner = max(alive, key=lambda p: p.ship_count)
                self.log.append(
                    f"\nTurn limit reached ({max_turns}). "
                    f"{winner.name} wins with {winner.ship_count} ships."
                )
                return winner.name
