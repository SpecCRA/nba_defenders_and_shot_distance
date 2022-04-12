#!/usr/bin/env python
# -*- coding: utf-8 -*-

from filter_player_data import ShotFreq
from tqdm import tqdm

# List of players
PLAYERS = [
    'bam adebayo',
    'deandre ayton',
    'draymond green',
    'evan mobley',
    'giannis antetokounmpo',
    'jarrett allen',
    'jaren jackson jr',
    'joel embiid',
    'myles turner',
    'nikola jokic',
    'robert williams',
    'rudy gobert'
]

CURR_SEASON = '2021-22'
PBP_FILEPATH = '../../data/raw/2021_22_pbp_data.csv'
ROTATIONS_FILEPATH = '../../data/raw/2021_22_rotations_data.csv'


# Gather shot frequency data
def parse_and_export():
    for name in tqdm(PLAYERS):
        print(f"Starting parsing for {name}...")
        first_initial = name.split(' ')[0][0]
        last_name = name.split(' ')[1]
        data = ShotFreq(name=name, season=CURR_SEASON)
        data.fill_player_info()
        data.load_pbp(filepath=PBP_FILEPATH)
        data.load_rotations(filepath=ROTATIONS_FILEPATH)
        data.create_pbps()
        data.create_shot_stats()

        output_path = f"../../data/processed/{first_initial}{last_name}_shots_data.csv"
        data.shot_stats.to_csv(output_path)
        print(f"File outputted to {output_path}")


parse_and_export()
