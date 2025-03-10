import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt


def getRatingData(names: list, birthdays: list) -> dict:
    ratingData = dict()
    rating_index = 8
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    for i, name in enumerate(names):
        ns = name.split(',')[0]
        ratingData[ns] = list()
        r = requests.get(f'https://olimpbase.org/Elo/player/{name}.html')

        # print(r)

        soup = BeautifulSoup(r.content, 'html.parser')
        # print(soup.prettify())

        content = soup.find_all('pre')
        for row in soup.get_text().split('\n'):
            rs = row.split()
            if not rs or len(rs) <= rating_index:
                continue
            if rs[0] in months:
                if int(rs[rating_index]) < 1000:
                    if int(rs[rating_index-1]) > 1000:
                        ratingData[ns].append((int(rs[1])-birthdays[i][1]+(months.index(rs[0])-months.index(birthdays[i][0]))/12, int(rs[rating_index-1])))
                    else:
                        print('Wrong rating index')
                else:
                    ratingData[ns].append((int(rs[1])-birthdays[i][1]+(months.index(rs[0])-months.index(birthdays[i][0]))/12, int(rs[rating_index])))
    return ratingData


def getFideRatingData(fideIDs: dict) -> dict:
    ratingData = dict()
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for player, (ID, bday) in fideIDs.items():
        ratingData[player] = list()
        r = requests.get(f'https://ratings.fide.com/profile/{ID}/chart')

        soup = BeautifulSoup(r.content, 'html.parser')
        # print(soup.prettify())
        for tr in soup.find_all('tr'):
            l = [td.text.strip() for td in tr.find_all('td') if td.text.strip()]
            if l:
                if '-' in l[0]:
                    ls = l[0].split('-')
                    ratingData[player].append((int(ls[0])+months.index(ls[1])/12-bday, int(l[1])))
    return ratingData


def combineRatingData(obData: dict, fideData: dict) -> dict:
    rData = dict()
    for player, data in fideData.items():
        if player not in obData.keys():
            rData[player] = list(sorted(data))
            continue
        newData = data.copy()
        for d in obData[player]:
            if d[0] not in [nd[0] for nd in newData]:
                newData.append(d)
        newData = list(sorted(newData))
        rData[player] = newData

    for player, data in obData.items():
        if player not in rData.keys():
            rData[player] = list(sorted(data))
    return rData


def plotRatingData(ratingData: dict, title: str, filename: str = None):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('#e6f7f2')
    colors = [('#93BFCF', '#6096B4'), ('#b9e6d3', '#7ed3b2'), ('#FFC4E1', '#FF87CA'), ('#DFCCFB', '#BEADFA'), ('#EBCE95', '#F8A978'), ('#FF9F9F', '#E97777'), ('#6E7C7C', '#435560')] 

    for i, (player, data) in enumerate(ratingData.items()):
        ax.plot([d[0] for d in data], [d[1] for d in data], label=player, color=colors[i%len(colors)][1])

    ax.set_xlabel('Age')
    ax.set_ylabel('FIDE rating')
    ax.legend()
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    plt.title(title)
    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


if __name__ == '__main__':
    """
    fideIDs = {'Polgar': (700070, 1976+6/12), 'Anand': (5000017, 1969+11/12)}
    fideData = getFideRatingData(fideIDs)
    names = ['Kasparov,%20Garry', 'Polgar,%20Judit', 'Anand,%20Viswanathan', 'Dreev,%20Alexey', 'Ivanchuk,%20Vassily']
    birthdays = [('Apr', 1963), ('Jul', 1976), ('Dec', 1969), ('Jan', 1969), ('Mar', 1969)]
    names = ['Bu,%20Xiangzhi']
    birthdays = [('Dec', 1985)]
    'Bu': (8601445, 1985+11/12)
    nData = getFideRatingData(nineties)
    ratingData = getRatingData(names, birthdays)
    print(ratingData)
    compData = combineRatingData(ratingData, fideData)
    compData = combineRatingData(ratingData, nData)
    print(compData)
    plotRatingData(compData)
    """
    gen1 = {'Carlsen': (1503014, 1990+10/12), 'Karjakin': (14109603, 1990+0/12), 'Caruana': (2020009, 1992+6/12), 'Nepo': (4168119, 1990+6/12), 'Giri': (24116068, 1994+5/12), 'Ding': (8603677, 1992+9/12), 'So': (5202213, 1993+9/12)}
    gen1RatingData = getFideRatingData(gen1)
    plotRatingData(gen1RatingData, '1990-1994 Generation', filename='../out/rating90Gen.png')
    gen2 = {'Firouzja': (12573981, 2003+5/12), 'Gukesh': (46616543, 2006+4/12), 'Abdusattorov': (14204118, 2004+8/12), 'Pragg': (25059530, 2005+7/12), 'Arjun': (35009192, 2003+8/12), 'Keymer': (12940690, 2004+10/12)}
    # 'Wei Yi': (8603405, 1999+5/12)
    gen2RatingData = getFideRatingData(gen2)
    plotRatingData(gen2RatingData, '2003-2006 Generation', filename='../out/rating00Gen.png')
    gen3 = {'Gurel': (44507356, 2008+11/12), 'Erdogmus': (44599790, 2011+5/12), 'Mishra': (30920019, 2009+1/12), 'Zemlyanskii': (24249971, 2010+7/12), 'Samunenkov': (14187086, 2009+5/12), 'Oro': (20000197, 2013+9/12), 'Lu Miaoyi': (8618020, 2010+1/12)}
    gen3RatingData = getFideRatingData(gen3)
    plotRatingData(gen3RatingData, '2008-2013 Generation', filename='../out/rating10Gen.png')
