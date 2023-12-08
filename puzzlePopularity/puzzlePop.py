import pandas as pd


if __name__=='__main__':
    puzzleDB = '~/chess/resources/lichess_db_puzzle_100k.csv'
    df = pd.read_csv(puzzleDB)
    df = df.sort_values('Popularity', ascending=False)
    pd.set_option('display.max_columns', None)
    print(df.info())
    print(df)
