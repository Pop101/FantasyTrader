from modules import config


player_evaluator = lambda plr: plr['percentile']
higher_is_better = False # If false: will minimize. If true: will maximize

def is_trade_mutual(pre_swap_my_value, post_swap_my_value, pre_swap_other_value, post_swap_other_value):
    edge_percentage = 1 - config.maximum_trade_edge
    
    if higher_is_better:
        return post_swap_my_value < pre_swap_my_value and \
               edge_percentage*post_swap_other_value <= pre_swap_other_value
    else:
        return post_swap_my_value > pre_swap_my_value and \
               edge_percentage*post_swap_other_value >= pre_swap_other_value