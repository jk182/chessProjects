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
