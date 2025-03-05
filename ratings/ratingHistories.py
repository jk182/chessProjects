import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt


def getRatingData() -> dict:
    names = ['Kasparov,%20Garry', 'Polgar,%20Judit', 'Anand,%20Viswanathan', 'Dreev,%20Alexey']
    birthdays = [('Apr', 1963), ('Jul', 1976), ('Dec', 1969), ('Jan', 1969)]
    ratingData = dict()

    for i, name in enumerate(names):
        print(name)
        ns = name.split(',')[0]
        ratingData[ns] = list()
        r = requests.get(f'https://olimpbase.org/Elo/player/{name}.html')

        # print(r)

        soup = BeautifulSoup(r.content, 'html.parser')
        # print(soup.prettify())

        rating_index = 8
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        content = soup.find_all('pre')
        for row in soup.get_text().split('\n'):
            rs = row.split()
            if not rs or len(rs) <= rating_index:
                continue
            if rs[0] in months:
                if int(rs[rating_index]) < 1000:
                    print('Wrong rating index')
                else:
                    ratingData[ns].append((int(rs[1])-birthdays[i][1]+(months.index(rs[0])-months.index(birthdays[i][0]))/12, int(rs[rating_index])))
    return ratingData


def plotRatingData(ratingData: dict):
    fig, ax = plt.subplots(figsize=(10, 6))

    for player, data in ratingData.items():
        ax.plot([d[0] for d in data], [d[1] for d in data], label=player)

    ax.legend()
    plt.show()


if __name__ == '__main__':
    ratingData = getRatingData()
    print(ratingData)
    plotRatingData(ratingData)
