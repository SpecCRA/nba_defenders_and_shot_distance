#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
import pandas as pd
import numpy as np
import time
from nba_api.stats.static import players
from nba_api.stats.endpoints import PlayerGameLog, BoxScoreTraditionalV2, TeamGameLog
import requests


@dataclass
class Player:
    name: str
    season: str
    playerid: str = None
    teamid: str = None
    player_gamelogs: [str] = field(default_factory=list)
    team_gamelogs: [str] = field(default_factory=list)
    games_not_played: [str] = field(default_factory=list)
    image_url: str = None

    def _get_player_id(self):
        playerid = players.find_players_by_full_name(self.name)[0]['id']
        time.sleep(0.600)
        self.playerid = playerid

    def _get_player_gamelogs(self):
        assert len(self.season) == 7, f"Season must be in YYYY-YY format"
        gamelogs = PlayerGameLog(player_id=self.playerid, season=self.season).get_data_frames()[0]
        time.sleep(0.600)
        self.player_gamelogs = list(gamelogs['Game_ID'].unique())

    def _get_team_id(self):
        assert self.player_gamelogs is not None, f"Player game logs not yet loaded."
        sample_boxscore = BoxScoreTraditionalV2(
            game_id=self.player_gamelogs[0]
        ).get_data_frames()[0]
        time.sleep(0.600)

        self.teamid = sample_boxscore[sample_boxscore['PLAYER_ID'] == self.playerid]['TEAM_ID'].iloc[0]

    def _get_team_logs(self):
        assert self.teamid is not None, "Team ID not yet assigned. Run self._get_team_id first."
        gamelogs = TeamGameLog(
            team_id=self.teamid,
            season=self.season
        ).get_data_frames()[0]
        time.sleep(0.600)
        self.team_gamelogs = list(gamelogs['Game_ID'].unique())

    def _get_games_not_played(self):
        assert self.team_gamelogs is not None, "Team gamelogs not yet assigned. Run self._get_team_logs first."
        self.games_not_played = [gameid for gameid in self.team_gamelogs if gameid not in self.player_gamelogs]

    def _get_player_image(self):
        self.image_url = f"https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{self.playerid}.png"
        time.sleep(0.600)
        output_path = '../../data/player_images/'
        img_data = requests.get(self.image_url).content
        with open(f"{output_path}{self.name}.png", 'wb') as handler:
            handler.write(img_data)

    def fill_player_info(self):
        # call each function to fill in object info
        self._get_player_id()
        self._get_player_gamelogs()
        self._get_team_id()
        self._get_player_image()
        self._get_team_logs()
        self._get_games_not_played()
        time.sleep(1)


