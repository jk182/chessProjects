import chess
import chess.pgn
import random
import resultPrediction
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import yaml
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plotting_helper
import argparse


def eloFormula(playerRating: int, oppRating: int) -> float:
    return 1 / (1 + 10**((oppRating-playerRating)/400))
    

def getBaseDrawRate(rating: int) -> float:
    """
    This calculates the base draw rate for a given rating, based on some estimations
    """
    if rating < 2500:
        return 0.5

    if 2500 <= rating < 2600:
        return 0.575 + ((rating-2500)/100) * 0.025

    if 2600 <= rating < 2700:
        return 0.6 + ((rating-2600)/100) * 0.05

    if 2700 <= rating < 2800:
        return 0.65 + ((rating-2700)/100) * 0.10

    return 0.75


def linearDrawRate(ratingDiff: float, k: float, ratingOffset: int = 0):
    """
    This calculates the relative draw rate based on rating difference
    """
    if ratingDiff < ratingOffset:
        return 1
    return k * (ratingDiff-ratingOffset) + 1


def predictResult(whiteRating: int, blackRating: int, whiteK: float = -0.002359, blackK: float = -0.002829) -> list:
    """
    This predicts the results of a game between players of given ratings.
    return -> list:
        [winProbability, drawProb, lossProb] from white's perspective
    whiteK, blackK
        The slope used for the relative draw rate fromula. The values come from real games
    """
    ratingDiff = abs(whiteRating-blackRating)
    if whiteRating+35 >= blackRating:
        expectedScore = eloFormula(whiteRating+35, blackRating)
        baseDrawRate = getBaseDrawRate(whiteRating)
        relativeDrawRate = linearDrawRate(ratingDiff, whiteK)
    else:
        expectedScore = eloFormula(blackRating, whiteRating+35)
        baseDrawRate = getBaseDrawRate(blackRating)
        relativeDrawRate = linearDrawRate(ratingDiff, blackK, ratingOffset=100)

    draws = baseDrawRate * relativeDrawRate * 0.96
    wins = expectedScore - 0.5*draws
    losses = 1 - draws - wins

    if whiteRating+35 >= blackRating:
        return [wins, draws, losses]
    return [losses, draws, wins]


def simulatePlayoff(tiedPlayers: list, playoffRatings: dict, tc: str) -> str:
    """
    This simulates a playoff (according to the rules of the 2026 Candidates) and returns the name of the winning player
    """
    tbPoints = {player: 0 for player in tiedPlayers}
    if tc == 'rapid':
        ratings = {player: r[0] for player, r in playoffRatings.items()}
    else:
        ratings = {player: r[1] for player, r in playoffRatings.items()}

    if len(tiedPlayers) == 1:
        return tiedPlayers[0]

    if len(tiedPlayers) > 2:
        points = dict()
        for player in tiedPlayers:
            points[player] = 0

        for i, player in enumerate(tiedPlayers):
            for j, opponent in enumerate(tiedPlayers[i+1:]):
                if j % 2 == 0:
                    white = player
                    black = opponent
                else:
                    white = opponent
                    black = player

                predictedResult = predictResult(ratings[white], ratings[black])
                x = random.random()
                if x <= predictedResult[0]:
                    tbPoints[white] += 1
                elif x <= predictedResult[0]+predictedResult[1]:
                    tbPoints[white] += 0.5
                    tbPoints[black] += 0.5
                else:
                    tbPoints[black] += 1

        tbPoints = dict(reversed(sorted(tbPoints.items(), key=lambda x: x[1])))
        newTiedPlayers = [player for player, points in tbPoints.items() if points == list(tbPoints.values())[0]]
        if len(newTiedPlayers) == 1:
            return newTiedPlayers[0]
        return simulatePlayoff(newTiedPlayers, playoffRatings, 'blitz')

    for i in range(2):
        white = tiedPlayers[i]
        black = tiedPlayers[(i+1)%2]

        predictedResult = predictResult(ratings[white], ratings[black])
        x = random.random()
        if x <= predictedResult[0]:
            tbPoints[white] += 1
        elif x <= predictedResult[0]+predictedResult[1]:
            tbPoints[white] += 0.5
            tbPoints[black] += 0.5
        else:
            tbPoints[black] += 1

    if tbPoints[tiedPlayers[0]] > tbPoints[tiedPlayers[1]]:
        return tiedPlayers[0]

    if tbPoints[tiedPlayers[1]] > tbPoints[tiedPlayers[0]]:
        return tiedPlayers[1]

    return simulatePlayoff(tiedPlayers, playoffRatings, 'blitz')


