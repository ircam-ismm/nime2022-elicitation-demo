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
            html.Div([daq.NumericInput(id='button-stroke-id', label='stroke:', value=0, min=0, max=1e3),],
                     className='one columns'),
            html.Div([daq.NumericInput(id='button-segment-id', label='segment:',value=-1, min=0, max=1e3),],
                     className='one columns'),
            ],
        className='row'),

        html.Div([
            dbc.Col([
                dcc.Graph(id='fig-all',),
                ]),
            ],
            style={'width': '49%', 'display': 'inline-block'},
        ),

        html.Div([
            dbc.Col([
                dcc.Graph(id='fig-trace',),
                dcc.Graph(id='fig-speed',),
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
    Input('data-store-small', 'data'),
    prevent_initial_call=True
    )
def cb(small_data):
    """Set the range for stroke selection based on stroke ids in the data.
    """
    stroke_id_list = np.array(small_data['stroke_id_list'])
    return stroke_id_list.min(), stroke_id_list.max()

@callback(
    Output('button-segment-id', 'min'),
    Output('button-segment-id', 'max'),
    Input('data-store-small', 'data'),
    prevent_initial_call=True
    )
def cb(small_data):
    """Set the range for segment selection based on segment ids in the data.
    """
    segment_id_list = np.array(small_data['segment_id_list'])
    return segment_id_list.min(), segment_id_list.max()

@callback(
    Output('button-stroke-id', 'value'),
    Input('button-segment-id', 'value'),
    Input('data-store-small', 'data'),
    prevent_initial_call=True
    )
def cb(numinput, small_data):
    """Set the stroke id from a segment id selection or on page load.
    """
    if numinput != -1:
        segment_stroke_map = small_data['segment_stroke_map']
        stroke_id = segment_stroke_map[str(numinput)]
    else:
        stroke_id_list = np.array(small_data['stroke_id_list'])
        stroke_id = stroke_id_list.min()

    return stroke_id


@callback(
    Output('data-store-sk', 'data'),
    ServersideOutput('data-store-fig-all', 'data'),
    Input('data-store-file', 'data'),
    prevent_initial_call=True,
    )
def cb(df):
    """Create a scatter with all points.
    """
    mms = skprep.MinMaxScaler(feature_range=(10, 80))
    p_scaled = mms.fit_transform(df['p'].values.reshape(-1,1)).reshape(-1)

    fig = px.scatter(data_frame=df, x='x', y='y', custom_data=['stroke_id'], opacity=0.05,)
    fig.update_traces(marker=dict(color='black', size=p_scaled))

    mms_json = mms_to_json(mms)

    return mms_json, fig


@callback(
    Output('fig-all', 'figure'),
    Input('data-store-file', 'data'),
    Input('data-store-fig-all', 'data'),
    Input('data-store-sk', 'data'),
    Input('button-stroke-id', 'value'),
    prevent_initial_call=True,
    )
def cb(df, fig_a, sk_data, numinput):
    """Update the scatter with all points with a specific stroke.
    """
    if sk_data == None:
        return dash.no_update

    mms = mms_from_json(sk_data)
    stroke_df = select(df, stroke_id=numinput)

    if stroke_df.shape[0] > 0:
        p_scaled = mms.transform(stroke_df['p'].values.reshape(-1,1)).reshape(-1)
        fig_b = px.scatter(data_frame=stroke_df, x='x', y='y', custom_data=['stroke_id'], opacity=1)
        fig_b.update_traces(marker=dict(size=p_scaled))

    fig = go.Figure(data=fig_a.data + fig_b.data)
    fig.update_traces(
        hovertemplate="ID:%{customdata} <br>t:%{x} <br>s:%{y:.2f}<extra></extra>"
        )
    fig.layout.update(
        title='Position (x, y) of all touch points with stroke {} in blue.'.format(numinput),
        xaxis_title='x-position',
        yaxis_title='y-position',
        showlegend=False,
        autosize=False,
        width=1000,
        height=1000,)
    return fig


@callback(
    Output('fig-trace', 'figure'),
    Input('data-store-file', 'data'),
    Input('data-store-sk', 'data'),
    Input('button-stroke-id', 'value'),
    )
def cb(df, sk_data, numinput):
    """Display a single stroke (x, y) with its segments coloured individually.
    """
    if sk_data is None:
        return dash.no_update

    stroke_i = select(df, stroke_id=numinput).copy()

    if stroke_i.shape[0] > 0:
        mms = mms_from_json(sk_data)
        stroke_i['size'] = mms.transform(stroke_i['p'].values.reshape(-1,1)).reshape(-1)
        stroke_i['color'] = ['rgba'+str(tab10[int(i)%10]+(1,)) for i in stroke_i['segment_id']]

        fig = px.scatter(
                data_frame=stroke_i, x='x', y='y', color='color', size='size',
                custom_data=['segment_id']
                )

    fig = go.Figure(data=fig.data)
    fig.update_traces(
        hovertemplate="ID:%{customdata}<extra></extra>"
        )
    fig.layout.update(
        title='Position (x, y) of stroke {}<br>with segments coloured individually.'.format(numinput),
        xaxis_title='x-position',
        yaxis_title='y-position',
        showlegend=False,
        autosize=False,
        width=500,
        height=500,
    )

    return fig

@callback(
    Output('fig-speed', 'figure'),
    Input('data-store-file', 'data'),
    Input('button-stroke-id', 'value'),
    )
def cb(df, numinput):
    """Display a single stroke (ts, s) with its segments coloured individually.
    """
    if df is None:
        return dash.no_update

    stroke_i = select(df, stroke_id=numinput).copy()

    if stroke_i.shape[0] > 0:
        stroke_i['color'] = ['rgba'+str(tab10[int(i)%10]+(1,)) for i in stroke_i['segment_id']]

        fig = px.scatter(
                data_frame=stroke_i, x='ts', y='s', color='color',
                custom_data=['segment_id']
                )

    fig = go.Figure(data=fig.data)
    fig.update_traces(
        hovertemplate="ID:%{customdata} <br>t:%{x} <br>s:%{y:.2f}<extra></extra>"
        )
    fig.update_layout(
        title='Feature profile of stroke {}<br>with segments coloured individually.'.format(numinput),
        xaxis_title='timestamp [ms]',
        yaxis_title='speed',
        showlegend=False,
        autosize=False,
        width=500,
        height=500,
        )

    return fig


################################################################################
# UTILS
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



