import chess
import chess.pgn
import matplotlib.pyplot as plt
import pandas as pd

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions

def buildGraph(board: chess.Board, orphans: bool = True) -> dict():
    """
    This creates the graph of all piece interactions on the board
    """
    graph = dict()
    for square in range(64):
        if board.piece_at(square):
            # if board.is_attacked_by(chess.WHITE, square) or board.is_attacked_by(chess.BLACK, square):
            v = [s for s in list(board.attacks(square)) if board.piece_at(s) and not board.is_pinned(board.turn, square)]
            if orphans:
                graph[square] = v
            elif v:
                graph[square] = v
            """
            if attacks := [s for s in list(board.attacks(square)) if board.piece_at(s)]:
                graph[square] = attacks
            """
    return graph


def findShortestPaths(graph: dict, start: int, end: int) -> list:
    if start not in graph.keys() or end not in graph.keys():
        return None
    if start == end:
        return None
    if end in graph[start]:
        return [[start, end]]
    paths = [[start, n] for n in graph[start]]
    retPaths = list()
    while paths:
        path = paths.pop(0)
        node = path[-1]
        if node not in graph.keys():
            # print("Piece not found")
            continue
        neighbors = graph[node]
        if end in neighbors:
            path.append(end)
            retPaths.append(path)
            for p in paths:
                if len(p) == len(path)-1 and (np := p[-1]) in graph.keys():
                    if end in graph[np]:
                        p.append(end)
                        retPaths.append(p)
            return retPaths
        for n in neighbors:
            if n not in path:
                newPath = path.copy()
                newPath.append(n)
                paths.append(newPath)
    return None


def calculateBC(graph: dict, piece: int) -> float:
    """
    This function calculates the betweenes centrality for a piece given the piece interaction graph
    """
    n = len(graph)
    norm = 1/((n-1)*(n-2))
    s = 0
    for p in graph.keys():
        for q in graph.keys():
            if p != piece and q != piece and p != q:
                if paths := findShortestPaths(graph, p, q):
                    pathsThroughPiece = len([path for path in paths if piece in path])
                    s += pathsThroughPiece/len(paths)
                    # print(p, q, paths)
                    # if pathsThroughPiece > 0:
                        # print(piece, paths, s)
    return norm * s


def calculateBoardFragility(board: chess.Board) -> float:
    graph = buildGraph(board, False)
    if len(graph) <= 2:
        return 0
    fragility = 0
    for piece in range(64):
        if board.piece_at(piece):
            for attacker in board.attackers(not board.color_at(piece), piece):
                fragility += calculateBC(graph, piece)
                break
    return fragility


def calculateGameFragility(pgnPath: str) -> list:
    frag = list()
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            frag.append(list())
            board = game.board()
            for move in game.mainline_moves():
                board.push(move)
                graph = buildGraph(board, True)
                newGraph = dict()
                for k, v in graph.items():
                    if v:
                        newGraph[k] = v
                    else:
                        for nv in graph.values():
                            if k in nv:
                                newGraph[k] = v
                                break
                BC = 0
                for piece in range(64):
                    if board.piece_at(piece):
                        for attacker in board.attackers(not board.color_at(piece), piece):
                            # if not board.is_pinned(not board.color_at(piece), attacker):
                            BC += calculateBC(newGraph, piece)
                            break
                frag[-1].append(BC)
    return frag


def plotGameFragility(fragility: list()):
    fig, ax = plt.subplots(figsize=(10, 6))
    for f in fragility:
        ax.plot(range(len(f)), f)
    plt.show()


def getEvalChange(pgnPaths: list) -> list:
    changes = list()
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                maxSharp = 0
                cpB = None
                node = game

                while not node.is_end():
                    if not functions.readComment(node, True, True):
                        node = node.variations[0]
                        continue
                    comment = functions.readComment(node, True, True)
                    node = node.variations[0]
                    if not functions.readComment(node, True, True):
                        continue
                    cpA = functions.readComment(node, True, True)[1]
                    sharp = functions.sharpnessLC0(comment[0])
                    cpB = comment[1]
                    if sharp > maxSharp:
                        cps = (cpB, cpA)
                changes.append(cps)
    return changes


def getTensionCPLoss(gameData: pd.DataFrame) -> list:
    tensionCP = list()
    minMove = 15
    for i, row in gameData.iterrows():
        if i > 5000:
            break
        if row["MoveNr"] >= minMove:
            if row["Color"]:
                cpLoss = row["EvalBefore"] - row["EvalAfter"]
            else:
                cpLoss = -row["EvalBefore"] + row["EvalAfter"]
            fragility = calculateBoardFragility(chess.Board(row["Position"]))
            cpLoss = max(0, cpLoss)
            tensionCP.append((fragility, cpLoss))
    return tensionCP


def plotTensionCPLoss(tensionCP: list):
    tension = [t[0] for t in tensionCP]
    CP = [t[1] for t in tensionCP]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(tension, CP)
    ax.set_xlabel('Fragility')
    ax.set_ylabel('CP Loss')
    plt.show()


if __name__ == '__main__':
    board = chess.Board('1bq1r1k1/1p3pp1/1P2b1n1/p1p1p2p/P1PNP1P1/4BP1P/2Q3B1/3R1RK1 b - - 0 25')
    board = chess.Board('1k3b2/4B2K/5r2/8/8/R7/8/8 w - - 0 1')
    graph = buildGraph(board, True)
    print(graph)
    newGraph = dict()
    for k, v in graph.items():
        if v:
            newGraph[k] = v
        else:
            for nv in graph.values():
                if k in nv:
                    newGraph[k] = v
                    break
    print(newGraph)
    print(calculateBC(newGraph, 52))
    df = pd.read_pickle('../out/gameDF')
    # tcp = getTensionCPLoss(df)
    # plotTensionCPLoss(tcp)
    # print(findShortestPaths(graph, 14, 28))
    """
    BC = 0
    for piece in range(64):
        if board.piece_at(piece):
            for attacker in board.attackers(not board.color_at(piece), piece):
                if not board.is_pinned(not board.color_at(piece), attacker):
                    BC += calculateBC(graph, piece)
                    break
    print(BC)
    """
    # frag = calculateGameFragility('../resources/kasparov-topalov.pgn')
    frag = calculateGameFragility('../resources/tension.pgn')
    plotGameFragility(frag)
    # print(getEvalChange(['../out/games/wijkMasters2025.pgn']))
