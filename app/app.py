# https://dash.plotly.com/interactive-graphing
# https://plotly.com/javascript/plotlyjs-events/#event-data

from dash import Dash, dcc, html
from dash.dependencies import Input, Output
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)

from dash import dcc
import plotly.graph_objs as go

import pandas as pd
import numpy as np
def read_data():
    data = pd.read_csv("../data.csv", index_col=0)
    new_rows = []
    default_value = np.ones(3) * np.nan
    for i, row in data.iterrows():
        row = eval(row[1].replace("false", "False"))
        x, y, p = row.get('xyp', default_value)
        x0, y0, p0 = row.get('xyp_lp', default_value)
        x1, y1, p1 = row.get('xyp_sg', default_value)
        new_row = [row['new_stroke'], row['timestamp'], row['n_stroke'], x, y, p, x0, y0, p0, x1, y1, p1]
        new_rows.append(new_row)
    data = pd.DataFrame(data=new_rows,
                        columns=['new_stroke', 'timestamp', 'n_stroke', 'x', 'y', 'p', 'x0', 'y0', 'p0', 'x1', 'y1', 'p1'])
    return data.iloc[:5000]
data = read_data()

def create_fig_all(data):
    fig = go.Figure()

    hovertext = np.c_[data['n_stroke'].index, data['n_stroke'].values]
    scatter = go.Scatter(x=data['x'], y=data['y'], mode='markers',
                         hovertext=hovertext,
                         opacity=.1, marker={'color':'black'},)
    fig.add_trace(scatter)
    fig.update_layout(
        autosize=False,
        width=1000,
        height=1000,
    )
    return fig, scatter

fig, scatter = create_fig_all(data)


def read_feat():
    feat = pd.read_csv("../feat.csv", index_col=0)
    feat = feat['1'].str.replace('null', '0')
    feat = pd.DataFrame(data=[eval(i) for i in feat.to_list()],
                        columns=['s', 'da', 'ns', 'ts', 'n', 'dtw'])
    return feat
feat = read_feat()

from plotly.subplots import make_subplots
def create_speed(n_stroke):
    fig = go.Figure()
    trace = feat[feat['ns'] == n_stroke]
    print("SPEED: ", trace.shape)
    scatter = go.Scatter(x=trace['ts'], y=feat['s'], mode='lines', name='speed')
    fig.add_trace(scatter)
    return fig

def create_dangle(n_stroke):
    fig = go.Figure()
    trace = feat[feat['ns'] == n_stroke]
    scatter = go.Scatter(x=trace['ts'], y=feat['da'], mode='lines', name='dAngle')
    fig.add_trace(scatter)
    return fig

app.layout = html.Div([
    html.H1("All data"),
    html.Div([dcc.Graph(id="fig_all", hoverData={}, figure=fig),
    #           dcc.Slider(0, 2000, 100, value=1000, id='my-slider'),
             ],
             style={'width': '49%', 'display': 'inline-block'},
            ),
    html.Div([dcc.Graph(id="fig_trace",),
             ],
             style={'width': '49%', 'display': 'inline-block'},
            )

])

@app.callback(
    Output(component_id="fig_all", component_property="figure"),
    Output(component_id="fig_trace", component_property="figure"),
    # Input(component_id="fig_all", component_property="hoverData"),
    Input(component_id="fig_all", component_property="clickData"),
    # Input(component_id="my-slider", component_property="value"),
    )
def update_click(clickData):
    print("###HOVER UPDATE", clickData)
    point = clickData['points'][0]

    if point['curveNumber'] == 0:
        pointIndex = point['pointIndex']
        n_stroke = data.iloc[pointIndex]['n_stroke']

        trace = data[data['n_stroke'] == n_stroke]
        trace_scatter = go.Scatter(x=trace['x'], y=trace['y'], opacity=1, marker={'color':'red'}, mode='markers', )

        fig, scatter = create_fig_all(data)
        fig.add_trace(trace_scatter)

        fig_speed = create_speed(n_stroke)
        # fig_dangle = create_speed(trace)

    # print("###HOVER UPDATE", fig.data)
    return fig, fig_speed


if __name__ == '__main__':
    app.run_server(debug=True)