import chess


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
    if end in graph[start]:
        return [[end]]
    paths = [[n] for n in graph[start]]
    retPaths = list()
    while paths:
        path = paths.pop(0)
        node = path[-1]
        if node not in graph.keys():
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
    BC = 0


if __name__ == '__main__':
    graph = buildGraph(chess.Board('r2r2k1/1p1bb2p/p3p1p1/4p1P1/2q1P2Q/2N5/PP4BP/3R1R1K w - - 0 1'))
    print(graph)
    print(findShortestPaths(graph, 14, 28))
