from dash import dcc, html
from dash import callback
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

import dash_bootstrap_components as dbc

################################################################################
# LAYOUT
layout = [
    # embedding
    html.Button('Embed', id='button-embed', n_clicks=0),
    # dbc.Progress(id='progress-bar-embed', value=25),
    dbc.Progress(id='progress', value=25),
    dcc.Interval(id="progress-interval", n_intervals=0, interval=500),
    ]

@callback(
    [Output("progress", "value"), Output("progress", "label")],
    [Input("progress-interval", "n_intervals")],
)
def update_progress(n):
    # check progress of some background process, in this example we'll just
    # use n_intervals constrained to be in 0-100
    progress = min(n % 110, 100)
    # only add text after 5% progress to ensure text isn't squashed too much
    return progress, f"{progress} %" if progress >= 5 else ""


# @callback(
#     Output('progress-bar-embed', 'value'),
#     Input('button-embed', 'n_clicks'),
#     )
# def update_progress_bar(n_clicks):

#     print('update_progress_bar', n_clicks)
#     if n_clicks == 0:
#         raise PreventUpdate()

#     print("start embedding.")
#     return n_clicks

# # import dash_bootstrap_components as dbc
# # from dash import Input, Output, dcc, html

# layout = html.Div(
#     [
#         dbc.Progress(id="progress"),
#     ]
# )


import numpy as np
from joblib import Parallel, delayed

# # https://stackoverflow.com/questions/24983493/tracking-progress-of-joblib-parallel-execution
# import contextlib
# import joblib
# from tqdm import tqdm

# @contextlib.contextmanager
# def tqdm_joblib(tqdm_object):
#     """Context manager to patch joblib to report into tqdm progress bar given as argument"""
#     class TqdmBatchCompletionCallback(joblib.parallel.BatchCompletionCallBack):
#         def __call__(self, *args, **kwargs):
#             tqdm_object.update(n=self.batch_size)
#             return super().__call__(*args, **kwargs)

#     old_batch_callback = joblib.parallel.BatchCompletionCallBack
#     joblib.parallel.BatchCompletionCallBack = TqdmBatchCompletionCallback
#     try:
#         yield tqdm_object
#     finally:
#         joblib.parallel.BatchCompletionCallBack = old_batch_callback
#         tqdm_object.close()

# from joblib import Parallel, delayed

# with tqdm_joblib(tqdm(desc="My calculation", total=10)) as progress_bar:
#     Parallel(n_jobs=16)(delayed(sqrt)(i**2) for i in range(10))


def compute_similarity_matrix(data, normalise=True):
    # Inspired from code by @GillesVandewiele:
    # https://github.com/rtavenar/tslearn/pull/128#discussion_r314978479
    matrix = np.zeros((len(data), len(data)))
    indices = np.triu_indices(len(data), k=1, m=len(data))
    matrix[indices] = Parallel(n_jobs=8, prefer="processes", verbose=1)(
                               delayed(metrics.dtw)(data[i], data[j],)
                               for i, j in zip(*indices))
    sm = matrix + matrix.T
    if normalise:
        sm = sm / sm.max()
    return sm

# def tsne_embed(sm, perplexity=10):
#     af = te.compute_affinity(sm, perplexity=perplexity)
#     emb = te.embed(af)
#     return emb
