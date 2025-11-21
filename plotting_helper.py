import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def getAllColors() -> dict:
    """
    This returns a dictionary with the colors mostly used for the posts
    """
    colors = dict()
    colors['background'] = '#e6f7f2'
    colors['orange'] = '#f8a978'
    colors['blue'] = '#689bf2'
    colors['red'] = '#fa5a5a'
    colors['green'] = '#5afa8d'
    colors['teal'] = '#7ed3b2'
    colors['pink'] = '#ff87ca'
    colors['purple'] = '#beadfa'
    colors['lightred'] = '#FD8A8A'
    colors['violet'] = '#85586F'
    colors['yellow'] = '#f7cf77'
    colors['grey'] = '#758A93'
    colors['darkgreen'] = '#5D866C'

    colors['much better'] = '#4ba35a'
    colors['slightly better'] = '#9cf196'
    colors['equal'] = '#f0ebe3'
    colors['slightly worse'] = '#f69e7b'
    colors['much worse'] = '#ef4b4b'
    
    return colors


def getColor(name: str) -> str:
    """
    This returns the color of the given name
    """
    colors = getAllColors()
    if name not in colors.keys():
        return None

    return colors[name]


def getColors(names: list) -> list:
    """
    This returns the colors for a given list of names
    """
    colorsDict = getAllColors()
    colors = list()

    for name in names:
        if name in colorsDict.keys():
            colors.append(colorsDict[name])
    return colors


def getDefaultColors() -> list:
    """
    This returns a list of default colors
    """
    return getColors(['blue', 'orange', 'green', 'red', 'purple'])


def plotPlayerBarChart(data: list, xTickLabels: list, ylabel: str, title: str, legend: list, colors: list = None, xlabel: str = None, filename: str = None):
    """
    A general function to create bar charts, where each player (or group of players) gets multiple bars.
    data: list
        A list of lists. The n-th list is the data for the n-th player
    xTickLabels: list
        The labels for the x-ticks. Usually the player names
    ylabel: str
        Label of the y-axis
    title: str
        The title for the plot
    legend: list
        The name for each bar to show in the legend
    colors: list
        The colors used for the bars.
        If no value is given, a default value will be chosen
    filename: str
        The name to save the plot to.
        If no name is given, the plot will be shown instead of saved.
    """
    if not colors:
        colors = getDefaultColors()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor(getColor('background'))
    plt.xticks(ticks=range(1, len(data)+1), labels=xTickLabels)
    if xlabel:
        ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    nBars = len(data[0])
    width = 0.8/nBars
    offset = width * (1/2 - nBars/2)

    yMax = 0
    for j in range(nBars):
        ax.bar([i+1+offset+(width*j) for i in range(len(data))], [d[j] for d in data], color=colors[j%len(colors)], edgecolor='black', linewidth=0.5, width=width, label=legend[j])
        yMax = max(yMax, max([d[j] for d in data]))

    ax.legend()
    ax.set_ylim(0, yMax * 1.05)
    plt.title(title)
    plt.axhline(0, color='black', linewidth=0.5)
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def plotLineChart(data: list, xLabel: str, yLabel: str, title: str, legend: list, colors: list = None, hlineHeight: float = None, xTicks: list = None, filename: str = None):
    """
    A general function to create line charts.
    data: list
        A list of lists, each list contains the data for one category
    xLabel, yLabel:
        Labels for the axes
    title: str
        Title of the plot
    legend: list
        Legend for each of the data lists
    colors: list
        Colors to be used of the lines.
        If no value is given, a default color palette will be chosen.
    filename: str
        Then path to save the plot.
        If no name is given, the plot will be shown instead of saved.
    """
    if not colors:
        colors = getDefaultColors()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor(getColor('background'))
    ax.set_xlabel(xLabel)
    ax.set_ylabel(yLabel)

    xMin = 0
    xMax = 0
    yMin = 100
    yMax = -100

    for i, d in enumerate(data):
        # ax.plot([(j+1)/2 for j in range(len(d))], d, color=colors[i%len(colors)], label=legend[i])
        ax.plot([j+1 for j in range(len(d))], d, color=colors[i%len(colors)], label=legend[i], linewidth=1.5)
        xMax = max(xMax, len(d)//2)
        yMin = min(yMin, min(d))
        yMax = max(yMax, max(d))

    yMin = min(0.5, yMin-0.01)
    ax.legend()
    # ax.set_xlim(xMin, xMax)
    # ax.set_ylim(yMin-0.5, yMax+0.5)
    ax.set_ylim(yMin, 1)
    if xTicks is not None:
        ax.set_xlim(1, len(data[-1]))
        # ax.set_xticks([j+1 for j in range(len(data[-1]))])
        # ax.set_xticklabels(xTicks)
        ax.xaxis.set_major_locator(ticker.LinearLocator(11))
        ax.xaxis.set_minor_locator(ticker.LinearLocator(21))
        ax.set_xticklabels([f'+{t/100}' for t in xTicks if t%100 == 0])
    plt.title(title)
    if hlineHeight is not None:
        plt.axhline(hlineHeight, color='black', linewidth=0.5)
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.07, right=0.95)

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def plotAvgLinePlot(data: list, playerNames: list, ylabel: str, title: str, legend: list, colors: list = None, maxMoves: int = 39, filename: str = None):
    """
    This function plots the average values of move data
    """
    if not colors:
        colors = ['#689bf2', '#5afa8d', '#f8a978', '#fa5a5a']

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('#e6f7f2')
    
    yMin = 0
    yMax = 0
    for k, d in enumerate(data):
        avg = list()
        for i in range(maxMoves):
            l = [c[i] for c in d if len(c) > i]
            avg.append(sum(l)/len(l))
        ax.plot(range(1, maxMoves+1), avg, color=colors[k], label=legend[k])
        yMin = min(yMin, min(avg))
        yMax = max(yMax, max(avg))
    
    plt.xlim(1, maxMoves)
    plt.ylim(yMin*1.05, yMax*1.05)
    ax.set_xlabel('Move Number')
    ax.set_ylabel(ylabel)
    ax.legend()
    plt.title(title)
    plt.axhline(0, color='black', linewidth=0.5)
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()

