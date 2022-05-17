
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
import dash_bootstrap_components as dbc

import plotly.graph_objs as go
import plotly.express as px

from utils import format_from_json, format_from_df, select, select_active_dfs
import embedding


################################################################################
# LAYOUT
layout = [
    html.Div([
        dbc.Button(id='button-embed', children='Embed!'),
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
]


################################################################################
# CALLBACKS
@callback(
    ServersideOutput('data-store-embedding', 'data'),
    Input('button-embed', 'n_clicks'),
    State('data-store-register', 'data'),
    State('data-store-dfs', 'data'),
    prevent_initial_call=True,
)
def cb(n_clicks, register, dfs):
    """Compute a DTW-TSNE embedding from individual segments.
    """
    data_df = select_active_dfs(dfs, register)
    grp_by_card_segment = data_df.groupby(['card_id', 'segment_id'])

    segments = [grp[['s', 'da']].values for i, grp in grp_by_card_segment]
    sm = embedding.compute_similarity_matrix(segments)
    emb = embedding.tsne_embed(sm, perplexity=30)
    emb = pd.DataFrame(emb, columns=['x', 'y'])

    emb[['card_id', 'segment_id']] = pd.DataFrame(list(grp_by_card_segment.groups.keys()))

    return emb


@callback(
    Output('fig-embedding', 'figure'),
    Input('data-store-embedding', 'data'),
    State('data-store-register', 'data'),
    State('data-store-dfs', 'data'),
    prevent_initial_call=True,
    )
def cb(emb, register, dfs):
    """Display the DTW-TSNE embedding.
    """
    if emb is None:
        return dash.no_update

    # TODO: add different color schemes, by cards or invention time as follows.
    # color=df.groupby('segment_id')['t0_norm'].mean()
    # emb['segment_id'] = list(df.groupby(['segment_id']).groups.keys())

    fig = px.scatter(data_frame=emb, x='x', y='y',
                     color_discrete_sequence=px.colors.qualitative.T10, color='card_id',
                     custom_data=['card_id', 'segment_id'])

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
    State('data-store-register', 'data'),
    State('data-store-dfs', 'data'),
    State('data-store-embedding', 'data'),
    prevent_initial_call=True,
    )
def cb(xy, selected, register, dfs, emb):
    """Display the selection of segments.
    """
    if selected is None:
        return dash.no_update

    data_df = select_active_dfs(dfs, register)
    selection = np.array([p['customdata'] for p in selected['points']]).astype(int)

    res = pd.DataFrame()
    for row in selection:
        selected = select(data_df, card_id=str(row[0]), segment_id=row[1])
        res = pd.concat([res, selected])
    res['plot_key'] = res.apply(lambda x: str(x['card_id'])+'_'+str(x['segment_id']), axis=1)
    selected_data = res

    selected_data['ts_'] = 0
    def add_ts_(grp):
        grp['ts_'] = np.arange(grp.shape[0])
        return grp
    selected_data = selected_data.groupby('plot_key').apply(add_ts_)

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
        facet_col='plot_key', facet_col_wrap=4)
    fig.update_layout(
        title='Selection of segments displayed by {}'.format(xy),
        showlegend=False,
        autosize=False,
        width=1000,
        height=1000,
        )

    return fig













