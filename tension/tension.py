import chess
import chess.pgn
import matplotlib.pyplot as plt


def buildGraph(board: chess.Board) -> dict():
    """
    This creates the graph of all piece interactions on the board
    """
    graph = dict()
    for square in range(64):
        if p := board.piece_at(square):
            graph[square] = [s for s in list(board.attacks(square)) if board.piece_at(s)]
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
            continue
        if node in path[:-1]:
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
            newPath = path.copy()
            newPath.append(n)
            paths.append(newPath)
    return None



def calculateBC(graph: dict, piece: int) -> float:
    """
    This function calculates the betweenes centrality for a piece given the piece interaction graph
    """
    n = len(graph)
    BC = 1/((n-1)*(n-2))
    s = 0
    for p in graph.keys():
        for q in graph.keys():
            if p != piece and q != piece:
                if paths := findShortestPaths(graph, p, q):
                    pathsThroughPiece = len([path for path in paths if piece in path])
                    s += pathsThroughPiece/len(paths)
    return BC * s


def calculateGameFragility(pgnPath: str) -> list:
    frag = list()
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            frag.append(list())
            board = game.board()
            for move in game.mainline_moves():
                board.push(move)
                graph = buildGraph(board)
                BC = 0
                for piece in range(64):
                    if board.piece_at(piece):
                        if board.attackers(not board.color_at(piece), piece):
                            BC += calculateBC(graph, piece)
                frag[-1].append(BC)
    return frag


def plotGameFragility(fragility: list()):
    fig, ax = plt.subplots(figsize=(10, 6))
    for f in fragility:
        ax.plot(range(len(f)), f)
    plt.show()


if __name__ == '__main__':
    graph = buildGraph(chess.Board('r2r2k1/1p1bb2p/p3p1p1/4p1P1/2q1P2Q/2N5/PP4BP/3R1R1K w - - 0 1'))
    print(graph)
    print(findShortestPaths(graph, 14, 28))
    print(calculateBC(graph, 14))
    g2 = buildGraph(chess.Board('6k1/8/8/8/8/3n4/2BrP3/3Q3K w - - 0 1'))
    print(findShortestPaths(g2, 3, 19))
    frag = calculateGameFragility('../resources/kasparov-topalov.pgn')
    plotGameFragility(frag)