@dataclass
class ShotFreq(Player):
    pbp: pd.core.frame.DataFrame = None
    rotations: pd.core.frame.DataFrame = None
    pbp_w_player: pd.core.frame.DataFrame = pd.DataFrame()
    pbp_wo_player: pd.core.frame.DataFrame = pd.DataFrame()
    shot_stats: pd.core.frame.DataFrame = None

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
        pbp['scoreMargin'] = pbp['scoreHome'].to_numpy() - pbp['scoreAway'].to_numpy()
        pbp['abScoreMargin'] = np.abs(pbp['scoreMargin'])
        pbp['time'] = pbp.apply(self._conv_pbp_clock_to_seconds, axis=1)
        pbp = (pbp
               .dropna(subset=['shotDistance'])
               .query('shotDistance <= 35')
               .pipe(self._round_shot_distances)
               .pipe(self._remove_garbage_pbp_time)
               )
        return pbp

    def _preprocess_rotations(self, rotations=None):
        if rotations is None:
            rotations = self.rotations
        rotations[['IN_TIME_REAL', 'OUT_TIME_REAL']] = rotations[['IN_TIME_REAL', 'OUT_TIME_REAL']].apply(
            lambda times: times / 10, axis=1
        )
        rotations = rotations[
            (
                (rotations['PERSON_ID'] == self.playerid)
            )
        ]
        return rotations

    def _remove_garbage_pbp_time(self, df=None, blowout_time_marker=None):
        if blowout_time_marker is None:
            blowout_time_marker = (4*60) + (3*12*60)
        if df is None:
            df = self.pbp

        games = df['game_id'].unique()
        garbage_rows = pd.DataFrame()
        for game in games:
            game_df = df[df['game_id'] == game].sort_values(by='time')
            end_of_game = game_df[game_df['time'] >= blowout_time_marker]
            if len(end_of_game) == 0:
                continue
            elif end_of_game.head(n=1).iloc[0]['abScoreMargin'] >= 20:
                garbage_rows = pd.concat([garbage_rows, end_of_game])

        df = pd.merge(df, garbage_rows, how='outer', indicator=True)
        output = df[df['_merge'] == 'left_only'].drop(columns=['_merge'])
        return output

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

        pbp_all = pbp_all.merge(self.pbp_w_player, on=common_pbp_cols, how='left', indicator=True)
        self.pbp_wo_player = pd.concat([pbp_all[pbp_all['_merge'] == 'left_only']])
        self.pbp_wo_player.drop(columns='_merge', inplace=True)

    def create_pbp_w_player(self):
        # Run this function before creating pbp without a player
        for gameid in self.player_gamelogs:
            game_rotation = self.rotations[self.rotations['GAME_ID'] == gameid]
            for row in game_rotation.iterrows():
                row = row[1]
                with_player = self.pbp[
                    (
                            (self.pbp['game_id'] == gameid) &
                            (self.pbp['time'].between(row['IN_TIME_REAL'], row['OUT_TIME_REAL'], inclusive='both'))
                    )
                ]
                self.pbp_w_player = pd.concat([self.pbp_w_player, with_player])

    def create_pbp_wo_player(self):
        self._filter_pbp_wo_player()
        games_without_player = self.pbp[self.pbp['game_id'].isin(self.games_not_played)]
        self.pbp_wo_player = pd.concat([self.pbp_wo_player, games_without_player])

    def create_pbps(self):
        self.create_pbp_w_player()
        self.create_pbp_wo_player()

    @staticmethod
    def _create_shot_agg(df):
        assert 'roundedShotDistance' in df.columns, "Rounded shot distance not yet created."
        df = df.groupby('roundedShotDistance')['shotResult'].value_counts().rename('value_counts').reset_index()
        return df

    def _select_dataframe(self, player_mode: np.str):
        # player or not
        if player_mode == 'with_player':
            return self._create_shot_agg(self.pbp_w_player)
        elif player_mode == 'without_player':
            return self._create_shot_agg(self.pbp_wo_player)
        elif player_mode == 'league':
            df = self.pbp[~(self.pbp['game_id'].isin(self.team_gamelogs))]
            return self._create_shot_agg(df)

    def create_agg_data(self, player_mode: np.str):
        df = self._select_dataframe(player_mode)

        # calculate shot accuracies
        shot_distances = list(df['roundedShotDistance'].unique())
        total_shots = df['value_counts'].sum()
        shot_accuracies = []
        shot_frequencies = []

        for dist in shot_distances:
            df_slice = df[df['roundedShotDistance'] == dist]
            if len(df_slice) <= 1:
                made_shots = 0
            else:
                made_shots = df_slice[df_slice['shotResult'] == 'Made']['value_counts'].iloc[0]
            acc = made_shots / df_slice['value_counts'].sum()
            shot_accuracies.append(acc)
            shot_freq = df_slice['value_counts'].sum() / total_shots
            shot_frequencies.append(shot_freq)

        output = pd.DataFrame(
            {
                'roundedShotDistance': shot_distances,
                f"FG_perc_{player_mode}": shot_accuracies,
                f"shotFreq_{player_mode}": shot_frequencies
            }
        )

        self.merge_shot_stats(df=output)

    def merge_shot_stats(self, df):
        merge_col = 'roundedShotDistance'
        if self.shot_stats is None:
            self.shot_stats = df
        else:
            self.shot_stats = df.merge(self.shot_stats, how='right', on=merge_col)

    def create_shot_stats(self):
        for mode in ['with_player', 'without_player', 'league']:
            self.create_agg_data(player_mode=mode)
