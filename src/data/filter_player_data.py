#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import dataclass
import pandas as pd
import numpy as np
import time
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import PlayerGameLog, BoxScoreTraditionalV2, TeamGameLog


@dataclass
class Player:
    name: str
    season: str
    playerid: str = None
    teamid: str = None
    player_gamelogs: list = None
    team_gamelogs: list = None
    games_not_played: list = None

    def _get_player_id(self):
        playerid = players.find_players_by_full_name(self.name)[0]['id']
        self.playerid = playerid

    def _get_player_gamelogs(self):
        assert len(self.season) == 7, f"Season must be in YYYY-YY format"
        gamelogs = PlayerGameLog(player_id=self.playerid, season=self.season).get_data_frames()[0]
        self.player_gamelogs = list(gamelogs['Game_ID'])

    def _get_team_id(self):
        assert self.player_gamelogs is not None, f"Player game logs not yet loaded."
        sample_boxscore = BoxScoreTraditionalV2(
            game_id=self.player_gamelogs[0]
        ).get_data_frames()[0]

        self.teamid = sample_boxscore[sample_boxscore['PLAYER_ID'] == self.playerid]['TEAM_ID'].iloc[0]

    def _get_team_logs(self):
        assert self.teamid is not None, "Team ID not yet assigned. Run self._get_team_id first."
        self.team_gamelogs = TeamGameLog(
            team_id=self.teamid,
            season=self.season
        ).get_data_frames()[0]

    def _get_games_not_played(self):
        assert self.team_gamelogs is not None, "Team gamelogs not yet assigned. Run self._get_team_logs first."
        self.games_not_played = [gameid for gameid in self.team_gamelogs if gameid not in self.player_gamelogs]

    def fill_player_info(self):
        # call each function to fill in object info
        self._get_player_id()
        self._get_player_gamelogs()
        self._get_team_id()
        time.sleep(3) # Avoid overloading NBA API
        self._get_team_logs()
        self._get_games_not_played()


@dataclass
class ShotFreq(Player):
    pbp: pd.core.frame.DataFrame = None
    rotations: pd.core.frame.DataFrame = None
    pbp_w_player: pd.core.frame.DataFrame = pd.DataFrame()
    pbp_wo_player: pd.core.frame.DataFrame = pd.DataFrame()

    def load_pbp(self, filepath):
        self.pbp = (pd.read_csv(filepath, index_col=0, dtype={'game_id': np.str})
                    .pipe(self._preprocess_pbp))

    def load_rotations(self, filepath):
        self.rotations = (pd.read_csv(filepath, index_col=0, dtype={'GAME_ID': np.str})
                          .pipe(self._preprocess_rotations))

    # helper functions
    def _preprocess_pbp(self, pbp=None):
        if pbp is None:
            pbp = self.pbp
        eight_minutes_left = 8 * 60
        pbp['scoreMargin'] = pbp['scoreHome'].to_numpy() - pbp['scoreAway'].to_numpy()
        pbp['abScoreMargin'] = np.abs(pbp['scoreMargin'])
        pbp['time'] = pbp.apply(self._conv_pbp_clock_to_seconds, axis=1)
        pbp = (pbp[
            ~((pbp['period'] == 4) & (pbp['time'] >= eight_minutes_left) & (pbp['abScoreMargin'] >= 20))
        ]
            .dropna(subset=['shotDistance'])
            .query('shotDistance <= 50')
            .pipe(self._round_shot_distances)
        )
        return pbp

    def _preprocess_rotations(self, rotations=None):
        if rotations is None:
            rotations = self.rotations
        rotations[['IN_TIME_REAL', 'OUT_TIME_REAL']] = rotations[['IN_TIME_REAL', 'OUT_TIME_REAL']].apply(
            lambda times: times/10, axis=1
        )
        rotation = rotations[
            (rotations['GAME_ID'].isin(self.player_gamelogs)) & (rotations['PERSON_ID'] == self.playerid)
        ]
        return rotations

    @staticmethod
    def _conv_pbp_clock_to_seconds(row):
        period_to_secs = (int(row['period']) - 1) * (12 * 60)
        min_to_secs = (int(row['clock'][2:4])) * 60
        secs = float(row['clock'][5:10])
        secs_left_in_quarter = (12 * 60) - (secs + min_to_secs)
        return period_to_secs + secs_left_in_quarter

    @staticmethod
    def _round_shot_distances(pbp):
        """
        Returns processed DataFrame with shot distance rounded to the nearest integer.
        """
        pbp['roundedShotDistance'] = pbp['shotDistance'].round().astype(int)
        return pbp

    def _filter_pbp_wo_player(self):
        pbp_all = self.pbp[self.pbp['game_id'].isin(self.player_gamelogs)]
        common_pbp_cols = list(pbp_all.columns)

        pbp_all = pbp_all.merge(self.pbp_w_player, on = common_pbp_cols, how='left', indicator=True)
        self.pbp_wo_player = pd.concat([pbp_all[pbp_all['_merge'] == 'left_only']])
        self.pbp_wo_player.drop(columns='_merge', inplace=True)

    def create_pbp_w_player(self):
        # Run this function before creating pbp without a player
        for gameid in self.player_gamelogs:
            game_rotation = self.rotations[self.rotations['GAME_ID'] == gameid]
            for row in game_rotation.iterrows():
                row = row[1]
                with_player = self.pbp[
                    (self.pbp['game_id'] == gameid) &
                    (self.pbp['time'].between(row['IN_TIME_REAL'], row['OUT_TIME_REAL'], inclusive='both'))
                ]
                self.pbp_w_player = pd.concat([self.pbp_w_player, with_player])

    def create_pbp_wo_player(self):
        self._filter_pbp_wo_player()
        games_without_player = self.pbp[self.pbp['game_id'].isin(self.games_not_played)]
        self.pbp_wo_player = pd.concat([self.pbp_wo_player, games_without_player])

    def create_pbps(self):
        self.create_pbp_w_player()
        self.create_pbp_wo_player()
