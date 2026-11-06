import chess
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import numpy as np


def lc0Rescale(wdl: list, wdl_rescale_ratio: float, wdl_rescale_diff: float):
    s = functions.sharpnessLC0(wdl)
    s = min(s, 5)

    W = min(max(wdl[0]/1000, 0.0001), 0.9999)
    L = min(max(wdl[2]/1000, 0.0001), 0.9999)

    a = np.log((1/W)-1)
    b = np.log((1/L)-1)

    mu = (a-b)/(a+b)

    mu_upper = mu + s * wdl_rescale_diff
    mu_lower = mu - s * wdl_rescale_diff
    s_new = np.sqrt(s) * wdl_rescale_ratio

    w_upper = 1 / (1 + np.exp((-1 + mu_upper)/s_new))
    l_upper = 1 / (1 + np.exp((-1 - mu_upper)/s_new))

    w_lower = 1 / (1 + np.exp((-1 + mu_lower)/s_new))
    l_lower = 1 / (1 + np.exp((-1 - mu_lower)/s_new))

    weight = 1 - abs(W-L)

    print(wdl, round(s, 3))
    # print(f'Previous expected score: {W-L}')
    # print(f'New expected score: {w_new-l_new}')
    print(f'Expected score shift: {abs((w_upper-l_upper) - (w_lower - l_lower))*weight}')


if __name__ == '__main__':
    wdl_rescale_ratio = 1
    wdl_rescale_diff = 0.1
    for wdl in [[333, 334, 333], [490, 20, 490], [500, 140, 360], [980, 10, 10], [10, 980, 10]]:
        lc0Rescale(wdl, wdl_rescale_ratio, wdl_rescale_diff)

    """
    for w in range(0, 1000, 50):
        for l in range(0, 1000, 50):
            if w+l < 1000:
                lc0Rescale([w, 1000-w-l, l], wdl_rescale_ratio, wdl_rescale_diff)
    """
