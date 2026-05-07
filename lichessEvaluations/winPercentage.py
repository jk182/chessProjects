import chess
import chess.pgn
import io
import pandas as pd


minGameNr = 0
maxGames = 30000000
gameNr = 0
pgn = ""
timeControl = ""
whiteElo = 0
blackElo = 0
evalCutoff = 100
whiteEval = 0
timeLeft = 0
includedPlys = [20, 30, 40, 50, 60, 70, 80, 90, 100]

minRating = 1400
usedTC = '180+0'
useGame = True

data = dict()

keys = ['WhiteElo', 'BlackElo', 'TimeControl', 'Evaluation', 'Ply', 'WhiteTimeLeft', 'BlackTimeLeft', 'Result']

for key in keys:
    data[key] = list()

while gameNr < maxGames:
    try:
        line = input().strip()
    except:
        print(gameNr)
        break

    if not line:
        continue

    ls = line.split('"')

    if 'WhiteElo' in ls[0]:
        whiteElo = int(ls[1])
        if whiteElo < minRating:
            useGame = False
    elif 'BlackElo' in ls[0]:
        blackElo = int(ls[1])
        if whiteElo < minRating:
            useGame = False
    elif 'TimeControl' in ls[0]:
        timeControl = ls[1]
        if timeControl != usedTC:
            useGame = False

    if line[0] == '1':
        if not useGame:
            useGame = True
            continue

        useGame = True
        gameNr += 1
        if gameNr < minGameNr:
            continue
        if 'eval' in line:
            game = chess.pgn.read_game(io.StringIO(line))
            result = game.headers["Result"]

            node = game
            while not node.is_end():
                node = node.variations[0]

                if not node.eval() or not node.clock():
                    continue

                # if node.eval().white().score() and abs(node.eval().white().score(mate_score=10000)) >= evalCutoff and len(node.variations) > 0:
                if len(node.variations) > 0 and node.ply() in includedPlys:
                    whiteEval = node.eval().white().score(mate_score=10000)
                    nextNode = node.variations[0]
                    if nextNode.clock() is None:
                        continue
                    if node.turn():
                        whiteTimeLeft = int(node.clock())
                        blackTimeLeft = int(nextNode.clock())
                    else:
                        whiteTimeLeft = int(nextNode.clock())
                        blackTimeLeft = int(node.clock())

                    data['WhiteElo'].append(whiteElo)
                    data['BlackElo'].append(blackElo)
                    data['TimeControl'].append(timeControl)
                    data['Evaluation'].append(int(whiteEval))
                    data['Ply'].append(node.ply())
                    data['WhiteTimeLeft'].append(whiteTimeLeft)
                    data['BlackTimeLeft'].append(blackTimeLeft)
                    data['Result'].append(result)
                    if node.turn() == includedPlys[-1]:
                        break

df = pd.DataFrame(data)
outFile = '../out/lichessEvaluations2026-04.pkl'
df.to_pickle(outFile)
df = pd.read_pickle(outFile)
print(df)
