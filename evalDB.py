import sqlite3
import functions
import chess
import json
import pandas as pd

def createTable(name: str):
    """
    This function creates the table for the evaaluation database
    name: str
        The filename of the database
    """
    con = sqlite3.connect(name)
    cur = con.cursor()
    cur.execute("""CREATE TABLE eval(
            position VARCHAR(255), 
            nodes INT, 
            w INT, 
            d INT, 
            l INT, 
            depth INT, 
            cp INT, 
            mate INT, 
            pv VARCHAR(255),
            PRIMARY KEY (position)
            )""")


def insert(position: str, nodes: int = -1, w: int = None, d: int = None, l: int = None, depth: int = -1, cp: float = None, mate: int = None, pv: str = None):
    """
    Inserting data into the table.
    Default values of nodes and depth are -1, if there is only an evaluation by LC0 or SF and not by both.
    """
    con = sqlite3.connect('../out/evaluation.db')
    cursor = con.cursor()
    cursor.execute(f'INSERT INTO eval VALUES ("{position}", "{nodes}", "{w}", "{d}", "{l}", "{depth}", "{cp}", "{mate}", "{pv}")')
    con.commit()


def update(position: str, nodes: int = -1, w: int = None, d: int = None, l: int = None, depth: int = -1, cp: float = None, mate: int = None, pv: str = None):
    con = sqlite3.connect('../out/evaluation.db')
    cur = con.cursor()
    # TODO: update for CP
    cur.execute(f'UPDATE eval SET nodes={nodes}, w={w}, d={d}, l={l} WHERE position="{position}"')
    con.commit()


def getEval(position: str):
    con = sqlite3.connect('../out/evaluation.db')
    cur = con.cursor()
    if not contains(position):
        return None
    query = cur.execute(f'SELECT w,d,l,nodes,cp,depth FROM eval WHERE position="{position}"').fetchall()[0]
    return {'cp': query[4], 'depth': query[5], 'wdl': [query[0], query[1], query[2]], 'nodes': query[3]}


def contains(position: str) -> bool:
    con = sqlite3.connect('../out/evaluation.db')
    cur = con.cursor()
    if cur.execute(f'SELECT 1 FROM eval WHERE position="{position}"').fetchall():
        return True
    return False


def importFromPGN(pgnPath: str, nodes: int = None, depth: int = None):
    with open(pgnPath, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            print('Test')
            node = game
            while not node.is_end():
                node = node.variations[0]
                fen = node.board().fen()
                if nodes and depth:
                    if functions.readComment(node, True, True):
                        wdl, cp = functions.readComment(node, True, True)
                        update(fen, nodes, wdl[0], wdl[1], wdl[2], depth, cp)
                elif nodes:
                    wdl = functions.readComment(node, True, False)
                    update(fen, nodes, wdl[0], wdl[1], wdl[2])
                elif depth:
                    cp = functions.readComment(node, False, True)
                    update(fen, depth=depth, cp=cp)


def importFromLichessDB(lichessDB: str):
    evalDB = pd.read_json(lichessDB, lines=True)
    for i, row in evalDB.iterrows():
        if i % 100000 == 0:
            print(i)
        if not contains(row['fen']):
            evals = row['evals']
            if 'cp' in evals[0]['pvs'][0].keys():
                cp = evals[0]['pvs'][0]['cp']
                pv = evals[0]['pvs'][0]['line']
                # print(evals)
                # print(row['fen'], cp, evals[0]['depth'], pv)
                insert(position=row['fen'], cp=cp, depth=evals[0]['depth'], pv=pv)


if __name__ == '__main__':
    """
    DBname = '../out/evaluation.db'
    con = sqlite3.connect(DBname)
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS eval")
    createTable(DBname)
    con2 = sqlite3.connect('../out/evaluation_backup.db')
    cur2 = con2.cursor()
    for entry in cur2.execute("SELECT * FROM eval").fetchall():
        fen = functions.modifyFEN(entry[0])
        if not contains(fen):
            insert(fen, entry[1], entry[2], entry[3], entry[4], entry[5], entry[6], entry[7], entry[8])
    """
    # print(cur.execute("SELECT name FROM sqlite_master").fetchone())
    # con.close()
    # importFromPGN('out/candidates2024-WDL+CP.pgn', 5000, 35)
    # con = sqlite3.connect(DBname)
    # cur = con.cursor()
    # print(cur.execute("SELECT * FROM eval").fetchall()[-100:])
    for i in range(7, 10):
        print(i)
        importFromLichessDB(f'../resources/lichess_db_eval_1000000_{i}.json')
    """
    insert('test2', depth=5, cp=0.4, w=2, d=1, l=3)
    print(contains('test2'))
    print(contains('test'))
    print(cur.execute('SELECT * FROM eval').fetchall())
    print(getEval('test2', True))
    print(getEval('test2', False))
    """
