#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
from nba_api.stats.endpoints import GameRotation, LeagueGameFinder
from nba_api.stats.static import teams
import time
import datetime

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

# Gather game rotations
print('Begin gathering game rotations data...')
ROTATIONS_DATA = pd.DataFrame()
for game_id in CURR_SEASON_GAME_IDS:
    game_rotations = GameRotation(game_id).get_data_frames()
    time.sleep(5)
    away_rotations = game_rotations[0]
    home_rotations = game_rotations[1]
    ROTATIONS_DATA = pd.concat([ROTATIONS_DATA, away_rotations, home_rotations])
print('Finished gathering rotations data.')

# Export file
FILEPATH = '../data/2021_22_rotations_data.csv'
ROTATIONS_DATA.to_csv(FILEPATH)

print(f"Rotations data successfully outputted to {FILEPATH}")
