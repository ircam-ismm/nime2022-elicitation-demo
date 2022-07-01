# https://community.plotly.com/t/bypassing-serialization-of-dash-graph-
# objects-for-efficient-server-side-caching/59669
import time
from typing import List
import json

import numpy as np
import plotly.io
import plotly.express as px
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, MATCH
from dash.exceptions import PreventUpdate
from plotly.graph_objs import Figure
from redis import Redis

FIGURE_LAYOUT = {"width": 300, "height": 250}

# docker run -p 6379:6379 redis
redis = Redis(host="0.0.0.0", port=6379)

app = Dash(__name__)
app.layout = html.Div([
    dcc.Input(id="num_plots", type="number", placeholder="Num. plots:"),
    dcc.Input(id="num_points", type="number", placeholder="Num. points:"),
    html.Div([], id="graphs-container"),
    html.Div([], id="figures-container"),
    html.Div([], id="signals-container"),
])


@app.callback(
    Output("graphs-container", "children"),
    Input("num_plots", "value")
)
def update_graphs(num_plots: int) -> List[dcc.Graph]:
    """Generates a number of empty figures according to user selection."""
    print('update_graphs', num_plots)

    if num_plots is None:
        raise PreventUpdate()

    return [
        dcc.Graph(
            id={"type": "graph", "index": i},
            figure=Figure(layout=FIGURE_LAYOUT)
        )
        for i in range(num_plots)
    ]


@app.callback(
    Output("figures-container", "children"),
    Input("num_plots", "value")
)
def update_figure_inputs(num_plots: int) -> List[dcc.Input]:
    """Generates hidden inputs to hold the figures that are retrieved as JSON strings from the
    server."""
    if num_plots is None:
        raise PreventUpdate()

    print('update_figure_inputs', num_plots)

    return [
        dcc.Input(id={"type": "figure", "index": i}, type="hidden")
        for i in range(num_plots)
    ]


@app.callback(
    Output("signals-container", "children"),
    Input("num_plots", "value")
)
def update_signal_inputs(num_plots: int) -> List[dcc.Input]:
    """These additional inputs allow to pattern match against the JSON hidden inputs."""

    print('update_signal_inputs', num_plots)
    if num_plots is None:
        raise PreventUpdate()

    return [
        dcc.Input(id={"type": "signal", "index": i}, type="hidden", value=i)
        for i in range(num_plots)
    ]


@app.callback(
    Output({"type": "figure", "index": MATCH}, "value"),
    Input({"type": "signal", "index": MATCH}, "value"),
    Input("num_points", "value"),
)
def update_figure(index: int, points: int) -> str:
    """Each call to this function returns the JSON string for one figure. Results are cached for
    (index, points) pairs."""
    print("update_figure", index, points)

    if (index is None) or (points is None) or (points == 0):
        return json.dumps({"layout": FIGURE_LAYOUT})
    else:
        return get_costly_figure(points, index)


app.clientside_callback(
    # This simple pattern-matching client-side callback does the magic of updating the graphs'
    # figure property with the parsed JSON. This is synchronous code, but likely always very fast.
    "(figure_json) => (figure_json !== undefined) ? JSON.parse(figure_json) : {}",
    Output({"type": "graph", "index": MATCH}, "figure"),
    Input({"type": "figure", "index": MATCH}, "value"),
)


def get_costly_figure(points: int, index: int) -> str:
    key = f"some-key-depending-on-{points}-and-{index}"
    figure_json = redis.get(key)

    if not figure_json:
        figure = produce_costly_figure(points)
        figure_json = plotly.io.to_json(figure)
        redis.set(key, figure_json)
    else:
        figure_json = figure_json.decode()

    return figure_json


def produce_costly_figure(points: int) -> Figure:
    """Some function that takes some >1s to complete."""
    time.sleep(np.random.randint(1, 3))
    return px.scatter(
        x=np.random.random(points),
        y=np.random.random(points)
    ).update_layout(**FIGURE_LAYOUT)


if __name__ == '__main__':

    print('running!')
    app.suppress_callback_exceptions = True
    app.run_server(debug=True)


