import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State

import dash_bootstrap_components as dbc

################################################################################
# The following modules contain their own layout and callbacks.
# See https://dash.plotly.com/urls for info about program structure.
import upload
import processing
import analysis

external_stylesheets = [dbc.themes.BOOTSTRAP]
# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    upload.layout+\
    [dcc.Tabs(id="tabs", value='tab-1',
              children=[dcc.Tab(label='Processing', value='tab-1'),
                        dcc.Tab(label='Analysis', value='tab-2',),]
        )
    ]+[
    html.Div(id='tabs-content')
    ]
    )


@app.callback(Output('tabs-content', 'children'),
              Input('tabs', 'value'),
    )
def render_content(tab):
    # print("render_content", tab, state)

    if tab == 'tab-1':
        return html.Div(processing.layout)

    elif tab == 'tab-2':
        return html.Div(analysis.layout)

if __name__ == '__main__':
    app.suppress_callback_exceptions = True
    app.run_server(debug=True)
