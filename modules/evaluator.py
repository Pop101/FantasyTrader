from modules import config


def player_evaluator(player):
    player_value = 30 * (1 - player['percentile'] ** 0.5)
    
    # While I would love to bring in these stats,
    # They skew the results too much in favor of higher-scoring positions
    # ex. Most QBs have a higher proj_points than most RBs
    player_value += 3 * player['proj_points']
    player_value += 0.1 * player['proj_season_points']
    return player_value

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
