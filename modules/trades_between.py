from itertools import product, combinations

def generate_trades_between(roster_1, roster_2, max_players=2):
    """Generates all possible combinations of size 1 to max_per_side of players to trade between two rosters"""
    
    for from_1, from_2 in product(range(1, max_players), range(1, max_players)):
        if from_1 + from_2 > max_players: continue
        for to_swap, to_receive in product(combinations(roster_1, from_1), combinations(roster_2, from_2)):
            yield to_swap, to_receive

if __name__ == "__main__":
    print('\n'.join(map(str, generate_trades_between([1,2,3,4], [5,6,7,8], max_players=3))))