def simulateTiebreaks(tournamentResult: dict, firstPlacePlayoff: bool = False, playoffRatings: dict = None) -> tuple:
    playerPoints = dict()
    for player in tournamentResult.keys():
        playerPoints[player] = tournamentResult[player][0] + tournamentResult[player][1] * 0.5

    playerPoints = dict(reversed(sorted(playerPoints.items(), key=lambda x: x[1])))

    playerStandings = list(playerPoints.keys())
    finalPoints = list(playerPoints.values())

    for i, (player, points) in enumerate(list(playerPoints.items())[:-1]):
        if points == finalPoints[i+1]:
            if tournamentResult[playerStandings[i]][0] < tournamentResult[playerStandings[i+1]][0]:
                p = playerStandings[i]
                playerStandings[i] = playerStandings[i+1]
                playerStandings[i+1] = p

    tiedForFirst = list()
    if firstPlacePlayoff and finalPoints[0] == finalPoints[1]:
        tiedForFirst = [player for player, points in playerPoints.items() if points == finalPoints[0]]
        winner = simulatePlayoff(tiedForFirst, playoffRatings, 'rapid')

        if winner != playerStandings[0]:
            playerStandings[playerStandings.index(winner)] = playerStandings[0]
            playerStandings[0] = winner

    return (playerStandings, tiedForFirst)


def simulateTournament(players: dict, pairings: list, simulations: int = 20000, startResults: dict = {}, firstPlacePlayoff: bool = False, playoffRatings: dict = None, playersToFollow: list = None) -> dict:
    data = dict()
    for player in players.keys():
        data[player] = list()

    if playoffRatings is None and firstPlacePlayoff:
        playoffRatings = {player: [rating, rating] for player, rating in players.items()}

    playedGames = sum([sum(wdl) for wdl in startResults.values()])//2
    print(playedGames)
    print(pairings[:playedGames])

    if playersToFollow is not None:
        playerResults = {player: list() for player in playersToFollow}

    for n in range(simulations):
        players['Nakamura, Hikaru'] = 2775 + 30*random.random()
        for white, black in pairings[playedGames:]:
            for player in [white, black]:
                if len(data[player]) <= n:
                    if player in startResults:
                        wdl = startResults[player].copy()
                    else:
                        wdl = [0, 0, 0]
                    data[player].append([wdl, 0, False])

                    if playersToFollow is not None and player in playersToFollow:
                        playerResults[player].append(list())
                    
            predictedResult = predictResult(players[white], players[black])
            x = random.random()
            if x <= predictedResult[0]:
                resultIndex = 0
            elif x <= predictedResult[0] + predictedResult[1]:
                resultIndex = 1
            else:
                resultIndex = 2

            data[white][-1][0][resultIndex] += 1
            data[black][-1][0][2-resultIndex] += 1

            if playersToFollow:
                if white in playersToFollow:
                    playerResults[white][-1].append((2-resultIndex)/2)
                if black in playersToFollow:
                    playerResults[black][-1].append(resultIndex/2)

        lastSimWDL = {player: d[-1][0] for player, d in data.items()}
        playerStandings, tied = simulateTiebreaks(lastSimWDL, firstPlacePlayoff, playoffRatings)

        for place, player in enumerate(playerStandings):
            data[player][-1][1] = place+1
            data[player][-1][2] = player in tied

    with open('../out/candidatesPlayerData.yaml', 'w+') as f:
        print(yaml.dump(playerResults), file=f)

    """
    with open('../out/candidatesSim.yaml', 'w+') as f:
        print(yaml.dump(data), file=f)
    """

    return data


def getPlaceProbabilities(tournamentSim: dict) -> dict:
    places = dict()
    for player, data in tournamentSim.items():
        places[player] = [0] * (len(tournamentSim.keys()) + 1)
        for d in data:
            places[player][d[1]] += 1
            if d[2]:
                places[player][0] += 1

        for i in range(len(places[player])):
            places[player][i] /= len(data)
    return places


def getClearAndTBWins(tournamentSim: dict) -> dict:
    """
    This counts the number of clear wins and wins after tiebreaks
    """
    wins = dict()
    for player, data in tournamentSim.items():
        wins[player] = [0, 0]
        for d in data:
            if d[1] == 1:
                if d[2]:
                    wins[player][1] += 1
                else:
                    wins[player][0] += 1

        wins[player][0] /= len(data)
        wins[player][1] /= len(data)
    return wins


