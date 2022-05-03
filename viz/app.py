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

import logging
logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

## Diskcache
import diskcache
from dash.long_callback import DiskcacheLongCallbackManager

cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)


# external_stylesheets = [dbc.themes.BOOTSTRAP]
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                long_callback_manager=long_callback_manager)

app.layout = html.Div(
    # DATASTORES
    [
    dcc.Store(id='data-store-fig_all'),
    dcc.Store(id='data-store-sk'),
    dcc.Store(id='data-store-file'),
    dcc.Store(id='data-store-embedding'),
    dcc.Store(id='data-store-small'),
    ]+\

    upload.layout+\
    [dcc.Tabs(id="tabs", value='tab-1',
              children=[dcc.Tab(label='Processing', value='tab-1', children=processing.layout),
                        dcc.Tab(label='Analysis', value='tab-2', children=analysis.layout),
                    ]
        )
    ]
    )

@app.callback(
    Output('processing-layout', component_property='style'),
    Input('tabs', 'value'),
    )
def visibility_layout(value):
    if value == 'tab-1':
        return {'display': 'block'}
    if value == 'tab-2':
        return {'display': 'none'}

@app.callback(
    Output('analysis-layout', component_property='style'),
    Input('tabs', 'value'),
    )
def visibility_analysis(value):
    if value == 'tab-1':
        return {'display': 'none'}
    if value == 'tab-2':
        return {'display': 'block'}



if __name__ == '__main__':
    app.suppress_callback_exceptions = True
    app.run_server(debug=True)
