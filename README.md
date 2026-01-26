# ARMageddon

This project is a serious game to learn the semaphore alphabet through a game inspired by the flash game "Alphattack".

## Project Structure

*   `main.py` : The entry point of the program, execute main.py to start the game
*   `analysis/` : Scripts to generate graphs to visualize the events of a game from a logs file
*   `assets/` : The various assets used by the game
*   `game/` : The code of all elements related to the gameplay
*   `logs/` : Storage location of logs created by the game, by default we left some of our logs
*   `profiles/` : Storage location of profiles created by the game, by default we left some of our profiles
*   `requirements.txt` : list of python librairies required to run the game

## Prerequisites

Python 3.11.9

Install all the librairies in requirements.txt

To run the scripts in analysis/ you may need the aditional librairies imported at the start of the scripts

## Usage

Run main.py

To generate visualizations of the log create you will need to edit the `LOG_FILE` constant in the script.
Visualization scripts :
*  `analysis/graph_logs.py` : Display many informations of what happened during the log over time :
    * The knowledge for each letter over time
    * The average/median/minimum letter knowledge over time
    * The progress at time of destruction of every missile as well as the general trend
    * The history of events such as level transition, bombs used, bonus bar filled...
*  `analysis/letter_missile_progress.py` : Displays the progress of each missile at time of destruction per letter
