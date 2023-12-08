import pandas as pd


if __name__=='__main__':
    puzzleDB = '~/chess/resources/lichess_db_puzzle.csv'
    df = pd.read_csv(puzzleDB)
    print(df.info())
