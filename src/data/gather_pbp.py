#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import datetime
import time
from nba_api.stats.endpoints import LeagueGameLog
from nba_api.live.nba.endpoints import playbyplay
from os.path import exists
from tqdm import tqdm

CURR_SEASON = '2021-22'

print(f"Current NBA season: {CURR_SEASON}")

print(f"Today: {datetime.date.today()}")

# See what game IDs are already in dataset
FILEPATH = '../../data/raw/2021_22_pbp_data.csv'
if exists(FILEPATH):
    print("Previous file exists. \nAdding new games.")
    EXISTING_GAMES = pd.read_csv(FILEPATH, index_col=0, dtype={'game_id': np.str})
    EXISTING_GAME_IDS = list(EXISTING_GAMES['game_id'].unique())
else:
    EXISTING_GAMES = pd.DataFrame()
    EXISTING_GAME_IDS = []

# Gather current season's game IDs
print('Gathering game IDs...')
games = LeagueGameLog(
    season=CURR_SEASON
                ).get_data_frames()[0]
CURR_SEASON_GAME_IDS = set(games['GAME_ID'])
time.sleep(0.600)
CURR_SEASON_GAME_IDS = list(CURR_SEASON_GAME_IDS)
print('Finished gathering game IDs.')

# Gather PBP
print('Gathering play by play data...')
CURR_SEASON_GAME_IDS = [game_id for game_id in CURR_SEASON_GAME_IDS if game_id not in EXISTING_GAME_IDS]
print(f"{len(CURR_SEASON_GAME_IDS)} games left.")
for gameid in tqdm(CURR_SEASON_GAME_IDS):
    pbp = playbyplay.PlayByPlay(gameid).get_dict()['game']['actions']
    time.sleep(1)
    pbp_df = pd.DataFrame.from_dict(pbp)
    pbp_df['game_id'] = gameid
    OUTPUT = pd.concat([EXISTING_GAMES, pbp_df])
print('Finished gathering play by play data.')

# Export file
EXISTING_GAMES.to_csv(FILEPATH)

print(f"File outputted to: {FILEPATH}")
