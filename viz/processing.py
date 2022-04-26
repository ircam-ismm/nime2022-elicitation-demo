import numpy as np
import pandas as pd

import plotly.graph_objs as go

from dash import dcc, html
from dash.dependencies import Input, Output
from dash import callback
import dash_daq as daq

from utils import select, tab10

################################################################################
# LAYOUT
layout = [

    html.Div([
        daq.NumericInput(id='my-numeric-input-1',value=86, min=0, max=1e3),
    ],
    style={'width': '100%', 'display': 'inline-block'}
    ),

    html.Div([
        dcc.Graph(id="fig_all",),
        # dcc.RangeSlider(0, 20, 1, value=[0, 1], id='my-range-slider'),
        ],
        style={'width': '49%', 'display': 'inline-block'},
    ),
    
    html.Div([
        dcc.Graph(id="fig_trace",),
        ],
        style={'width': '49%', 'display': 'inline-block'},
    ),

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

        data = pd.read_json(jsonified_cleaned_data, orient='split')
        data.columns = [0, 'source', 'data']
        select_df = select(data, source='/data')
        data_df = format_data(select_df)

        mms = skprep.MinMaxScaler(feature_range=(10, 80))
        p_scaled = mms.fit_transform(data_df['p'].values.reshape(-1,1))

        # hovertext = np.c_[data['n_stroke'].index, data['n_stroke'].values]
        scatter = go.Scatter(
            x=data_df['x'], y=data_df['y'],
            mode='markers',
            marker={'size':p_scaled, 'color':'black'},
            # hovertext=hovertext,
            opacity=.1,
            name='all data')
        fig.add_trace(scatter)

        stroke_df = select(data_df, stroke_id=value)
        if stroke_df.shape[0] > 0:
            p_scaled = mms.transform(stroke_df['p'].values.reshape(-1,1))
            scatter = go.Scatter(
                x=stroke_df['x'], y=stroke_df['y'], mode='markers',
                marker={'size':p_scaled, 'color':'blue'},
                # hovertext=hovertext,
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
        # get both df
        data = pd.read_json(jsonified_cleaned_data, orient='split')
        data.columns = [0, 'source', 'data']
        select_df = select(data, source='/data')
        data_df = format_data(select_df)
        select_df = select(data, source='/feat')
        feat_df = format_feat(select_df)

        mms = skprep.MinMaxScaler(feature_range=(10, 80))
        mms.fit(data_df['p'].values.reshape(-1,1))

        # select stroke
        stroke_i = select(data_df, stroke_id=numinput_value)

        if stroke_i.shape[0] > 0:

            stroke_i_feat = stroke_i.join(feat_df.set_index('key'), on='key').dropna()

            if stroke_i_feat.shape[0] > 0:
                p_scaled = mms.transform(stroke_i_feat['p'].values.reshape(-1,1))

                colors = ["rgba"+str(tab10[int(i)]+(1,)) for i in stroke_i_feat['segment_id']]
                scatter = go.Scatter(
                    x=stroke_i_feat['x'], y=stroke_i_feat['y'], mode='markers',
                    marker={'size':p_scaled, 'color':colors},
                    # hovertext=hovertext,
                    opacity=1,
                    name='stroke '+str(numinput_value))
                fig.add_trace(scatter)

                fig.update_layout(
                    autosize=False,
                    width=1000,
                    height=1000,
                )

    return fig


# @app.callback(
#     Output('dd-output-container', 'children'),
#     Input('demo-dropdown', 'value')
# )
# def update_output(value):
#     return f'You have selected {value}'

################################################################################
# LOCAL

def format_from_json(jsonified_cleaned_data, source='/data'):
    data = pd.read_json(jsonified_cleaned_data, orient='split')
    data.columns = [0, 'source', 'data']
    select_df = select(data, source=source)

    if source == '/data':
        data_df = format_data(select_df)
    elif source == '/feat':
        data_df = format_feat(select_df)

    return data_df

def format_data(df):
    new_rows = []
    default_value = np.ones(3) * np.nan

    for i, row in df.iterrows():

        row = eval(row['data'].replace("false", "False"))

        key = row['sample_key']
        t0 = row['timestamp0']
        ts = row['timestamp']
        stroke_id = row['stroke_id']

        x, y, p = row.get('xyp', default_value)
        x_, y_, p_ = row.get('rel_xyp', default_value)
        x0, y0, p0 = row.get('rel_xyp_lp', default_value)
        x1, y1, p1 = row.get('xyp_sg', default_value)

        new_row = [key, t0, ts, stroke_id, x, y, p, x_, y_, p_, x0, y0, p0, x1, y1, p1]
        new_rows.append(new_row)

    data = pd.DataFrame(data=new_rows,
                        columns=['key', 't0', 'ts', 'stroke_id',
                                 'x', 'y', 'p', 'x_', 'y_', 'p_',
                                 'x0', 'y0', 'p0', 'x1', 'y1', 'p1']
                       )

    return data

def format_feat(df):
    # feat = feat['1'].str.replace('null', '0')??
    new_rows = []
    for i, row in df.iterrows():
        row = eval(row['data'])
        key = row['sample_key']
        segment_id = row['segment_id']
        s = row['s']
        da = row['da']
        min_dtw = row.get('min_dtw', -1)
        min_dtw_id = row.get('min_dtw_id', -1)

        new_row = [key, segment_id, s, da, min_dtw, min_dtw_id]
        new_rows.append(new_row)

    data = pd.DataFrame(data=new_rows,
                        columns=['key', 'segment_id', 's', 'da', 'min_dtw', 'min_dtw_id'])
    # data = data.convert_dtypes()
    return data

