# https://gist.github.com/tcbegley/b7c49d0aec605e383d3b8190448f45f2
import json

import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import ALL, Input, Output, State
from dash.exceptions import PreventUpdate

FONT_AWESOME = "https://use.fontawesome.com/releases/v5.13.0/css/all.css"
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME])

app.layout = dbc.Container(
    [
        dbc.InputGroup(
            [
                dbc.Input(id="input"),
                dbc.InputGroup(
                    dbc.Button("Add card", id="add-button"),
                ),
            ],
            className="mb-4",
        ),
        html.Div([], id="output"),
    ],
    className="p-5",
)


def make_card(n_add, content):
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    "Card header",
                    html.Button(
                        html.I(className="fas fa-times"),
                        className="ml-auto close",
                        id={"type": "close-button", "index": n_add},
                    ),
                ]
            ),
            dbc.CardBody(html.P(content, className="card-text")),
        ],
        id={"type": "card", "index": n_add},
        style={"width": "400px"},
        className="mb-3 mx-auto",
    )


@app.callback(
    Output("output", "children"),
    [
        Input("add-button", "n_clicks"),
        Input({"type": "close-button", "index": ALL}, "n_clicks"),
    ],
    [
        State("input", "value"),
        State("output", "children"),
        State({"type": "close-button", "index": ALL}, "id"),
    ],
)
def manage_cards(n_add, n_close, content, children, close_id):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate
    else:
        button_id, _ = ctx.triggered[0]["prop_id"].split(".")

    if button_id == "add-button":
        if n_add:
            if children is None:
                children = []
            children.append(make_card(n_add, content))
    else:
        button_id = json.loads(button_id)
        index_to_remove = button_id["index"]
        children = [
            child
            for child in children
            if child["props"]["id"]["index"] != index_to_remove
        ]

    return children


if __name__ == "__main__":
    app.run_server(debug=True)