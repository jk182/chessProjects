import matplotlib.pyplot as plt


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


def plotPlayerBarChart(data: list, xTickLabels: list, ylabel: str, title: str, legend: list, colors: list = None, filename: str = None):
    """
    A general function to create bar charts, where each player (or group of players) gets multiple bars.
    data: list
        A list of listss. The n-th list is the data for the n-th player
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
        colors = getDefaultColors

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor(getColor('background'))
    plt.xticks(ticks=range(1, len(data)+1), labels=xTickLabels)
    ax.set_ylabel(ylabel)

    nBars = len(data[0])
    width = 0.8/nBars
    offset = width * (1/2 - nBars/2)

    for j in range(nBars):
        ax.bar([i+1+offset+(width*j) for i in range(len(data))], [d[j] for d in data], color=colors[j%len(colors)], edgecolor='black', linewidth=0.5, width=width, label=legend[j])

    ax.legend()
    plt.title(title)
    plt.axhline(0, color='black', linewidth=0.5)
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()

