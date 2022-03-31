# NBA: Analyzing Opponent Shot Distances

# Introduction

This project aims to analyze the effect of certain defensive centers by looking at shot distance.

# How to use

To write

# Data Dictionary

### Main Fields
* FG_perc_* : field goal percentage by shot distance
* shotFreq_* : shot frequency calculated by shot attempts divided by total shots taken under condition

### Subfields
* league: numbers calculated without player's team's games
* with_player: only include shots taken when player is on the court
* without_player: team possessions where player is not on the court

# Players of Interest

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
* Kristaps Porzingis
* Evan Mobley

# Technologies Used
* `nba_api` library
* Python 3.10
* Python dataclasses
