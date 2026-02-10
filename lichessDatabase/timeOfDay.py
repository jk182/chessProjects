import chess
import chess.pgn
import io


pgn = ""
gameNr = 0
analysedGames = 0
players = dict()
blitz = None
white = None
black = None
whiteElo = 0
blackElo = 0
analysed = True

while gameNr < 10000000:
    line = input()
    if line.strip():
        # pgn = f"{pgn}{line}\n"
        if 'White ' in line:
            white = line.split('"')[1]
        elif 'Black ' in line:
            black = line.split('"')[1]
        elif 'WhiteElo' in line:
            whiteElo = int(line.split('"')[1])
        elif 'BlackElo' in line:
            blackElo = int(line.split('"')[1])
        elif 'TimeControl' in line:
            if line.split('"')[1] == '180+0':
                blitz = True
            else:
                blitz = False

        if line[0] == '1':
            if "eval" in line:
                if not (white == 'Odirovski' or black == 'Odirovski'):
                    continue
                analysed = True
                if white in players:
                    players[white] += 1
                elif whiteElo >= 2200:
                    players[white] = 1

                if black in players:
                    players[black] += 1
                elif blackElo >= 2200:
                    players[black] = 1

                # analysedGames += 1
            else:
                analysed = False

            white = None
            black = None
            whiteElo = 0
            blackElo = 0
            """
            game = chess.pgn.read_game(io.StringIO(pgn))
            if game.variations:
                node = game.variations[0]
                if node.eval():
                    for player in [game.headers["White"], game.headers["Black"]]:
                        if player not in players:
                            players[player] = 1
                        else:
                            players[player] += 1
                    analysedGames += 1
            """
            gameNr += 1
            pgn = ""


print(dict(sorted(players.items(), key=lambda item: item[1])))
# print(analysedGames, gameNr)
