import logging
import json

import numpy as np
import pandas as pd

import sklearn.preprocessing as skprep

from dash_extensions.enrich import Output, Input, State
from dash_extensions.enrich import html, dcc
from dash_extensions.enrich import DashProxy, ServersideOutput, ServersideOutputTransform
from dash_extensions.enrich import callback
from dash.exceptions import PreventUpdate

import dash
import dash_daq as daq
import dash_bootstrap_components as dbc

import plotly.graph_objs as go
import plotly.express as px

from utils import format_from_json, format_from_df, tab10, select, select_active_dfs


################################################################################
# LAYOUT
layout = [
    html.Div([
        dbc.Col([
            dcc.Graph(id='fig-all',),
            ]),
        ],
        style={'width': '49%', 'display': 'inline-block'},
    ),

    html.Div([
        dbc.Col([
            dcc.Graph(id='fig-hist-speed',),
            dcc.Graph(id='fig-hist-pressure',),
            ]),
        ],
        style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'},
    ),
]


################################################################################
# CALLBACKS
@callback(
    Output('fig-all', 'figure'),
    Input('data-store-register', 'data'),
    State('data-store-dfs', 'data'),
    prevent_initial_call=True,
    )
def cb(register, dfs):
    """Display data from all cards.
    """
    data_df = select_active_dfs(dfs, register)

    if data_df.shape[0] > 0:

        fig = px.scatter(
            data_frame=data_df, x='x', y='y', color='card_id',
            custom_data=['card_id', 'stroke_id', 'p'], opacity=0.3,
            color_discrete_sequence=px.colors.qualitative.T10,
            )

        mms = skprep.MinMaxScaler(feature_range=(10, 80))
        p_scaled = mms.fit_transform(data_df['p'].values.reshape(-1,1)).reshape(-1)
        fig.update_traces(marker=dict(size=p_scaled))
        fig = go.Figure(data=fig.data)

    else:
        fig = go.Figure()

    fig.update_traces(
        hovertemplate="card:%{customdata[0]} <br>stroke:%{customdata[1]} <br>p:%{customdata[2]:.2f}<extra></extra>"
        )
    fig.layout.update(
        title='Position (x, y) of all touch points for cards {}'.format(register['active']),# with stroke {} in blue.'.format(numinput),
        xaxis_title='x-position',
        yaxis_title='y-position',
        showlegend=False,
        autosize=False,
        width=1000,
        height=1000,)
    return fig


@callback(
    Output('fig-hist-speed', 'figure'),
    Input('data-store-register', 'data'),
    State('data-store-dfs', 'data'),
    prevent_initial_call=True,
    )
def cb(register, dfs):
    """Display the histogram of speed in the whole dataset.
    """
    data_df = select_active_dfs(dfs, register)

    if data_df.shape[0] > 0:
        fig = px.histogram(
            data_frame=data_df, x='s', color='card_id', histnorm='probability density',
            color_discrete_sequence=px.colors.qualitative.T10)
    else:
        fig = go.Figure()

    fig.layout.update(
        title='Histogram of speed value (used for segmentation).',
        showlegend=False,
        autosize=False,
        width=500,
        height=500,
        )

    return fig


@callback(
    Output('fig-hist-pressure', 'figure'),
    Input('data-store-register', 'data'),
    State('data-store-dfs', 'data'),
    prevent_initial_call=True,
    )
def cb(register, dfs):
    """Display the histogram of pressure in the whole dataset.
    """
    data_df = select_active_dfs(dfs, register)

    if data_df.shape[0] > 0:
        fig = px.histogram(
            data_frame=data_df, x='p', color='card_id', histnorm='probability density',
            color_discrete_sequence=px.colors.qualitative.T10)
    else:
        fig = go.Figure()

    fig.layout.update(
        title='Histogram of pressure.',
        showlegend=False,
        autosize=False,
        width=500,
        height=500,
        )

    return fig

