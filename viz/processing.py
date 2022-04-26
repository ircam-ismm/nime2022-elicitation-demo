import numpy as np
import pandas as pd

import plotly.graph_objs as go

from dash import dcc, html
from dash.dependencies import Input, Output
from dash import callback
import dash_daq as daq
import dash_bootstrap_components as dbc

from utils import format_from_json, tab10, select


################################################################################
# LAYOUT
layout = [

    html.Div([
        html.H5("Select stroke:"),
        daq.NumericInput(id='my-numeric-input-1',value=0, min=0, max=1e3),
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

    html.Div([
        dcc.Dropdown(['xy', 'feat'], 'xy', id='demo-dropdown'),
        ], style={'width': '49%', 'display': 'inline-block'},),

]


################################################################################
# CALLBACK

# @callback(
#     Output('my-range-slider', 'max'),
#     Input('data-store', 'data')
#     )
# def update_rangeslider(jsonified_cleaned_data):
#     if jsonified_cleaned_data is not None:
#         data_df = format_from_json(jsonified_cleaned_data, source='/data')
#         return len(set(data_df['stroke_id']))
#     else:
#         return 20


@callback(
    Output('my-numeric-input-1', 'min'),
    Output('my-numeric-input-1', 'max'),
    Output('my-numeric-input-1', 'value'),
    Input('data-store', 'data'),
    )
def update_rangeslider(jsonified_cleaned_data):
    if jsonified_cleaned_data is not None:
        data_df = format_from_json(jsonified_cleaned_data, source='/data')
        stroke_id_list = np.array(list(set(data_df['stroke_id'])))
        return stroke_id_list.min(), stroke_id_list.max(), stroke_id_list.min()
    else:
        return 0, 10, 1

import sklearn.preprocessing as skprep

@callback(
    Output('fig_all', 'figure'),
    Input('data-store', 'data'),
    Input('my-numeric-input-1', 'value'),
    )
def update_graph_all(jsonified_cleaned_data, value):
    """Create the graph for data all when the datastore is updated.
    """

    fig = go.Figure()

    print("update_graph", value)
    if jsonified_cleaned_data is not None:

        data_df = format_from_json(jsonified_cleaned_data, source='/data')

        mms = skprep.MinMaxScaler(feature_range=(10, 80))
        p_scaled = mms.fit_transform(data_df['p'].values.reshape(-1,1))

        scatter = go.Scatter(
            x=data_df['x'], y=data_df['y'],
            mode='markers',
            marker={'size':p_scaled, 'color':'black'},
            opacity=.1,
            name='all data')
        fig.add_trace(scatter)

        stroke_df = select(data_df, stroke_id=value)
        if stroke_df.shape[0] > 0:
            p_scaled = mms.transform(stroke_df['p'].values.reshape(-1,1))
            scatter = go.Scatter(
                x=stroke_df['x'], y=stroke_df['y'], mode='markers',
                marker={'size':p_scaled, 'color':'blue'},
                opacity=1,
                name='stroke '+str(value))
            fig.add_trace(scatter)

        fig.update_layout(
            autosize=False,
            width=1000,
            height=1000,
        )

    return fig


@callback(
    Output('fig_trace', 'figure'),
    Input('data-store', 'data'),
    Input('my-numeric-input-1', 'value'),
    Input('demo-dropdown', 'value')
    )
def update_graph_stroke(jsonified_cleaned_data, numinput_value, dropdown_value):
    fig = go.Figure()

    if jsonified_cleaned_data is not None:

        data_df = format_from_json(jsonified_cleaned_data, source='/data')
        feat_df = format_from_json(jsonified_cleaned_data, source='/feat')

        mms = skprep.MinMaxScaler(feature_range=(10, 80))
        mms.fit(data_df['p'].values.reshape(-1,1))

        # select stroke
        stroke_i = select(data_df, stroke_id=numinput_value)

        if stroke_i.shape[0] > 0:

            stroke_i_feat = stroke_i.join(feat_df.set_index('key'), on='key').dropna()

            if stroke_i_feat.shape[0] > 0:
                p_scaled = mms.transform(stroke_i['p'].values.reshape(-1,1))
                scatter = go.Scatter(
                    x=stroke_i['x'], y=stroke_i['y'], mode='markers', marker_symbol='x',
                    opacity=0.1, marker={'size':p_scaled, 'color':'black'},
                    )
                fig.add_trace(scatter)

                p_scaled = mms.transform(stroke_i_feat['p'].values.reshape(-1,1))
                colors = ["rgba"+str(tab10[int(i)%10]+(1,)) for i in stroke_i_feat['segment_id']]
                scatter = go.Scatter(
                    x=stroke_i_feat['x'], y=stroke_i_feat['y'], mode='markers',
                    marker={'size':p_scaled, 'color':colors},
                    customdata=stroke_i_feat['segment_id'],
                    hovertemplate="%{customdata}",
                    opacity=1,
                    name='stroke '+str(numinput_value))
                fig.add_trace(scatter)

                fig.update_layout(
                    autosize=False,
                    width=1000,
                    height=1000,
                )

    return fig




@callback(
    Output('fig_speed', 'figure'),
    Input('data-store', 'data'),
    Input('my-numeric-input-1', 'value'),
    Input('demo-dropdown', 'value')
    )
def update_graph_speed(jsonified_cleaned_data, numinput_value, dropdown_value):
    fig = go.Figure()

    if jsonified_cleaned_data is not None:
        pass

        data_df = format_from_json(jsonified_cleaned_data, source='/data')
        feat_df = format_from_json(jsonified_cleaned_data, source='/feat')

        mms = skprep.MinMaxScaler(feature_range=(10, 80))
        mms.fit(data_df['p'].values.reshape(-1,1))

        # select stroke
        stroke_i = select(data_df, stroke_id=numinput_value)

        if stroke_i.shape[0] > 0:

            stroke_i_feat = stroke_i.join(feat_df.set_index('key'), on='key').dropna()

            if stroke_i_feat.shape[0] > 0:

                p_scaled = mms.transform(stroke_i_feat['p'].values.reshape(-1,1))
                colors = ["rgba"+str(tab10[int(i)%10]+(1,)) for i in stroke_i_feat['segment_id']]
                scatter = go.Scatter(
                    x=stroke_i_feat['ts'], y=stroke_i_feat['s'], mode='markers',
                    marker={'size':p_scaled, 'color':colors},
                    customdata=stroke_i_feat['segment_id'],
                    hovertemplate="%{customdata}",
                    opacity=1,
                    name='stroke '+str(numinput_value))
                fig.add_trace(scatter)

                fig.update_layout(
                    autosize=False,
                    width=1000,
                    height=1000,
                )

    return fig





