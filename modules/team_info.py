import re
from modules import config
from modules.player_stats import get_player_info
from espn_api.football import League
from datetime import datetime
from Levenshtein import ratio
from cachetools import TTLCache, cached

league_cache = TTLCache(maxsize=2, ttl=config.league_cache_ttl)
free_agent_cache = TTLCache(maxsize=2, ttl=config.league_cache_ttl)
league = League(int(config.league_id), datetime.now().year, config.espn_s2 or None, config.swid or None, debug=False)

def espn_to_cbs_name(name:str):
    # CBS only give us first initial and last name
    # and does not include D/ST in the name
    
    name = name.strip()
    if 'D/ST' not in name:
        name = re.sub('^(.)[\w]*', '\\1.', name)
    else:
        name = re.sub('D/ST', '', name)
        
    return name.strip()
  

@cached(league_cache)  
def get_teams():
    teams = list()
    my_team_name = config.team_name
    for team in league.teams:
        team_info = {
            'team_id': team.team_id,
            'team_abbrev': team.team_abbrev,
            'team_name': team.team_name,
            'is_my_team': False,
            'roster': list()
        }
        
        # Extract roster
        for player in team.roster:
            team_info['roster'].append({
                'name': espn_to_cbs_name(player.name),
                'position': player.position
            })
            
        teams.append(team_info)
    
    # Claim the team with a name closest to ours
    teams = [(t, ratio(t['team_name'].lower(), my_team_name.lower())) for t in teams]
    teams = sorted(teams, key=lambda x: x[1], reverse=True)
    teams[0][0]['is_my_team'] = True
    teams = [t[0] for t in teams]
    return teams

def estimate_team_value(team:dict):
    """Estimates the value of a team based on the average value of its non-benched players"""
    # TODO: this function is mad slow
    
    players_by_position = dict()
    for player in team['roster']:
        # Note: get_player_info handles name collisions and player not found
        player_info = get_player_info(player['name'], player['position'])
        players_by_position.setdefault(player['position'], list()).append(player_info)
    
    # Note: only the top 
    positions_on_team = {
        'QB': 1,
        'RB': 2,
        'WR': 2,
        # TODO: get FLEX working
        'TE': 1,
        'D/ST': 1,
        'K': 1
    }
    # Are counted
    
    players_by_position = {
        k: sorted(v, key=lambda x: x['percentile'])
        for k,v in players_by_position.items()
    }
    
    total_value = 0
    for pos, num in positions_on_team.items():
        # Not enough players -> fail
        if pos not in players_by_position or len(players_by_position[pos]) < num:
            return float('inf')
        
        for player_info in players_by_position[pos][:num]:
            total_value += player_info['percentile']
    
    return total_value #/ len(team['roster'])

def remove_from_team(team:dict, player:dict):
    """Removes a player from a team, returing a copy
    Note that the player must be a player on the team EXACTLY as it appears in the roster
    """
    
    team = team.copy()
    team['roster'] = [p for p in team['roster'] if p != player]
    return team

def add_to_team(team:dict, player:dict):
    """Adds a player to a team, returing a copy
    Note that the player must be a player on the team EXACTLY as it appears in the roster
    """
    
    team = team.copy()
    team['roster'].append(player)
    return team

@cached(free_agent_cache)
def get_free_agents():
    """Returns an unranked list of free agent names and positions"""
    free_agents = list()
    for player in league.free_agents(size=200):
        free_agents.append({
            'name': espn_to_cbs_name(player.name),
            'position': player.position
        })
    return free_agents