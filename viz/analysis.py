
import logging

import pandas as pd

from dash_extensions.enrich import Output, Input, State
from dash_extensions.enrich import html, dcc
from dash_extensions.enrich import DashProxy, ServersideOutput, ServersideOutputTransform
from dash_extensions.enrich import callback
from dash.exceptions import PreventUpdate
import dash

import plotly.graph_objs as go
import plotly.express as px

from utils import format_from_json, format_from_df
import embedding


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
                dcc.Graph(id="fig_embedding",),
            ],
            style={'width': '49%', 'display': 'inline-block'},
        ),

        html.Div([
                dcc.Graph(id="fig_strokes",),
            ],
            style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'},
        ),


        html.Div(id='tmp'),

        ],

        style= {'display': 'block'}
        )
    ]



################################################################################
# CALLBACKS

@callback(
    ServersideOutput('data-store-embedding', 'data'),
    Input('button_id', 'n_clicks'),
    State('data-store-file', 'data'),
    prevent_initial_call=True,
)
def embed_long_callback(n_clicks, df):

    segments = [grp[['s', 'da']].values for i, grp in df.groupby('segment_id')]

    logging.info("cluster start")
    sm = embedding.compute_similarity_matrix(segments)
    logging.info("cluster done")

    logging.info("embed start")
    emb = embedding.tsne_embed(sm, perplexity=30)
    logging.info("embed done")

    emb = pd.DataFrame(emb, columns=['x', 'y'])

    return emb


@callback(
    Output('fig_embedding', 'figure'),
    Input('data-store-embedding', 'data'),
    prevent_initial_call=True,
    )
def create_fig_embedding(df):

    fig = px.scatter(x=df['x'], y=df['y'])

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
    # return json.dumps(selected)

