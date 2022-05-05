
import logging

import numpy as np
import pandas as pd

from dash_extensions.enrich import Output, Input, State
from dash_extensions.enrich import html, dcc
from dash_extensions.enrich import DashProxy, ServersideOutput, ServersideOutputTransform
from dash_extensions.enrich import callback
from dash.exceptions import PreventUpdate
import dash

import plotly.graph_objs as go
import plotly.express as px

from utils import format_from_json, format_from_df, select
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
                # dcc.Dropdown(['NYC', 'MTL', 'SF'], 'NYC', id='fig-embedding-options'),
                dcc.Graph(id='fig-embedding',),
            ],
            style={'width': '49%', 'display': 'inline-block'},
        ),
        html.Div([
                dcc.Graph(id='fig_selected',),
            ],
            style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'},
        ),

        ],
        style= {'display': 'block'}
        )
    ]


################################################################################
# CALLBACKS
@callback(
    ServersideOutput('data-store-embedding', 'data', session_check=False, arg_check=False),
    Input('button_id', 'n_clicks'),
    State('data-store-file', 'data'),
    prevent_initial_call=True,
    memoize=True,
)
def cb(n_clicks, df):
    """Compute a DTW-TSNE embedding from individual segments.
    """
    segments = [grp[['s', 'da']].values for i, grp in df.groupby('segment_id')]

    logging.info('cluster start')
    sm = embedding.compute_similarity_matrix(segments)
    logging.info('cluster done')

    logging.info('embed start')
    emb = embedding.tsne_embed(sm, perplexity=30)
    logging.info('embed done')

    emb = pd.DataFrame(emb, columns=['x', 'y'])

    return emb


@callback(
    Output('fig-embedding', 'figure'),
    Input('data-store-embedding', 'data'),
    prevent_initial_call=True,
    )
def cb(df):
    """Display the DTW-TSNE embedding.
    """
    df['segment_id'] = np.arange(df.shape[0])
    fig = px.scatter(data_frame=df, x='x', y='y', custom_data=['segment_id'])

    fig = go.Figure(data=fig.data)
    fig.update_traces(
        hovertemplate="ID:%{customdata} <br>t:%{x} <br>s:%{y:.2f}<extra></extra>"
        )
    fig.layout.update(
        title='t-SNE embedding of segment data based on DTW distance.',
        dragmode='select',
        showlegend=False,
        autosize=False,
        width=1000,
        height=1000,)
    # print(fig)

    return fig


@callback(
    Output('fig_selected', 'figure'),
    Input('fig-embedding', 'selectedData'),
    State('data-store-file', 'data'),
    State('data-store-embedding', 'data'),
    prevent_initial_call=True,
    )
def cb(selected, df, emb):
    """Display the selection of segments.
    """
    print(selected)

    selected_ids = [p['pointIndex'] for p in selected['points']]

    selected_data = select(df, segment_id=selected_ids).copy()
    selected_data['ts_'] = 0
    def add_ts_(grp):
        grp['ts_'] = np.arange(grp.shape[0])
        return grp
    selected_data = selected_data.groupby('segment_id').apply(add_ts_)
    fig = px.line(data_frame=selected_data, x='ts_', y=['s', 'da'], facet_col='segment_id', facet_col_wrap=4)
    fig.layout.update(showlegend=False,
                      autosize=False,
                      width=1000,
                      height=1000,)

    return fig













