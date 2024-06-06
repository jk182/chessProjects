import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
from flask import Flask, render_template_string
import plotly.graph_objects as go
import plotly.express as px
import chess
import pandas as pd
import glob
import math
import scipy.stats as stats


app = Flask(__name__)

def getAccuracyDistribution(paths: list) -> dict:
    accuracies = {'acc': list(), 'rating': list()}
    for pgnPath in paths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                if 'WhiteElo' in game.headers.keys() and 'BlackElo' in game.headers.keys():
                    wRating = int(game.headers['WhiteElo'])
                    bRating = int(game.headers['BlackElo'])
                else:
                    continue
                node = game
                cpBefore = None
                while not node.is_end():
                    node = node.variations[0]
                    acc = None
                    if not functions.readComment(node, True, True):
                        continue
                    cpAfter = functions.readComment(node, True, True)[1]
                    if not cpBefore:
                        cpBefore = cpAfter
                        continue
                    if abs(cpBefore) > 5000 and abs(cpAfter) > 5000 and cpBefore*cpAfter > 0:
                        cpBefore = cpAfter
                        continue
                    if node.turn():
                        wpB = functions.winP(cpBefore * -1)
                        wpA = functions.winP(cpAfter * -1)
                        acc = min(100, functions.accuracy(wpB, wpA))
                        if acc < 0:
                            acc = 1
                        accuracies['acc'].append(int(acc))
                        accuracies['rating'].append(bRating)
                    else:
                        wpB = functions.winP(cpBefore)
                        wpA = functions.winP(cpAfter)
                        acc = min(100, functions.accuracy(wpB, wpA))
                        if acc < 0:
                            acc = 1
                        accuracies['acc'].append(int(acc))
                        accuracies['rating'].append(wRating)
                    cpBefore = cpAfter
    return accuracies


def smoothing(data: list, width: int) -> list:
    margin = width//2
    smoothed = list()
    for i in range(margin):
        smoothed.append(data[i])
    for i,x in enumerate(data[:-width-margin]):
        j = i+margin
        smoothed.append(sum(data[j:j+width])/len(data[j:j+width]))
    for i in data[-margin:]:
        smoothed.append(i)
    return smoothed


def plotAccuracies(accuracies: dict):
    colors = ['#689bf2', '#f8a978', '#ff87ca', '#beadfa', '#A1EEBD']
    df = pd.DataFrame(accuracies)
    # fig = px.histogram(df[df['rating'].isin(range(2750, 2900))], x='acc', color='rating', log_y=True, histnorm='probability density')
    ratingBoundaries = (2000, 2400, 2500, 2600, 2700, 2900)

    candidates = getAccuracyDistribution(['../out/candidates2024-WDL+CP.pgn'])

    fig = go.Figure()
    for i in range(len(ratingBoundaries)-1):
        x1 = list(df[df['rating'].isin(range(ratingBoundaries[i], ratingBoundaries[i+1]))]['acc'])
        if i == 1:
            d = [0]*101
            for x in x1:
                d[x] += 1
            smoothed = smoothing(d, 5)
            s = [x/sum(smoothed) for x in smoothed]
            # p = stats.norm.fit(s[0:])
            fig.add_trace(go.Bar(x=list(range(1,101)), y=s, name='Smoothed', marker_color='green'))
            # fig.add_trace(go.Scatter(x=list(range(1, 101)), y=list(reversed([stats.norm.pdf(x, p[0], p[1]) for x in range(1, 101)])), mode='lines', name='lines 3'))
        x2 = [100-x for x in x1 if x>=0]
        x3 = [100-x for x in x1 if x>20]
        b, loc, scale = stats.pareto.fit(x2)
        b2, loc2, scale2 = stats.pareto.fit(x3)
        fig.add_trace(go.Histogram(x=x1, histnorm='probability density', name=f'{ratingBoundaries[i]}-{ratingBoundaries[i+1]}', marker_color=colors[i%len(colors)]))
        fig.add_trace(go.Scatter(x=list(range(1, 101)), y=list(reversed([stats.pareto.pdf(x, b, loc, scale) for x in range(1, 101)])), mode='lines', name='lines 1'))
        fig.add_trace(go.Scatter(x=list(range(1, 101)), y=list(reversed([stats.pareto.pdf(x, b2, loc2, scale2) for x in range(1, 101)])), mode='lines', name='lines 2'))
        # fig.add_trace(go.Scatter(x=list(range(1, 101)), y=list(reversed([stats.exponpow.pdf(x, g[0], g[1], g[2]) for x in range(1, 101)])), mode='lines', name='lines 2'))
    fig.update_yaxes(type="log")
    fig.update_layout(
        height=700,
        xaxis = dict(autorange="reversed"),
        barmode='overlay',
        plot_bgcolor='#e6f7f2'
    )
    fig.update_traces(opacity=0.70)
    return fig.to_html(full_html=False)


def create_plot():
    config = {'scrollZoom': True}
    data = {
            'accuracy': [94, 99, 97, 67, 90],
            'sharpness': [0.5, 0.1, 0.6, 1.2, 0.8],
            'rating': [2700, 2666, 2803, 2770, 2750]
            }
    fig = px.scatter(data, x='accuracy', y='sharpness', size='rating', title="sample figure")
    fig.update_layout(plot_bgcolor='#e6f7f2')
    return fig.to_html(full_html=False, config=config)


@app.route('/')
def home():
    # plot_html = create_plot()
    games = glob.glob('../out/games/*')
    accuracies = getAccuracyDistribution(games)
    plot_html = plotAccuracies(accuracies)
    return render_template_string('''
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <title>Interactive Plot</title>
        </head>
        <body>
            <div class="container">
                <h1 class="mt-5">Interactive Plotly Graph</h1>
                <div>{{ plot_html|safe }}</div>
            </div>
        </body>
        </html>
    ''', plot_html=plot_html)


if __name__ == '__main__':
    app.run(debug=True)
