#!/usr/bin/env python
# -*- coding: utf-8 -*-

from filter_player_data import ShotFreq

# List of players
PLAYERS = [
    'rudy gobert',
    'draymond green',
    'deandre ayton',
    'myles turner',
    'nikola jokic',
    'giannis antetokounmpo',
    'robert williams',
    'jaren jackson jr',
    'joel embiid',
    'jarrett allen',
    'kristaps porzingis',
    'evan mobley'
]

CURR_SEASON = '2021-22'
PBP_FILEPATH = '../../data/raw/2021_22_pbp_data.csv'
ROTATIONS_FILEPATH = '../../data/raw/2021_22_rotations_data.csv'

# Gather shot frequency data
def parse_and_export():
    for name in PLAYERS:
        print(f"Starting parsing for {name}...")
        first_name = name.split(' ')[0]
        data = ShotFreq(name=name, season=CURR_SEASON)
        data.fill_player_info()
        data.load_pbp(filepath=PBP_FILEPATH)
        data.load_rotations(filepath=ROTATIONS_FILEPATH)
        data.create_pbps()
        data.create_shot_stats()

        output_path = f"../../data/processed/{first_name}_shots_data.csv"
        data.shot_stats.to_csv(output_path)
        print(f"File outputted to {output_path}")


parse_and_export()
