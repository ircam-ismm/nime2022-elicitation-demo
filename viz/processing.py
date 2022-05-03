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
import plotly.io

from utils import format_from_json, format_from_df, tab10, select


################################################################################
# LAYOUT
layout = [
    # FIGURES
    html.Div(id='processing-layout', children=[

        html.Div([
            html.H5("Select stroke:"),
            daq.NumericInput(id='button-stroke-id',value=0, min=0, max=1e3),
        ],
        style={'width': '100%', 'display': 'inline-block'}
        ),

        html.Div([
            dbc.Col([
                dcc.Graph(id="fig_all",),
                ]),
            ],
            style={'width': '49%', 'display': 'inline-block'},
        ),

        html.Div([
            dbc.Col([
                dcc.Graph(id="fig_trace",),
                dcc.Graph(id="fig_speed",),
                ]),
            ],
            style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'},
        ),

        # this align the slider to the right hand side
        html.Div([], style={'width': '49%', 'display': 'inline-block'},),
    ],
    style= {'display': 'none'}
    )
]


################################################################################
# CALLBACKS
@callback(
    Output('button-stroke-id', 'min'),
    Output('button-stroke-id', 'max'),
    Output('button-stroke-id', 'value'),
    Input('data-store-small', 'data'),
    prevent_initial_call=True
    )
def update_rangeslider(small_data):
    stroke_id_list = np.array(small_data['stroke_id_list'])
    return stroke_id_list.min(), stroke_id_list.max(), stroke_id_list.min()


@callback(
    Output('data-store-sk', 'data'),
    ServersideOutput('data-store-fig_all', 'data'),
    Input('data-store-file', 'data'),
    prevent_initial_call=True,
    )
def create_fig_all(df):
    mms = skprep.MinMaxScaler(feature_range=(10, 80))
    p_scaled = mms.fit_transform(df['p'].values.reshape(-1,1)).reshape(-1)

    fig = px.scatter(x=df['x'], y=df['y'], opacity=0.05)
    fig.update_traces(marker=dict(color='black', size=p_scaled))

    mms_json = mms_to_json(mms)

    return mms_json, fig


@callback(
    Output('fig_all', 'figure'),
    Input('data-store-file', 'data'),
    Input('data-store-fig_all', 'data'),
    Input('data-store-sk', 'data'),
    Input('button-stroke-id', 'value'),
    prevent_initial_call=True,
    )
def update_graph_all(data_df, fig_a, sk_data, value):
    if sk_data == None:
        return dash.no_update

    mms = mms_from_json(sk_data)
    stroke_df = select(data_df, stroke_id=value)

    if stroke_df.shape[0] > 0:
        p_scaled = mms.transform(stroke_df['p'].values.reshape(-1,1)).reshape(-1)
        fig_b = px.scatter(x=stroke_df['x'], y=stroke_df['y'], opacity=1)
        fig_b.update_traces(marker=dict(size=p_scaled))

    fig = go.Figure(data=fig_a.data + fig_b.data)
    fig.layout.update(showlegend=False,
                      autosize=False,
                      width=1000,
                      height=1000,)
    return fig


@callback(
    Output('fig_trace', 'figure'),
    Input('data-store-file', 'data'),
    Input('data-store-sk', 'data'),
    Input('button-stroke-id', 'value'),
    )
def update_graph_stroke(df, sk_data, numinput_value):
    if sk_data is None:
        return dash.no_update

    stroke_i = select(df, stroke_id=numinput_value)

    if stroke_i.shape[0] > 0:
        mms = mms_from_json(sk_data)
        p_scaled = mms.transform(stroke_i['p'].values.reshape(-1,1)).reshape(-1)
        colors = ["rgba"+str(tab10[int(i)%10]+(1,)) for i in stroke_i['segment_id']]
        fig = px.scatter(x=stroke_i['x'], y=stroke_i['y'], color=colors, size=p_scaled)

    fig = go.Figure(data=fig.data)
    fig.layout.update(
        showlegend=False,
        autosize=False,
        width=500,
        height=500,
    )

    return fig

@callback(
    Output('fig_speed', 'figure'),
    Input('data-store-file', 'data'),
    Input('button-stroke-id', 'value'),
    )
def update_graph_speed(df, numinput_value):
    if df is None:
        return dash.no_update

    stroke_i = select(df, stroke_id=numinput_value)

    if stroke_i.shape[0] > 0:
        colors = ["rgba"+str(tab10[int(i)%10]+(1,)) for i in stroke_i['segment_id']]
        fig = px.scatter(x=stroke_i['ts'], y=stroke_i['s'], color=colors)

    fig = go.Figure(data=fig.data)
    fig.update_layout(
        showlegend=False,
        autosize=False,
        width=500,
        height=500,
    )

    return fig


def mms_to_json(model):
    serialize = json.dumps

    data = {}
    data['init_params'] = model.get_params()
    data['model_params'] = mp = {}
    for p in ('min_', 'scale_','data_min_', 'data_max_', 'data_range_'):
        mp[p] = getattr(model, p).tolist()
    return serialize(data)

def mms_from_json(jstring):
    data = json.loads(jstring)
    model = skprep.MinMaxScaler(**data['init_params'])
    for name, p in data['model_params'].items():
        setattr(model, name, np.array(p))
    return model



