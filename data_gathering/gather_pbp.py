#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import datetime
import time
from nba_api.stats.endpoints import LeagueGameFinder
from nba_api.stats.static import teams
from nba_api.live.nba.endpoints import playbyplay

CURR_SEASON = '2021-22'

print(f"Current NBA season: {CURR_SEASON}")

print(f"Today: {datetime.date.today()}")

# Gather team IDs
TEAMS_DATA = teams.get_teams()
TEAM_IDS = [team['id'] for team in TEAMS_DATA]

# Gather current season's game IDs
print('Gathering game IDs...')
CURR_SEASON_GAME_IDS = set()
for teamid in TEAM_IDS:
    team_games = LeagueGameFinder(
                        team_id_nullable=teamid,
                        season_nullable=CURR_SEASON
                    ).get_data_frames()[0]
    game_ids = set(team_games['GAME_ID'])
    time.sleep(5)
    CURR_SEASON_GAME_IDS.update(game_ids)

print('Finished gathering game IDs.')

# Gather PBP
OUTPUT = pd.DataFrame()

print('Gathering play by play data...')
for gameid in CURR_SEASON_GAME_IDS:
    pbp = playbyplay.PlayByPlay(gameid).get_dict()['game']['actions']
    pbp_df = pd.DataFrame.from_dict(pbp)
    pbp_df['game_id'] = gameid
    time.sleep(5)
    OUTPUT = pd.concat([OUTPUT, pbp_df])
print('Finished gathering play by play data.')

# Export file
FILEPATH = '~/Documents/data_projects/nba_defenders_and_shot_distance/2021_22_pbp_data.csv'
OUTPUT.to_csv(FILEPATH)

print(f"File outputted to: {FILEPATH}")
