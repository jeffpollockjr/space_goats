import pandas as pd
import random


def load_all_decks(filepath="data/Space_Goats_V1_Card_Deck2.xlsx"):
    starter   = pd.read_excel(filepath, sheet_name="StarterDeck")
    rockets   = pd.read_excel(filepath, sheet_name="RocketMarket")
    shields   = pd.read_excel(filepath, sheet_name="ShieldMarket")
    specials  = pd.read_excel(filepath, sheet_name="SpecialsMarket")
    abilities = pd.concat([rockets, shields, specials], ignore_index=True)
    return starter, abilities


def build_starter_deck(starter_df):
    """Returns a shuffled 10-card personal deck for one player."""
    deck = []
    for _, row in starter_df.iterrows():
        for _ in range(int(row["quantity"])):
            deck.append(row.to_dict())
    random.shuffle(deck)
    return deck


def build_market_pile(df):
    """Expand a market sheet by 'copies', then shuffle. Top card = available."""
    pile = []
    for _, row in df.iterrows():
        for _ in range(int(row["copies"])):
            pile.append(row.to_dict())
    random.shuffle(pile)
    return pile
