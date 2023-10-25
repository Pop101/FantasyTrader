from modules import config


def player_evaluator(player):
    player_value = 1 * (1 - player['percentile'])
    return player_value

higher_is_better = True # If false: will minimize. If true: will maximize

def is_trade_mutual(pre_swap_my_value, post_swap_my_value, pre_swap_other_value, post_swap_other_value):
    edge_percentage = 1 - config.maximum_trade_edge
    
    if not higher_is_better:
        return post_swap_my_value < pre_swap_my_value and \
               edge_percentage*post_swap_other_value <= pre_swap_other_value
    else:
        return post_swap_my_value > pre_swap_my_value and \
               edge_percentage*post_swap_other_value >= pre_swap_other_value

def is_beneficial(pre_swap_value, post_swap_value):
    if not higher_is_better:
        return post_swap_value < pre_swap_value
    else:
        return post_swap_value > pre_swap_value
