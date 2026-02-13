from cards import load_all_decks
from game import Game

starter, abilities = load_all_decks()

game = Game(["Alice", "Bob", "Carol", "Jack", "John"], starter, abilities)
winner = game.run()

print("\n".join(game.log))
print(f"\nWinner: {winner} in {game.turn_number} turns")
