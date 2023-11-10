from modules.player_stats import get_all_players
from modules.team_info import get_teams, estimate_team_value, add_to_team, remove_from_team, get_free_agents, print_team, get_team_lineup
from modules.trades_between import generate_trades_between
from modules.evaluator import is_trade_mutual, is_beneficial, higher_is_better, worst_player
from modules import config

print(f"Parsed info on {len(get_all_players())} players")

print(f"Your team is {get_teams()[0]['team_name']}")
print(print_team(get_teams()[0], scores=True, lineup=True))

print()
print("Beginning trade simulation")
mutually_beneficial_trades = list()

my_team = get_teams()[0]
for other_team in get_teams()[1:]:
    print(f"Simulating trades with {other_team['team_name']}")
    for to_swap, to_receive in generate_trades_between(my_team['roster'], other_team['roster'], config.maximum_trade_size):
        pre_swap_team1_value = estimate_team_value(my_team)
        pre_swap_team2_value = estimate_team_value(other_team, bench_weight=config.opponent_bench_weight)
        
        # Perform swaps.
        # Consider 4 'for's to handle name collisions
        
        # Skip all trades between the same position
        # These are extremely unlikely to occur, since 
        # one actor in the trade will always be screwed
        
        if all(s['position'] == r['position'] for s in to_swap for r in to_receive):
            continue
        
        my_team_postswap = my_team.copy()
        ot_team_postswap = other_team.copy()
        my_team_postswap['roster'] = my_team_postswap['roster'].copy()
        ot_team_postswap['roster'] = ot_team_postswap['roster'].copy()
        
        for p in to_swap:
            my_team_postswap = remove_from_team(my_team_postswap, p)
            ot_team_postswap = add_to_team(ot_team_postswap, p)
        
        for p in to_receive:
            my_team_postswap = add_to_team(my_team_postswap, p)
            ot_team_postswap = remove_from_team(ot_team_postswap, p)
            
        # Drop X players from our team until we reach the roster size limit
        to_drop = list()
        while len(my_team_postswap['roster']) > config.maximum_team_size:
            # (we don't care about the other team since they will be reset)
            team_lineup = get_team_lineup(my_team_postswap)
            benched_players = team_lineup['Bench']
            worst_benchie = worst_player(benched_players)
            
            to_drop.append(worst_benchie)
            my_team_postswap = remove_from_team(my_team_postswap, worst_benchie)
        
        post_swap_team1_value = estimate_team_value(my_team_postswap)
        post_swap_team2_value = estimate_team_value(ot_team_postswap, bench_weight=config.opponent_bench_weight)
        
        if is_trade_mutual(pre_swap_team1_value, post_swap_team1_value, pre_swap_team2_value, post_swap_team2_value):
            mutually_beneficial_trades.append({
                'to_giveaway': to_swap,
                'to_receive': to_receive,
                'to_drop': to_drop,
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
        
        if is_beneficial(pre_swap_team_value, post_swap_team_value):
            mutually_beneficial_trades.append({
                    'to_giveaway': (player_1,),
                    'to_receive': (player_2,),
                    'to_drop': tuple(),
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
mutually_beneficial_trades = sorted(mutually_beneficial_trades, key=lambda x: x['my_delta'], reverse=higher_is_better)

running_team = my_team.copy()
i = 0
for trade in mutually_beneficial_trades:
    # Skip any trade that involves a player we've already traded
    if any(player['name'] in players_to_trade for player in trade['to_giveaway']):
        continue
    if any(player['name'] in players_to_trade for player in trade['to_receive']):
        continue
    if any(player['name'] in players_to_trade for player in trade['to_drop']):
        continue
    
    # Calculate the next possible team
    next_running_team = running_team.copy()
    for player in trade['to_giveaway']:
        next_running_team = remove_from_team(next_running_team, player)
    for player in trade['to_receive']:
        next_running_team = add_to_team(next_running_team, player)
    for player in trade['to_drop']:
        next_running_team = remove_from_team(next_running_team, player)
        
    
    # Check if this team is acceptable
    delta = estimate_team_value(next_running_team) - estimate_team_value(running_team)
    if (higher_is_better and delta < 0) or (not higher_is_better and delta > 0):
        # Never accept worse teams -> trade chain ends if team is invalid
        break 
    elif delta == 0:
        # Ignore trades where we would just bench the new guy
        continue 
    else:
        # This trade is good
        running_team = next_running_team.copy()
        players_to_trade.update(player['name'] for player in trade['to_giveaway'])
        players_to_trade.update(player['name'] for player in trade['to_receive'])
        players_to_trade.update(player['name'] for player in trade['to_drop'])
    
    # Print the trade
    i += 1
    print(f"Trade Suggestion #{i} - {trade['other_team']}")
    print("\t Trade away: ", end=" ")
    for player in trade['to_giveaway']:
        print(f"{player['name']} ({player['position']}) ", end=" ")
    print("\n\t For: ", end=" ")
    for player in trade['to_receive']:
        print(f"{player['name']} ({player['position']}) ", end=" ")
    if trade['to_drop']: print("\n\t Drop: ", end=" ")
    for player in trade['to_drop']:
        print(f"{player['name']} ({player['position']}) ", end=" ")
    print() 
    
    print(f"\tMy team value delta: {trade['my_delta']}")
    print(f"\tTheir team value delta: {trade['their_delta']}")

    print("Running Team Value: ", estimate_team_value(running_team))
    

print()

print(print_team(running_team, scores=True, lineup=True))