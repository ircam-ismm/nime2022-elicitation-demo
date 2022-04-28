import dash
from dash import dcc, html
from dash.dependencies import Input, Output

################################################################################
# The following modules contain their own layout and callbacks.
# See https://dash.plotly.com/urls for info about program structure.
import upload
import processing

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    upload.layout+\
    [dcc.Tabs(id="tabs-example-graph", value='tab-1-example-graph',
              children=[dcc.Tab(label='Processing', value='tab-1-example-graph'),
                        dcc.Tab(label='Analysis', value='tab-2-example-graph'),]
        )
    ]+[
    html.Div(id='tabs-content-example-graph')
    ]
    )


@app.callback(Output('tabs-content-example-graph', 'children'),
              Input('tabs-example-graph', 'value'))
def render_content(tab):
    print("render_content", tab)
    if tab == 'tab-1-example-graph':
        return html.Div(processing.layout)

    elif tab == 'tab-2-example-graph':
        return html.Div([
            html.H3('Tab content 2'),
            dcc.Graph(
                id='graph-2-tabs-dcc',
                figure={
                    'data': [{
                        'x': [1, 2, 3],
                        'y': [5, 10, 6],
                        'type': 'bar'
                    }]
                }
            )
        ])

if __name__ == '__main__':
    app.suppress_callback_exceptions = True
    app.run_server(debug=True)
