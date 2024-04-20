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


def insert(connection, position: str, nodes: int = None, w: int = None, d: int = None, l: int = None, depth: int = None, cp: float = None, mate: int = None, pv: str = None):
    cursor = con.cursor()
    cursor.execute(f'INSERT INTO eval VALUES ("{position}", "{nodes}", "{w}", "{d}", "{l}", "{depth}", "{cp}", "{mate}", "{pv}")')
    connection.commit()


if __name__ == '__main__':
    DBname = 'evaluation.db'
    con = sqlite3.connect(DBname)
    cur = con.cursor()
    # cur.execute("DROP TABLE IF EXISTS eval")
    # createTable(DBname)
    print(cur.execute("SELECT name FROM sqlite_master").fetchone())
    insert(con, 'test', 5, 200, 1000, 700)
    print(cur.execute('SELECT * FROM eval').fetchall())
