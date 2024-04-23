import sqlite3

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
            cp FLOAT, 
            mate INT, 
            pv VARCHAR(255),
            PRIMARY KEY (position)
            )""")


def insert(position: str, nodes: int = -1, w: int = None, d: int = -1, l: int = None, depth: int = None, cp: float = None, mate: int = None, pv: str = None):
    """
    Inserting data into the table.
    Default values of nodes and depth are -1, if there is only an evaluation by LC0 or SF and not by both.
    """
    con = sqlite3.connect('evaluation.db')
    cursor = con.cursor()
    cursor.execute(f'INSERT INTO eval VALUES ("{position}", "{nodes}", "{w}", "{d}", "{l}", "{depth}", "{cp}", "{mate}", "{pv}")')
    con.commit()


def update(position: str, nodes: int = -1, w: int = None, d: int = -1, l: int = None, depth: int = None, cp: float = None, mate: int = None, pv: str = None):
    con = sqlite3.connect('evaluation.db')
    cur = con.cursor()
    nd = cur.execute(f'SELECT nodes, depth FROM eval WHERE position="{position}"')
    # TODO: check if position is in DB and nodes or depth are higher than before, then update
    print(nd.fetchall())


def getEval(position: str, wdl: bool):
    con = sqlite3.connect('evaluation.db')
    cur = con.cursor()
    if wdl:
        return list(cur.execute(f'SELECT w,d,l FROM eval WHERE position="{position}"').fetchall()[0])
    return cur.execute(f'SELECT cp FROM eval WHERE position="{position}"').fetchall()[0][0]


def contains(position: str) -> bool:
    con = sqlite3.connect('evaluation.db')
    cur = con.cursor()
    if cur.execute(f'SELECT 1 FROM eval WHERE position="{position}"').fetchall():
        return True
    return False


if __name__ == '__main__':
    DBname = 'evaluation.db'
    con = sqlite3.connect(DBname)
    cur = con.cursor()
    # cur.execute("DROP TABLE IF EXISTS eval")
    createTable(DBname)
    # print(cur.execute("SELECT name FROM sqlite_master").fetchone())
    """
    insert('test2', depth=5, cp=0.4, w=2, d=1, l=3)
    print(contains('test2'))
    print(contains('test'))
    print(cur.execute('SELECT * FROM eval').fetchall())
    print(getEval('test2', True))
    print(getEval('test2', False))
    """