def plotPlaceProbabilities(placeProbabilities: dict, playerColors: dict = None, filename: str = None):
    playerColors = {'Sindarov, Javokhir': plotting_helper.getColor('much better'), 'Wei, Yi': plotting_helper.getColor('red'), 
                    'Bluebaum, Matthias': plotting_helper.getColor('yellow'), 'Esipenko, Andrey': plotting_helper.getColor('purple'), 
                    'Praggnanandhaa R': plotting_helper.getColor('darkorange'), 'Giri, Anish': plotting_helper.getColor('darkblue'), 
                    'Caruana, Fabiano': plotting_helper.getColor('blue'), 'Nakamura, Hikaru': plotting_helper.getColor('violet')}

    playerColors = {'Divya Deshmukh': plotting_helper.getColor('much better'), 'Muzychuk, Anna': plotting_helper.getColor('red'), 
                      'Vaishali, Rameshbabu': plotting_helper.getColor('yellow'), 'Assaubayeva, Bibisara': plotting_helper.getColor('purple'), 
                      'Goryachkina, Aleksandra': plotting_helper.getColor('darkorange'), 'Lagno, Kateryna': plotting_helper.getColor('darkblue'), 
                      'Zhu, Jiner': plotting_helper.getColor('darkorange'), 'Tan, Zhongyi': plotting_helper.getColor('violet')}
    if playerColors is None:
        playerColors = dict()
        colors = plotting_helper.getDefaultColors()
        for i, player in enumerate(list(placeProbabilities.keys())):
            playerColors[player] = colors[i%len(colors)]

    placeProbabilities = dict(sorted(placeProbabilities.items(), key=lambda x: sum([(i+1)*p for i, p in enumerate(x[1])])))

    fig, ax = plt.subplots(len(placeProbabilities), figsize=(6, 8), sharey=True)

    yMax = max([max(places) for places in placeProbabilities.values()])
    for i, (player, places) in enumerate(placeProbabilities.items()):
        ax[i].set_facecolor(plotting_helper.getColor('background'))
        yMax = max(yMax, max(places))
        # ax.plot(range(1, len(places)), places[1:], label=player.split(',')[0].split()[0], color=playerColors[player], linewidth=2)
        ax[i].bar(range(1, len(places)), places[1:], label=player.split(',')[0].split()[0], color=playerColors[player], width=1, edgecolor='black')
        ax[i].set_xlim(0.5, len(places)-0.5)
        ax[i].set_ylim(0, yMax*1.05)
        ax[i].legend()
        ax[i].label_outer()

    fig.text(0.03, 0.37, "Probability to finish in that position", ha='center', rotation='vertical')
    ax[0].set_title("Probabilities of different finishing positions for each player")
    ax[-1].set_xlabel('Finishing position')
    # ax.legend(loc='upper center', ncol=4)
    # ax.set_xlim(1, len(places)-1)

    # plt.title("Finish position probabilities for each player in the Women's Candidates tournament")

    fig.subplots_adjust(bottom=0.07, top=0.95, left=0.1, right=0.95)

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def plotWinningChances(winProbabilities: dict, filename: str = None):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor(plotting_helper.getColor('background'))

    winProbabilities = dict(reversed(sorted(winProbabilities.items(), key=lambda x: sum(x[1]))))
    outrightWins = [wins[0] for wins in winProbabilities.values()]
    TBwins = [wins[1] for wins in winProbabilities.values()]
    labels = [player.split(',')[0].split()[0] for player in winProbabilities.keys()]

    ax.bar(labels, outrightWins, color=plotting_helper.getColor('blue'), label='Outright win probability', edgecolor='black')
    ax.bar(labels, TBwins, bottom=outrightWins, color=plotting_helper.getColor('green'), edgecolor='black', label='Tiebreak win probability')

    ax.legend()
    plt.title("The win probability for each player in the Women's Candidates tournament")
    ax.set_ylabel('Win probabilitiy')
    ax.set_xlim(0-0.6, len(labels)-0.4)
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def plotTournamentStandings(wdlData: dict, filename: str = None):
    """
    This plots the standings in the tournament, given the number of wins, draws in losses for each player
    wdlData: dict
        {playerName: [wins, draws, losses], ...}
    """
    wdlData = dict(reversed(sorted(wdlData.items(), key=lambda x: x[1][0]+x[1][1]*0.5)))
    plotData = dict()
    for player, wdl in wdlData.items():
        plotData[player.split(',')[0].split()[0]] = f'{wdl[0]+wdl[1]/2}/{sum(wdl)}'

    fig, ax = plt.subplots()
    # ax.set_facecolor(plotting_helper.getColor('background'))

    fig.patch.set_visible(False)
    ax.axis('off')
    ax.axis('tight')

    colors = [plotting_helper.getColors(['background', 'background'])] * len(plotData)
    table = ax.table(cellText=list(plotData.items()), colLabels=['Player', 'Points'], loc='center', colLoc='left', cellLoc='left', colWidths=[0.3, 0.1], cellColours=colors, colColours=plotting_helper.getColors(['background', 'background']))

    for (row, col), cell in table.get_celld().items():
        if (row == 0) or (col == -1):
            cell.set_text_props(fontproperties=FontProperties(weight='bold'), size='xx-large')
            cell.set(linewidth=1.5)

    fig.tight_layout()

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def commandLine():
    parser = argparse.ArgumentParser(prog='Tournament simulation', 
                                     description='This script runs the simulation of a tournament')

    parser.add_argument('--config_path', default='configFiles/config', help="Path to the YAML config files")
    parser.add_argument('--tournament_name', default='', help='Name of the tournament for the config files')
    parser.add_argument('--pgn', default=None, help="PGN file to generate config files")
    parser.add_argument('-n', '--nSimulations', default=50000, help="Number of simulations to run")
    parser.add_argument('--no_playoff_simulation', action='store_false', help="If this is set, there won't be a simulation for a tiebreak playoff")
    parser.add_argument('--use_playoff_ratings', action='store_true', help="If this is set, separate playoff ratings will be used")
    parser.add_argument('--use_start_results', action='store_true', help="If this is set, the players start out with points specified by a config file")

    args = parser.parse_args()

    if args.pgn is not None:
        ratings = resultPrediction.getPlayersFromPGN(args.pgn)
        pairings = resultPrediction.getPairingsFromPGN(args.pgn)
        with open(f'{args.config_path}Ratings{args.tournament_name}.yaml', 'w+') as f:
            print(yaml.dump(ratings), file=f)
        with open(f'{args.config_path}Pairings{args.tournament_name}.yaml', 'w+') as f:
            print(yaml.dump(pairings), file=f)
    else:
        with open(f'{args.config_path}Ratings{args.tournament_name}.yaml', 'r') as f:
            ratings = yaml.load(f, Loader=yaml.FullLoader)
        with open(f'{args.config_path}Pairings{args.tournament_name}.yaml', 'r') as f:
            pairings = yaml.load(f, Loader=yaml.FullLoader)

    if args.use_playoff_ratings:
        with open(f'{args.config_path}PlayoffRatings{args.tournament_name}.yaml', 'r') as f:
            playoffRatings = yaml.load(f, Loader=yaml.FullLoader)
    else:
        playoffRatings = None

    if args.use_start_results:
        with open(f'{args.config_path}StartResults{args.tournament_name}.yaml', 'r') as f:
            startResults = yaml.load(f, Loader=yaml.FullLoader)
    else:
        startResults = dict()

    tournamentSim = simulateTournament(ratings, pairings, 
                                       simulations=int(args.nSimulations), 
                                       firstPlacePlayoff=args.no_playoff_simulation, 
                                       playoffRatings=playoffRatings,
                                       startResults=startResults, # playersToFollow=['Vaishali, Rameshbabu', 'Zhu, Jiner'])
                                       playersToFollow=['Sindarov, Javokhir', 'Giri, Anish'])
    
    for player, wins in getClearAndTBWins(tournamentSim).items():
        print(player, sum(wins))

    """
    placeProbs = getPlaceProbabilities(tournamentSim)
    plotPlaceProbabilities(placeProbs, filename='../out/candidatesPlaceProbsW.png')

    with open( '../out/candidatesPlayerData.yaml', 'r') as f:
        playerData = yaml.load(f, Loader=yaml.FullLoader)
    """

    # analyseTournamentSimulation(tournamentSim, playerData)


