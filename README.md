# NBA: Analyzing Opponent Shot Distances

# Introduction

This project aims to analyze the effect of certain defensive centers by looking at shot distance.

# How to use

To write

# Example Results

![alt text](https://github.com/SpecCRA/nba_defenders_and_shot_distance/main/fg_league.png?raw=true)

# Data Dictionary

### Main Fields
* FG_perc_* : field goal percentage by shot distance
* shotFreq_* : shot frequency calculated by shot attempts divided by total shots taken under condition

### Subfields
* league: numbers calculated without player's team's games
* with_player: only include shots taken when player is on the court
* without_player: team possessions where player is not on the court

# Players of Interest

* Bam Adebayo
* Rudy Gobert
* Draymond Green
* Deandre Ayton
* Myles Turner
* Nikola Jokic
* Giannis Antetokounmpo
* Robert Williams III
* Jaren Jackson Jr
* Joel Embiid
* Jarrett Allen
* Evan Mobley

# To Do
* Write general config using hydra
* Write general script for plotting charts without annotations

# Technologies Used
* `nba_api` library
* Python 3.10
* Python dataclasses
* Plotly
* PIL
