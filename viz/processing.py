import numpy as np
import pandas as pd

import plotly.graph_objs as go

from dash import dcc, html
from dash.dependencies import Input, Output
from dash import callback

from utils import select

################################################################################
# LAYOUT
components = [
    html.Div([
        dcc.Graph(id="fig_all",),
        dcc.RangeSlider(0, 20, 1, value=[0, 1], id='my-range-slider'),
        ],
        style={'width': '49%', 'display': 'inline-block'},
    ),
    
    html.Div([
        dcc.Graph(id="fig_trace",),
        ],
        style={'width': '49%', 'display': 'inline-block'},
    )
]


################################################################################
# CALLBACK


# html.Div(id = "appRangeSlider")
# ])

# @app.callback(
#     Output("appRangeSlider", "children"),
#     [Input("group", "value")])

# def plotRangeSlider(group):
#     if group == "A":
#         return dcc.RangeSlider(
#             id = "my-range-slider",
#             min = 0,
#             max = 20,
#             step = 0.5,
#             value=[5, 15])

@callback(Output('my-range-slider', 'max'),
          # Output('my-range-slider', ''),
          Input('data-store', 'data'))
def update_rangeslider(jsonified_cleaned_data):
    if jsonified_cleaned_data is not None:
        data_df = format_from_json(jsonified_cleaned_data, source='/data')
        return len(set(data_df['stroke_id']))
    else: 
        return 20

@callback(Output('fig_all', 'figure'),
          Input('data-store', 'data'))
def update_graph(jsonified_cleaned_data):
    """Create the graph for data all when the datastore is updated.
    """

    fig = go.Figure()

    print("update_graph")
    if jsonified_cleaned_data is not None:

        data = pd.read_json(jsonified_cleaned_data, orient='split')
        data.columns = [0, 'source', 'data']
        select_df = select(data, source='/data')
        data_df = format_data(select_df)

        # hovertext = np.c_[data['n_stroke'].index, data['n_stroke'].values]
        scatter = go.Scatter(x=data_df['x'], y=data_df['y'], mode='markers',)
                             # hovertext=hovertext,
                             # opacity=.1, marker={'color':'black'},)
        fig.add_trace(scatter)
        fig.update_layout(
            autosize=False,
            width=1000,
            height=1000,
        )

    return fig


################################################################################
# LOCAL

def format_from_json(jsonified_cleaned_data, source='/data'):
    data = pd.read_json(jsonified_cleaned_data, orient='split')
    data.columns = [0, 'source', 'data']
    select_df = select(data, source=source)
    data_df = format_data(select_df)
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
        row = eval(row[1])
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

