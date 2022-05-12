import logging

from dash_extensions.enrich import Output, Input, State
from dash_extensions.enrich import html, dcc
from dash_extensions.enrich import DashProxy, ServersideOutputTransform, NoOutputTransform

import dash_bootstrap_components as dbc

# The following modules contain their own layout and callback definitions.
# See https://dash.plotly.com/urls for info about program structure.
import upload
import processing
import analysis


logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

FONT_AWESOME = "https://use.fontawesome.com/releases/v5.13.0/css/all.css"
external_stylesheets = [dbc.themes.BOOTSTRAP, FONT_AWESOME]
# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = DashProxy(__name__, external_stylesheets=external_stylesheets,
                          transforms=[ServersideOutputTransform(), NoOutputTransform()])

register = {
    'new_id' : 0,
    'active' : [],
}


app.layout = html.Div(
    # DATASTORES
    [
    dcc.Store(id='data-store-register', data=register),
    dcc.Store(id='data-store-file'),
    dcc.Store(id='data-store-fig-all'),
    dcc.Store(id='data-store-sk'),
    dcc.Store(id='data-store-embedding'),
    dcc.Store(id='data-store-small'),
    ]+\

    # HEADER
    upload.layout+\

    # TABS
    [
    dcc.Tabs(id='tabs', value='tab-1',
             children=[dcc.Tab(label='Processing', value='tab-1', children=processing.layout),
                       dcc.Tab(label='Analysis', value='tab-2', children=analysis.layout),
                ]
        )
    ]
)

# complement Tabs - toggle Tab's visibility
@app.callback(Output('processing-layout', component_property='style'),
              Input('tabs', 'value'),)
def cb(value):
    if value == 'tab-1': return {'display': 'block'}
    if value == 'tab-2': return {'display': 'none'}
@app.callback(Output('analysis-layout', component_property='style'),
              Input('tabs', 'value'),)
def cb(value):
    if value == 'tab-1': return {'display': 'none'}
    if value == 'tab-2': return {'display': 'block'}


if __name__ == '__main__':
    app.suppress_callback_exceptions = True
    app.run_server(debug=True, port=8050, host='127.0.0.1')
