import chess
import chess.pgn
import io
import pandas as pd


maxGames = 100000
gameNr = 0
pgn = ""
timeControl = ""
whiteElo = 0
blackElo = 0
evalCutoff = 100
whiteEval = 0
timeLeft = 0

data = dict()

keys = ['WhiteElo', 'BlackElo', 'TimeControl', 'FirstEvalAdvantage', 'Ply', 'WhiteTimeLeft', 'BlackTimeLeft', 'Result']

for key in keys:
    data[key] = list()

while gameNr < maxGames:
    line = input().strip()
    if not line:
        continue

    if 'WhiteElo' in line:
        whiteElo = int(line.split('"')[1])
    elif 'BlackElo' in line:
        blackElo = int(line.split('"')[1])
    elif 'TimeControl' in line:
        timeControl = line.split('"')[1]

    if line[0] == '1':
        gameNr += 1
        if 'eval' in line:
            game = chess.pgn.read_game(io.StringIO(line))
            result = game.headers["Result"]

            node = game
            while not node.is_end():
                node = node.variations[0]

                if not node.eval():
                    continue
                if node.eval().white().score() and abs(node.eval().white().score(mate_score=10000)) >= evalCutoff and len(node.variations) > 0:
                    whiteEval = node.eval().white().score()
                    nextNode = node.variations[0]
                    if node.clock() is None or nextNode.clock() is None:
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
                    data['FirstEvalAdvantage'].append(whiteEval)
                    data['Ply'].append(node.ply())
                    data['WhiteTimeLeft'].append(whiteTimeLeft)
                    data['BlackTimeLeft'].append(blackTimeLeft)
                    data['Result'].append(result)
                    break

df = pd.DataFrame(data)
print(df)
