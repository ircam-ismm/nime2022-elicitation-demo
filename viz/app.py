import logging

from dash_extensions.enrich import Output, Input, State
from dash_extensions.enrich import html, dcc
from dash_extensions.enrich import DashProxy, ServersideOutputTransform, NoOutputTransform

import dash_bootstrap_components as dbc

# The following modules contain their own layout and callback definitions.
# See https://dash.plotly.com/urls for info about program structure.
import upload
import tab1, tab2, tab3


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

tab1 = html.Div(id='tab-1', children=tab1.layout, )
tab2 = html.Div(id='tab-2', children=tab2.layout, )
tab3 = html.Div(id='tab-3', children=tab3.layout, )

app.layout = html.Div(
    # DATASTORES
    [
    dcc.Store(id='data-store-register', data=register),
    dcc.Store(id='data-store-dfs'),
    dcc.Store(id='data-store-fig-all'),
    dcc.Store(id='data-store-sk'),
    dcc.Store(id='data-store-embedding'),
    dcc.Store(id='data-store-props'),
    ]+\

    # UPLOAD INTERFACE
    upload.layout+\

    # TABS
    [
    dcc.Tabs(id='tabs', value='tab-1',
             children=[dcc.Tab(label='All data', value='tab-1', children=tab1),
                       dcc.Tab(label='Single strokes', value='tab-2', children=tab2),
                       dcc.Tab(label='Embedding', value='tab-3', children=tab3),
                ]
        )
    ]
)

# complement Tabs - toggle Tab's visibility
@app.callback(
    Output('tab-1', component_property='style'),
    Output('tab-2', component_property='style'),
    Output('tab-3', component_property='style'),
    Input('tabs', 'value'),
    )
def cb(value):
    res = [{'display': 'block' if tab == value else 'none'}
            for tab in ('tab-1', 'tab-2', 'tab-3')]
    return res[0], res[1], res[2]


if __name__ == '__main__':
    app.suppress_callback_exceptions = True
    app.run_server(debug=True, port=8050, host='127.0.0.1')
