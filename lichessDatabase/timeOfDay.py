import chess
import chess.pgn
import io


pgn = ""
gameNr = 0
analysedGames = 0
players = dict()
while gameNr < 1000000000:
    line = input()
    if line.strip():
        pgn = f"{pgn}{line}\n"
        if line[0] == '1':
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
            gameNr += 1
            pgn = ""

print(dict(sorted(players.items(), key=lambda item: item[1])))
print(analysedGames, gameNr)
