from modules import config
from modules.league_info import league

smoid = lambda x: 1/(1+2.71828**x)

def player_evaluator(player):
    week = league.current_week
    week_rating = smoid((week-5)/2) # Decrease weight of 'explore' as week approaches 10
    
    player_value = 2 * week_rating * (1 - player['percentile'] ** 0.5) # Ranges from 0-10 strictly
    
    # Most QBs have a higher proj_points than most RBs,
    # and as such are more valuable overall.
    # This is desired behavior.    
    
    player_value += 2 * player['proj_points'] ** 1.5 # Ranges from 0-100, gets up to 250 for QBs 
    player_value += week_rating * (0.15 * player['proj_season_points']) ** 1.5 # Ranges from 0-250, with overflow
    return round(player_value)

higher_is_better = True # If false: will minimize. If true: will maximize

def is_trade_mutual(pre_swap_my_value, post_swap_my_value, pre_swap_other_value, post_swap_other_value):
    neg_edge_percentage = 1 - config.maximum_trade_edge
    edge_percentage = 1 + config.maximum_trade_edge
    
    if not higher_is_better:
        return post_swap_my_value < pre_swap_my_value and \
               neg_edge_percentage*post_swap_other_value <= pre_swap_other_value
    else:
        return post_swap_my_value > pre_swap_my_value and \
               edge_percentage*post_swap_other_value >= pre_swap_other_value

def is_beneficial(pre_swap_value, post_swap_value):
    if not higher_is_better:
        return post_swap_value < pre_swap_value
    else:
        return post_swap_value > pre_swap_value

def worst_player(roster):
    if len(roster) == 0:
        return None
    
    if higher_is_better:
        return min(roster, key=player_evaluator)
    else:
        return max(roster, key=player_evaluator)
    
def best_player(roster):
    if len(roster) == 0:
        return None
    
    if higher_is_better:
        return max(roster, key=player_evaluator)
    else:
        return min(roster, key=player_evaluator)