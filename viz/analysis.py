
import logging

import numpy as np
import pandas as pd

import sklearn.preprocessing as skprep

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
                dcc.Graph(id='fig-embedding',),
            ],
            style={'width': '49%', 'display': 'inline-block'},
        ),
        html.Div([
                dcc.Dropdown(['features', 'position'], 'features', id='fig-selected-dropdown'),
                dcc.Graph(id='fig-selected',),
            ],
            style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'},
        ),

        html.Div([
            html.Button(id='button_id', children='Embed!'),
        ],
        style={'width': '100%', 'display': 'inline-block'}
        ),

        ],
        style= {'display': 'block'}
        )
    ]


################################################################################
# CALLBACKS
@callback(
    ServersideOutput('data-store-embedding', 'data', session_check=True, arg_check=False),
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
    Input('data-store-file', 'data'),
    prevent_initial_call=True,
    )
def cb(emb, df):
    """Display the DTW-TSNE embedding.
    """
    if emb is None:
        return dash.no_update

    # compute color
    color=df.groupby('segment_id')['t0_norm'].mean()

    # similar to list(set(df['segment_id']))
    emb['segment_id'] = list(df.groupby(['segment_id']).groups.keys())

    fig = px.scatter(data_frame=emb, x='x', y='y',
                     color_continuous_scale='rdpu', color=color,
                     custom_data=['segment_id'])

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

    return fig


@callback(
    Output('fig-selected', 'figure'),
    Input('fig-selected-dropdown', 'value'),
    Input('fig-embedding', 'selectedData'),
    State('data-store-file', 'data'),
    State('data-store-embedding', 'data'),
    prevent_initial_call=True,
    )
def cb(xy, selected, df, emb):
    """Display the selection of segments.
    """
    if selected is None:
        return dash.no_update

    selected_ids = [p['customdata'][0] for p in selected['points']]
    selected_data = select(df, segment_id=selected_ids).copy()

    selected_data['ts_'] = 0
    def add_ts_(grp):
        grp['ts_'] = np.arange(grp.shape[0])
        return grp
    selected_data = selected_data.groupby('segment_id').apply(add_ts_)

    if xy == 'features':
        x = 'ts_'
        y = ['s', 'da']
        labels = {'ts_': 'zeroed timestamp [ms]', 'value': 's, da'}
    if xy == 'position':
        x = 'x'
        y = 'y'
        labels = {'x': 'x', 'y': 'y'}

    fig = px.line(
        data_frame=selected_data, x=x, y=y, labels=labels,
        facet_col='segment_id', facet_col_wrap=4)
    fig.update_layout(
        title='Selection of segments displayed by {}'.format(xy),
        showlegend=False,
        autosize=False,
        width=1000,
        height=1000,
        )

    return fig













