from cachetools import TTLCache, cached
from functools import lru_cache

from modules import config
from modules.proxied_request import proxied_get
from lxml import html
from Levenshtein import ratio

cache = TTLCache(maxsize=1000, ttl=config.player_cache_ttl)

# Ideally, we could scrape the player stats from https://www.fantasypros.com/nfl/rankings/ros-overall.php
@cached(cache)
def get_all_players():
    """Returns a list of all players, sorted by position and rank"""
    players = list()
    
    for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
        raw_html = proxied_get(f'https://www.cbssports.com/fantasy/football/rankings/ppr/{pos}/')
        doc = html.fromstring(raw_html.content)
        
        # TODO: consider parsing individual expert rankings instead of consensus rankings
        consensus_rankings = doc.xpath('//*[normalize-space(@class)="experts-column triple"]')[0]
        total_ranks = len(consensus_rankings.xpath('.//div[@class="player"]'))
        for rank, player in enumerate(consensus_rankings.xpath('.//div[@class="player"]')):
            if not player.xpath('./a'): continue
            player_name = player.xpath('./a')[0].text_content()
            
            percentile = rank / total_ranks
            
            players.append({
                'name': player_name.strip(),
                'rank': rank,
                'percentile': percentile,
                'percentile_score': (percentile ** 0.5),
                'pos': pos,
            })
    
    return players

@lru_cache
def search_player_info(player_name, pos=None):
    """Search for a player by name, optionally filtered by position

    Args:
        player_name (str): The name of the player to search for
        pos (str, optional): The position in {'QB', 'RB', 'WR', 'TE', 'K', 'DST'}. Defaults to None.

    Returns:
        list[str]: All players matching the given name and position.
                   Some players may have the same name, so this may return multiple players.
    """
    
    players = get_all_players()
    if pos is not None: players = [p for p in players if p['pos'] == pos]
    if not players: return list()
    
    players = [(p, ratio(p['name'].lower(), player_name.lower())) for p in players]
    players = sorted(players, key=lambda x: x[1], reverse=True)
    
    max_val = players[0][1]
    players = [p[0] for p in players if p[1] == max_val]
    return players

def get_player_info(player_name, pos=None):
    """Get a single player with the given name and position.
    Ties are broken by percentile rank within a player's position.
    If no player is found, returns a dummy player

    Args:
        player_name (str): The name of the player to search for
        pos (str, optional): The position in {'QB', 'RB', 'WR', 'TE', 'K', 'DST'}. Defaults to None.

    Returns:
        dict: That player's info
    """
    results = search_player_info(player_name, pos)
    
    # Assume we want the best player, by percentile
    dummy_player = {'name': player_name, 'pos': pos or 'FLEX', 'rank': 100, 'percentile': 1}
    return max(results, key=lambda x: x['percentile']) if results else dummy_player

def get_players(pos):
    """Returns a list of players with the given position"""
    players = get_all_players()
    return [p for p in players if p['pos'] == pos]