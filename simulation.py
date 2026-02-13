from collections import Counter
from cards import load_all_decks
from game import Game


def run_simulation(num_games=1000, num_players=3, verbose=False):
    starter, abilities = load_all_decks()
    player_names = [f"Player_{i+1}" for i in range(num_players)]

    win_counts  = Counter()
    turn_counts = []

    for i in range(num_games):
        game = Game(player_names, starter, abilities)
        winner = game.run()
        win_counts[winner] += 1
        turn_counts.append(game.turn_number)

        if verbose and i < 2:
            print("\n".join(game.log))
            print()

    print(f"\n=== Simulation Results: {num_games} games, {num_players} players ===")
    for name in sorted(win_counts):
        pct = win_counts[name] / num_games * 100
        print(f"  {name}: {win_counts[name]} wins ({pct:.1f}%)")

    avg   = sum(turn_counts) / len(turn_counts)
    print(f"\n  Avg game length : {avg:.1f} turns")
    print(f"  Shortest game   : {min(turn_counts)} turns")
    print(f"  Longest game    : {max(turn_counts)} turns")


if __name__ == "__main__":
    run_simulation(num_games=1000, num_players=5)
