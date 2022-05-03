from dash import dcc, html
from dash import callback
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import dash_bootstrap_components as dbc

from utils import format_from_json, format_from_df

import plotly.graph_objs as go
import plotly.express as px

################################################################################
# LAYOUT
layout = [
    html.Div(id='analysis-layout', children=[


        html.Div([
            html.Div(id='progress'),
            html.Button(id='button_id', children='Run Job!'),
        ],
        style={'width': '100%', 'display': 'inline-block'}
        ),

        html.Div([
            # dbc.Col([
                dcc.Graph(id="fig_embedding",),
                # ]),
            ],
            style={'width': '49%', 'display': 'inline-block'},
        ),

        html.Div([
            # dbc.Col([
                dcc.Graph(id="fig_strokes",),
                # dcc.Graph(id="fig_speed",),
                # ]),
            ],
            style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'},
        ),


        html.Div(id='tmp'),

        ],

        style= {'display': 'block'}
        )
    ]




import logging

import embedding
from dash.exceptions import PreventUpdate

import time
@callback(
    output=Output('data-store-embedding', 'data'),
    inputs=[
        Input('button_id', 'n_clicks'),
        State('data-store-file', 'data')
        ],
    # running=[
    #     (Output('button_id', 'disabled'), True, False),
    #     ],
)
def embed_long_callback(n_clicks, jsonified_cleaned_data):
    print('embed_long_callback', n_clicks, jsonified_cleaned_data==None)

    if jsonified_cleaned_data == None:
        return None

    df = format_from_json(jsonified_cleaned_data)
    segments = [grp[['s', 'da']].values for i, grp in df.groupby('segment_id')]

    logging.info("cluster start")
    sm_seg = embedding.compute_similarity_matrix(segments)
    logging.info("cluster done")

    logging.info("embed start")
    emb_seg = embedding.tsne_embed(sm_seg, perplexity=30)
    logging.info("embed done")

    embed_json = pd.DataFrame(emb_seg).to_json(date_format='iso', orient='split')

    return embed_json


import pandas as pd

@callback(
    Output('fig_embedding', 'figure'),
    Input('data-store-embedding', 'data'),
    )
def create_fig_embedding(json):

    if json == None:
        return go.Figure()

    df = pd.read_json(json, orient='split')
    print('create_fig_embedding', df.values)

    fig = px.scatter(x=df.values[:, 0], y=df.values[:, 1])

    fig = go.Figure(data=fig.data)
    fig.layout.update(showlegend=False,
                      autosize=False,
                      width=1000,
                      height=1000,)

    print(fig)

    return fig


import json

@callback(
    Output('tmp', 'children'),
    Input('fig_embedding', 'selectedData'),
    )
def cb(selected):
    print(selected)
    return json.dumps(data)



# if __name__ == "__main__":
#     app.run_server(debug=True)

# from flask_caching import Cache

# Create a server side resource.
# fsc = FileSystemCache("cache_dir")
# fsc.set("progress", None)




# @callback(
#     Output("progress", "value"), Output("progress", "label"),
#     Input('button-embed', 'n_clicks'),
#     # [Input("progress-interval", "n_intervals")],
# )
# def update_progress(n):
#     # check progress of some background process, in this example we'll just
#     # use n_intervals constrained to be in 0-100
#     progress = min(n % 110, 100)
#     # only add text after 5% progress to ensure text isn't squashed too much
#     return progress, f"{progress} %" if progress >= 5 else ""


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
