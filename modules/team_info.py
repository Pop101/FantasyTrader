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

positions_on_team = {
    'QB': 1,
    'RB': 2,
    'WR': 2,
    'TE': 1,
    'D/ST': 1,
    'K': 1,
    'FLEX': 1
}

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

def get_team_lineup(team:dict):
    """Estimates the best lineup for a team"""
    
    players_by_position = dict()
    for player in team['roster']:
        # Note: get_player_info handles name collisions and player not found
        player_info = get_player_info(player['name'], player['position'])
        players_by_position.setdefault(player['position'], list()).append(player_info)
    
    # Note: only the top players of each position are counted
    
    players_by_position = {
        k: sorted(v, key=lambda x: x['percentile'])
        for k,v in players_by_position.items()
    }
    
    # Move worst people to bench
    players_by_position['Bench'] = list()
    for pos, num in positions_on_team.items():
        if pos not in players_by_position: continue
        
        num = min(num, len(players_by_position[pos]))
        players_by_position['Bench'] += players_by_position[pos][num:]
        players_by_position[pos] = players_by_position[pos][:num]
    
    # Grab the best benched player that's RB, WR, or TE -> they're flex
    if 'Bench' in players_by_position:
        eligible_players = [p for p in players_by_position['Bench'] if p['pos'] in ['RB', 'WR', 'TE']]
        eligible_players = sorted(eligible_players, key=lambda x: x['percentile'])
        
        flexes = eligible_players[:min(positions_on_team['FLEX'], len(eligible_players))]
        
        players_by_position['Bench'] = [p for p in players_by_position['Bench'] if p not in flexes]
        players_by_position['FLEX'] = flexes
    
    # Move bench dict key to end (aesthetic)
    players_by_position['Bench'] = players_by_position.pop('Bench')
    
    return players_by_position

def estimate_team_value(team:dict):
    """Estimates the value of a team based on the average value of its non-benched players"""
    
    lineup = get_team_lineup(team)
    
    total_value = 0
    for pos, players in lineup.items():
        if pos == 'Bench': continue
        
        if len(players) < positions_on_team[pos]:
            return float('inf')
        
        for player in players:
            total_value += player['percentile']
    
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

def print_team(team:dict, scores=True, lineup=True):
    output = f"{team['team_name']}"
    
    if not lineup:
        for player in team['roster']:
            output += f"\n\t{player['name']} ({player['position']})"
            if scores:
                player_info = get_player_info(player['name'], player['position'])
                output += f" - {player_info['percentile']}"
    
    if lineup:
        lineup = get_team_lineup(team)
        for pos, players in lineup.items():
            output += f"\n{pos}"
            for player in players:
                output += f"\n\t{player['name']} ({player['pos']}) - {player['percentile']}"
    
    if scores: output += f"\n\nOverall value: {estimate_team_value(team)}"
    
    return output

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