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


def plotRatingData(ratingData: dict):
    fig, ax = plt.subplots(figsize=(10, 6))

    for player, data in ratingData.items():
        ax.plot([d[0] for d in data], [d[1] for d in data], label=player)

    ax.legend()
    plt.show()


if __name__ == '__main__':
    fideIDs = {'Polgar': (700070, 1976+6/12), 'Anand': (5000017, 1969+11/12)}
    fideData = getFideRatingData(fideIDs)
    names = ['Kasparov,%20Garry', 'Polgar,%20Judit', 'Anand,%20Viswanathan', 'Dreev,%20Alexey', 'Ivanchuk,%20Vassily']
    birthdays = [('Apr', 1963), ('Jul', 1976), ('Dec', 1969), ('Jan', 1969), ('Mar', 1969)]
    names = ['Bu,%20Xiangzhi']
    birthdays = [('Dec', 1985)]
    nineties = {'Carlsen': (1503014, 1990+10/12), 'Karjakin': (14109603, 1990+0/12), 'Bu': (8601445, 1985+11/12)}
    nData = getFideRatingData(nineties)
    ratingData = getRatingData(names, birthdays)
    print(ratingData)
    compData = combineRatingData(ratingData, fideData)
    compData = combineRatingData(ratingData, nData)
    print(compData)
    plotRatingData(compData)