def analyseTournamentSimulation(simData: dict, playerData: dict):
    focusPlayer = 'Giri, Anish'
    # focusPlayer = 'Zhu, Jiner'
    focusRound = 1
    giriGameWins = dict()
    giriTWins = dict()
    tWinIndices = list()
    for player in simData.keys():
        giriGameWins[player] = list()

    for player in playerData.keys():
        giriTWins[player] = list()

    for i, results in enumerate(playerData[focusPlayer]):
        """
        if results[focusRound] == 0:
        # if results[1] == 0.5 and results[3] == 0.5:
            for player in simData.keys():
                giriGameWins[player].append(simData[player][i])
        """

        if simData[focusPlayer][i][1] == 1:
            tWinIndices.append(i)
            for player in simData.keys():
                giriGameWins[player].append(simData[player][i])
            for player in giriTWins.keys():
                giriTWins[player].append(playerData[player][i])

    for player, wins in getClearAndTBWins(giriGameWins).items():
        print(player, sum(wins), wins[1])

    for player, data in giriTWins.items():
        print(len(data))
        print(player)
        print(sum([sum(d) for d in data])/len(data))
        print(sum([sum(d) for d in playerData[player]])/len(playerData[player]))
        


if __name__ == '__main__':
    commandLine()
    # print(analyseTournamentSimulation('../out/candidatesSim.yaml', '../out/candidatesPlayerData.yaml'))
    for end in ['', 'W']:
        with open(f'configFiles/configStartResultsCandidates{end}.yaml', 'r') as f:
            standings = yaml.load(f, Loader=yaml.FullLoader)
        plotTournamentStandings(standings, f'../out/standingsCandidates{end}.png')

    """
    playoffRatings = {'Sindarov, Javokhir': [2727, 2662], 'Wei, Yi': [2726, 2698], 'Bluebaum, Matthias': [2587, 2634], 'Esipenko, Andrey': [2657, 2652], 'Praggnanandhaa R': [2663, 2698], 'Giri, Anish': [2689, 2666], 'Caruana, Fabiano': [2727, 2769], 'Nakamura, Hikaru': [2742, 2838]}
    playoffRatingsW = {'Divya Deshmukh': [2416, 2351], 'Muzychuk, Anna': [2398, 2400], 'Vaishali, Rameshbabu': [2387, 2371], 'Assaubayeva, Bibisara': [2439, 2457], 'Goryachkina, Aleksandra': [2499, 2424], 'Lagno, Kateryna': [2435, 2414], 'Zhu, Jiner': [2479, 2411], 'Tan, Zhongyi': [2502, 2424]}
    candidatesOpen = '../resources/candidatesPairingsOpen.pgn'
    candidatesWomen = '../resources/candidatesPairingsWomen.pgn'
    ratings = resultPrediction.getPlayersFromPGN(candidatesOpen)
    data = yaml.dump(playoffRatings)
    print(data)
    print(yaml.load(data, Loader=yaml.FullLoader))
    ratingsW = resultPrediction.getPlayersFromPGN(candidatesWomen)
    pairings = resultPrediction.getPairingsFromPGN(candidatesOpen)
    pairingsW = resultPrediction.getPairingsFromPGN(candidatesWomen)
    # tournamentSim = simulateTournament(ratings, pairings, simulations=50000, firstPlacePlayoff=True, playoffRatings=playoffRatings, startResults={'Bluebaum, Matthias': [2, 1, 0]})
    ratingsW['Divya Deshmukh'] += 12.6
    ratingsW['Zhu, Jiner'] -= 23.5
    # tournamentSim = simulateTournament(ratingsW, pairingsW, simulations=50000, firstPlacePlayoff=True, playoffRatings=playoffRatingsW)
    # print(sum([1 for i in range(50000) for player in tournamentSim.keys() if any([tournamentSim[player][i][2]])])/50000)
    places = getPlaceProbabilities(tournamentSim)
    colors = plotting_helper.getColors(['much better', 'red', 'yellow', 'purple', 'darkorange', 'darkblue', 'blue', 'violet'])
    playerColors = dict()
    playerColorsW = dict()
    for i, player in enumerate(list(playoffRatings.keys())):
        playerColors[player] = colors[i]
    for i, player in enumerate(list(playoffRatingsW.keys())):
        playerColorsW[player] = colors[i]
    # plotPlaceProbabilities(places, playerColorsW, filename='../out/candidatesWomenPlaces.png')

    wins = getClearAndTBWins(tournamentSim)
    print(wins)
    # plotWinningChances(wins, filename='../out/candidatesWomenFirst.png')
    """
