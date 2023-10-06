from modules.player_stats import get_all_players, get_player_info
from modules.team_info import get_teams, estimate_team_value, add_to_team, remove_from_team, get_free_agents
from modules.trades_between import generate_trades_between
from modules import config
from itertools import product, chain, combinations

print("Loaded successfully")
print(f"\tParsed info on {len(get_all_players())} players")

print(f"Your team is {get_teams()[0]['team_name']}")
for player in get_teams()[0]['roster']:
    player_info = get_player_info(player['name'], player['position'])
    print(f"\t{player['name']} ({player['position']}) - {player_info['percentile']}")
print("My team value: ", estimate_team_value(get_teams()[0]))

print()

print("Beginning trade simulation")
mutually_beneficial_trades = list()

my_team = get_teams()[0]
for other_team in get_teams()[1:]:
    print(f"Simulating trades with {other_team['team_name']}")
    for to_swap, to_receive in generate_trades_between(my_team['roster'], other_team['roster'], max_per_side=config.maximum_trade_size):
        pre_swap_team1_value = estimate_team_value(my_team)
        pre_swap_team2_value = estimate_team_value(other_team)
        
        # Perform swaps.
        # Consider 4 'for's to handle name collisions
        
        my_team_postswap = my_team.copy()
        ot_team_postswap = other_team.copy()
        for p in to_swap:
            my_team_postswap = remove_from_team(my_team_postswap, p)
            ot_team_postswap = add_to_team(ot_team_postswap, p)
        
        for p in to_receive:
            my_team_postswap = add_to_team(my_team_postswap, p)
            ot_team_postswap = remove_from_team(other_team, p)            
        
        post_swap_team1_value = estimate_team_value(my_team_postswap)
        post_swap_team2_value = estimate_team_value(ot_team_postswap)
        
        edge_percentage = 1 - config.maximum_trade_edge
        if post_swap_team1_value < pre_swap_team1_value and edge_percentage*post_swap_team2_value <= pre_swap_team2_value:
            mutually_beneficial_trades.append({
                'to_giveaway': to_swap,
                'to_receive': to_receive,
                'other_team': other_team['team_name'],
                'my_delta': post_swap_team1_value - pre_swap_team1_value,
                'their_delta': post_swap_team2_value - pre_swap_team2_value,
            })

# Now, consider all swaps for free agents
if config.check_free_agents:
    print("Simulating trades with free agents")
    for (player_1,), (player_2,) in generate_trades_between(my_team['roster'], get_free_agents()):
        pre_swap_team_value = estimate_team_value(my_team)
        
        my_team_postswap = remove_from_team(my_team, player_1)
        my_team_postswap = add_to_team(my_team_postswap, player_2)
        
        post_swap_team_value = estimate_team_value(my_team_postswap)
        
        if post_swap_team_value < pre_swap_team_value:
            mutually_beneficial_trades.append({
                    'to_giveaway': (player_1,),
                    'to_receive': (player_2,),
                    'other_team': 'Free Agents',
                    'my_delta': post_swap_team_value - pre_swap_team_value,
                    'their_delta': 0,
                })

print(f"Found {len(mutually_beneficial_trades)} mutually beneficial trades")
print("Filtering down to a set of optimal trades")

# Because I can only trade each player once(ex, can't trade the same dude to two different teams)
# you can't take all the trades
# Use a greedy algorithm to solve

players_to_trade = set()
mutually_beneficial_trades = sorted(mutually_beneficial_trades, key=lambda x: x['my_delta'])

i = 0
for trade in mutually_beneficial_trades:
    if any(player['name'] in players_to_trade for player in trade['to_giveaway']):
        continue
    if any(player['name'] in players_to_trade for player in trade['to_receive']):
        continue
    
    for player in trade['to_giveaway']:
        players_to_trade.add(player['name'])
    for player in trade['to_receive']:
        players_to_trade.add(player['name'])
    
    i += 1
    
    print(f"Trade Suggestion #{i} - {trade['other_team']}")
    print("\t Trade away: ", end=" ")
    for player in trade['to_giveaway']:
        print(f"{player['name']} ({player['position']}) ", end=" ")
    print("\n\t For: ", end=" ")
    for player in trade['to_receive']:
        print(f"{player['name']} ({player['position']}) ", end=" ")
    print()
    
    print(f"\tMy team value delta: {trade['my_delta']}")
    print(f"\tTheir team value delta: {trade['their_delta']}")