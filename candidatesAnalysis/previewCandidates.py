import chess
import chess.pgn
import requests
from bs4 import BeautifulSoup
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plotting_helper
import matplotlib.pyplot as plt


def getFideRatingData(fideIDs: dict, startYear: int, startMonth: str = 'Jan') -> dict:
    """
    This gets the rating data for the given players
    fideIDs: dict
        {playerName: fideID, ...}
    startYear: int
        The earliest year to get the data from
    startMonth: str
        The month in the year when data should be gathered.
    return -> dict:
        {playerName: [startRating, ratingNextMonth, ...], ...}
    """
    ratingData = dict()
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for player, ID in fideIDs.items():
        ratingData[player] = list()
        r = requests.get(f'https://ratings.fide.com/profile/{ID}/chart')

        soup = BeautifulSoup(r.content, 'html.parser')
        # print(soup.prettify())
        for tr in soup.find_all('tr'):
            l = [td.text.strip() for td in tr.find_all('td') if td.text.strip()]
            if l:
                if '-' in l[0]:
                    ls = l[0].split('-')
                    year = int(ls[0])
                    month = ls[1]
                    if year > startYear or (year == startYear and months.index(month) >= months.index(startMonth)):
                        ratingData[player].append(int(l[1]))
        ratingData[player] = list(reversed(ratingData[player]))
    return ratingData


def getPlayerWDL(players: list, pgnFolder: str) -> dict:
    """
    This gets the number of wins, draws and losses for each player
    players: list
        List with the player names
    pgnFolder: str
        Path to the folder containing the PGN files titles playername.pgn
    return -> dict
        {playerName: [[whiteWins, blackWins], [whiteDraws, blackDraws], [whiteLosses, blackLosses]], ...}
    """
    wdls = dict()
    for player in players:
        wdls[player] = [[0, 0], [0, 0], [0, 0]]
        lastName = player.split(',')[0].split()[0]
        with open(f'{pgnFolder}/{lastName.lower()}.pgn', 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                if lastName in game.headers["White"]:
                    white = True
                elif lastName in game.headers["Black"]:
                    white = False
                else:
                    print(f'Player {lastName} not found in {game.headers["White"]}-{game.headers["Black"]}')

                result = game.headers["Result"]
                if result == '1-0':
                    if white:
                        wdls[player][0][0] += 1
                    else:
                        wdls[player][2][1] += 1
                elif result == '1/2-1/2':
                    if white:
                        wdls[player][1][0] += 1
                    else:
                        wdls[player][1][1] += 1
                elif result == '0-1':
                    if white:
                        wdls[player][2][0] += 1
                    else:
                        wdls[player][0][1] += 1
                else:
                    print(f'Result {result} not found in {game.headers["White"]}-{game.headers["Black"]}')

    return wdls


def getPlayerOpenings(players: list, pgnFolder: str) -> dict:
    """
    This function counts how often the players have played different openings with each color
    return -> dict:
        {playerName: {openingName: [nWhiteGames, nBlackGames], ...}, ...}
    """
    openings = dict()
    for player in players:
        openings[player] = dict()
        lastName = player.split(',')[0].split()[0]
        with open(f'{pgnFolder}/{lastName.lower()}.pgn', 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                if lastName in game.headers["White"]:
                    colorIndex = 0
                elif lastName in game.headers["Black"]:
                    colorIndex = 1
                else:
                    print(f'Player {lastName} not found in {game.headers["White"]}-{game.headers["Black"]}')

                opening = game.headers["Opening"]
                opening = opening.split('(')[0].split(',')[0].strip()

                if opening not in openings[player]:
                    openings[player][opening] = [0, 0]

                openings[player][opening][colorIndex] += 1

    return openings


def getWhiteFirstMoves(players: list, pgnFolder: str) -> dict:
    firstMoves = dict()
    for player in players:
        firstMoves[player] = dict()
        lastName = player.split(',')[0].split()[0]
        with open(f'{pgnFolder}/{lastName.lower()}.pgn', 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                if lastName in game.headers["White"]:
                    board = game.board()

                    firstMove = board.san(list(game.mainline_moves())[0])
                    if firstMove not in firstMoves[player]:
                        firstMoves[player][firstMove] = 1
                    else:
                        firstMoves[player][firstMove] += 1
    return firstMoves


def plotRatingProgression(ratingData: dict, startDate: str, filename: str = None):
    """
    This generates a rating plot for each player, where the other players are included in smaller grey lines
    """
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    xTickGap = 4
    totalMonths = len(list(ratingData.values())[0])
    startYear = int(startDate.split('-')[0])
    startMonth = int(startDate.split('-')[1])
    xTickLabels = [f'{months[startMonth]}-{startYear}']
    for i in range(xTickGap, totalMonths, xTickGap):
        currentMonth = startMonth + i
        currentYear = startYear + currentMonth // 12
        xTickLabels.append(f'{months[currentMonth%12]}-{currentYear}')

    for player, ratings in ratingData.items():
        fig, ax = plt.subplots(figsize=(5, 1))
        ax.set_facecolor(plotting_helper.getColor('background'))

        for p, r in ratingData.items():
            if p != player:
                ax.plot(range(len(r)), r, linewidth=1, color='grey')
        ax.plot(range(len(ratings)), ratings, linewidth=2, color=plotting_helper.getColor('blue'))

        ax.grid()
        ax.set_xticks(range(0, totalMonths, xTickGap))
        ax.set_xticklabels(xTickLabels)
        ax.set_xlim(0, len(ratings)-1)
        ax.tick_params(axis='both', which='major', labelsize=8)
        ax.tick_params(axis='both', which='minor', labelsize=8)
        if filename:
            plt.savefig(f'{filename}_{player.split(",")[0].split()[0]}.png', dpi=300)
        else:
            plt.show()

        break


if __name__ == '__main__':
    openCandidates = {'Caruana, Fabiano': 2020009, 'Nakamura, Hikaru': 2016192, 'Praggnanandhaa R': 25059530, 'Wei, Yi': 8603405, 
            'Giri, Anish': 24116068, 'Esipenko, Andrey': 24175439, 'Sindarov, Javokhir': 14205483, 'Bluebaum, Matthias': 24651516}
    players = list(openCandidates.keys())
    pgnFolder = '../resources/candidatesGames'
    ratingData = getFideRatingData(openCandidates, 2024, 'May')
    plotRatingProgression(ratingData, '2024-05')#, filename='/Users/julian/Desktop/test')
    # print(getPlayerWDL(players, pgnFolder))
    openingNames = {'Enlgish': ['English opening'], 'Italian Game': ['Two knights defence', 'Giuoco Pianissimo', 'Giuoco Piano'], 'Sicilian': ['Sicilian defence'], 'Reti': ['Reti opening']}
    # openings = getPlayerOpenings(players, pgnFolder)
    # for player, d in openings.items():
        # print(player, dict(reversed(sorted(d.items(), key=lambda x: x[1][0]))))
    # firstMoves = getWhiteFirstMoves(players, pgnFolder)
    # for player, d in firstMoves.items():
        # print(player, d)
