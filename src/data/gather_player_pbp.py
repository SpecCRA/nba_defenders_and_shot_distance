#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import time
from nba_api.stats.static import players
from nba_api.stats.endpoints import PlayerGameLogs
from nba_api.live.nba.endpoints import playbyplay


# function to get player ID
def _get_player_id(full_name: str):
    player_id = players.find_players_by_full_name(full_name)
    return str(player_id[0]['id'])


# function to by player id gather game IDs
def _get_games_ids(playerid: str, season: str):
    gamelogs = PlayerGameLogs(
        season_nullable=season,
        player_id_nullable=playerid
    ).get_data_frames()[0]

    return list(gamelogs['GAME_ID'])


# function to gather pbp data with game ID input
def _get_game_pbp(gameid: str):
    pbp = playbyplay.PlayByPlay(
        game_id=gameid
    ).get_dict()['game']['actions']

    df = pd.DataFrame.get_dict(pbp)
    time.sleep(3) # prevent timeout from server
    return df


def get_all_player_pbp(full_name: str, season: str):
    player_id = _get_player_id(full_name)
    game_ids = _get_games_ids(player_id, season)
    output = pd.DataFrame()
    for gameid in game_ids:
        df = _get_game_pbp(gameid)
        output = pd.concat([output, df])
        # should i write a csv file in case of errors

    return output
