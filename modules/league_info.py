from modules import config
from espn_api.football import League
from datetime import datetime

league = League(int(config.league_id), datetime.now().year, config.espn_s2 or None, config.swid or None, debug=False)
