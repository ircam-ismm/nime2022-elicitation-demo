import numpy as np
import tslearn
from tslearn import metrics
from joblib import Parallel, delayed

# from utils import datasets, process
import tsne_helper as te

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
tab10 = sns.color_palette('tab10')


import plotly.graph_objects as go
def plot_embedding(emb, labels):
    df = pd.DataFrame(data=emb, columns=['x', 'y'])
    fig = go.Figure()
    gs = go.Scatter(x=df['x'], y=df['y'],
                    mode='markers',
                    text=labels,
                    )
    gs.hovertemplate = "%{text}<extra></extra>"
    fig.add_trace(gs)
    fig.update_layout(showlegend=False,
                      width=400, height=400,
                     )
    fig.update_yaxes(dtick=2)
    fig.update_xaxes(dtick=2)
    fig.show()

def plot_neighbourhood_xy(neighbours, uni_short, uni_seg, labels_seg, col_wrap=5, **kwdict):

    n_lines = int(np.ceil(neighbours.shape[0] / col_wrap))
    fig, axs = plt.subplots(n_lines, col_wrap, figsize=(15, 4*n_lines))

    # get the incremental list of id for segments
    uni_seg_id = []
    acc = 0
    for sample in uni_seg:
        uni_seg_id.append(list(range(acc, acc+len(sample))))
        acc += len(sample)

    for i, neighbour in enumerate(neighbours):
        ax_id = np.unravel_index(i, (n_lines, col_wrap))
        ax = axs[ax_id]
        # list of all segments in the stroke that contains neighbour
        stroke_segs_id = [i for i in uni_seg_id if neighbour in i][0]
        # and corresponding stroke id
        stroke_id = uni_seg_id.index(stroke_segs_id)

        stroke = uni_short[stroke_id][0]
        ax.plot(stroke[:, 0], stroke[:, 1])

        seg_id = stroke_segs_id.index(neighbour)
        sample = uni_seg[stroke_id][seg_id]
        ax.plot(sample[:, 0], sample[:, 1])

        ax.set_title(labels_seg[stroke_id])
        fig.tight_layout()

def plot_neighbourhood(neighbours, uni_seg_list, labels_seg, col_wrap=5, **kwdict):

    df = pd.DataFrame()
    for i, sample_id in enumerate(neighbours):
        sample = uni_seg_list[int(sample_id)]
        tmp = pd.DataFrame(data=sample, columns=['da', 's'])
        tmp['i'] = i
        tmp['title'] = labels_seg[int(sample_id)]
        df = pd.concat([df, tmp])

    grid = sns.FacetGrid(df, col="i", col_wrap=col_wrap, **kwdict)
    grid.map(plt.plot, "da", marker="o", color=tab10[0])
    grid.map(plt.plot, "s", marker="o", color=tab10[1])

    labels = df.groupby('i').first()['title']
    for label, ax in zip(labels, grid.axes):
        ax.set_title(label)

# from torchvision.transforms import Compose

# def load_data_nofeatures(dims):
#     dt = 10
#     lc = 10
#     fs = 1.e3/dt
#     cps = Compose([process.TimeInterpolation(dt=dt),
#                            process.LowPassFilter(lc=lc, fs=fs),
#                            process.PandasToNumpy()])
#     unistroke = datasets.Unistroke("../datasets/unistroke.df",
#                           transform=cps)
#     return unistroke

# def load_data_features(dims):
#     dt = 10
#     lc = 10
#     fs = 1.e3/dt
#     cps = Compose([process.TimeInterpolation(dt=dt),
#                            process.LowPassFilter(lc=lc, fs=fs),
#                            process.FeatureExtractor(dims=dims),
#                            process.PandasToNumpy()])
#     unistroke = datasets.Unistroke("../datasets/unistroke.df",
#                           transform=cps)
#     return unistroke

def compute_similarity_matrix(data, normalise=True):
    # Inspired from code by @GillesVandewiele:
    # https://github.com/rtavenar/tslearn/pull/128#discussion_r314978479
    matrix = np.zeros((len(data), len(data)))
    indices = np.triu_indices(len(data), k=1, m=len(data))
    matrix[indices] = Parallel(n_jobs=8, prefer="processes", verbose=0)(
                               delayed(metrics.dtw)(data[i], data[j],)
                               for i, j in zip(*indices))
    sm = matrix + matrix.T
    if normalise:
        sm = sm / sm.max()
    return sm

def tsne_embed(sm, perplexity=10):
    af = te.compute_affinity(sm, perplexity=perplexity)
    emb = te.embed(af)
    return emb


## this did not work too well...
# # linkage
# import scipy.spatial as scspa
# sq = scspa.distance.squareform(dm)
# import scipy.cluster as scclu
# z = scclu.hierarchy.linkage(sq)
# plt.hist(scclu.hierarchy.fcluster(z, criterion='maxclust', t=100))
# %%time
# fig, ax = plt.subplots(figsize=(16, 16))
# _=scclu.hierarchy.dendrogram(z)