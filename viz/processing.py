import logging

import numpy as np
import pandas as pd

from dash import dcc, html
from dash.dependencies import Input, Output
from dash import callback
from dash.exceptions import PreventUpdate

import dash_daq as daq
import dash_bootstrap_components as dbc

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
# CALLBACK
# Some graphs can be long to create due the amount of data points involved. We
# therefore cache the figure when possible for background data.
# See https://community.plotly.com/t/bypassing-serialization-of-dash-graph-
# objects-for-efficient-server-side-caching/59669 for more info.

import json
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


@callback(
    Output('button-stroke-id', 'min'),
    Output('button-stroke-id', 'max'),
    Output('button-stroke-id', 'value'),
    Input('data-store-small', 'data'),
    )
def update_rangeslider(small_data):
    print('update_rangeslider', small_data)

    if small_data == None:
        raise PreventUpdate()


    stroke_id_list = np.array(small_data['stroke_id_list'])
    return stroke_id_list.min(), stroke_id_list.max(), stroke_id_list.min()
    # else:
    #     return 0, 10, 1


import plotly.graph_objs as go
import plotly.express as px
import plotly.io

import sklearn.preprocessing as skprep

@callback(
    Output('data-store-sk', 'data'),
    Output('data-store-fig_all', 'data'),
    Input('data-store-file', 'data'),
    )
def create_fig_all(jsonified_cleaned_data):
    print("create_fig_all - flag", jsonified_cleaned_data==None)

    if jsonified_cleaned_data == None:
        return None, None
        # raise PreventUpdate()

    # print(jsonified_cleaned_data)

    logging.info('#### create fig - start')

    data_df = format_from_json(jsonified_cleaned_data, source='/data')
    print('create_fig_all - data', data_df.head())

    mms = skprep.MinMaxScaler(feature_range=(10, 80))

    p_scaled = mms.fit_transform(data_df['p'].values.reshape(-1,1)).reshape(-1)

    fig = px.scatter(x=data_df['x'], y=data_df['y'], opacity=0.05)
    fig.update_traces(marker=dict(color='black', size=p_scaled))

    logging.info('#### create fig - end')

    mms_json = mms_to_json(mms)

    return mms_json, plotly.io.to_json(fig)


@callback(
    Output('fig_all', 'figure'),
    Input('data-store-file', 'data'),
    Input('data-store-fig_all', 'data'),
    Input('data-store-sk', 'data'),
    Input('button-stroke-id', 'value'),
    )
def update_graph_all(jsonified_cleaned_data, fig_all_json, sk_data, value):
    """Create the graph for data all when the datastore is updated.
    """

    if jsonified_cleaned_data == None or fig_all_json == None or sk_data == None:
        return go.Figure()

    # print("update_graph", value, fig_all_json)
    # if

    fig_a = plotly.io.from_json(fig_all_json)
    mms = mms_from_json(sk_data)

    data_df = format_from_json(jsonified_cleaned_data, source='/data')
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
def update_graph_stroke(jsonified_cleaned_data, sk_data, numinput_value):
    # fig = go.Figure()
    print('update_graph_stroke', jsonified_cleaned_data==None, sk_data)

    if jsonified_cleaned_data == None or sk_data == None:
        raise PreventUpdate()

    df = format_from_json(jsonified_cleaned_data)
    print('update_graph_stroke', df.head())

    mms = mms_from_json(sk_data)

    # select stroke
    stroke_i = select(df, stroke_id=numinput_value)

    if stroke_i.shape[0] > 0:
        # stroke_i_feat = stroke_i.join(df.set_index('key'), on='key').dropna()
        # if stroke_i_feat.shape[0] > 0:
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
def update_graph_speed(jsonified_cleaned_data, numinput_value):

    print('update_graph_speed', jsonified_cleaned_data==None, numinput_value)

    if jsonified_cleaned_data == None:
        raise PreventUpdate()

    df = format_from_json(jsonified_cleaned_data)
    print('update_graph_speed', numinput_value, df.head())

    # select stroke
    stroke_i = select(df, stroke_id=numinput_value)

    print("graph SPEED", stroke_i.shape)

    if stroke_i.shape[0] > 0:
        # stroke_i_feat = stroke_i.join(df.set_index('key'), on='key').dropna()
        # if stroke_i_feat.shape[0] > 0:
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





