import pandas as pd


if __name__=='__main__':
    puzzleDB = '~/chess/resources/lichess_db_puzzle_100k.csv'
    df = pd.read_csv(puzzleDB)
    # df = df.sort_values('Popularity', ascending=False)
    pd.set_option('display.max_columns', None)

    plays = 1000
    ndf = df[df['NbPlays'] >= plays]
    ndf = ndf.reset_index()
    ndf['Solution Length'] = [len(sol.split(' ')) for sol in ndf['Moves']]
    for i in ndf.index:
        print(ndf['FEN'][i], ndf['Moves'][i])
    print(ndf.sort_values('Solution Length'))
    print(ndf['Popularity'].corr(ndf['Rating']))
    print(ndf['NbPlays'].corr(ndf['Rating']))
    print(ndf['Popularity'].corr(ndf['Solution Length']))
