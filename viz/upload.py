import base64
import datetime
import io

from dash_extensions.enrich import Output, Input, State, ALL, MATCH
from dash_extensions.enrich import html, dcc
from dash_extensions.enrich import DashProxy, ServersideOutput
from dash_extensions.enrich import callback
import dash_bootstrap_components as dbc
import dash

import numpy as np
import pandas as pd

from utils import format_from_json, format_from_df


################################################################################
# LAYOUT
layout = [
    # io
    dcc.Upload(
        id='upload-data',
        children=html.Div(['Drag and Drop or ',html.A('Select File(s)')]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    # info
    html.Div(id='upload-summary', children=[]),
    html.Hr(),
    ]

import json
################################################################################
# CALLBACK
# https://www.dash-extensions.com/transforms/serverside-output-transform
@callback(

    ServersideOutput('data-store-dfs', 'data', arg_check=False),
    Output('data-store-props', 'data'),
    Output('data-store-register', 'data'),
    Output('upload-summary', 'children'),

    Input({'type': 'close-button', 'index': ALL}, 'n_clicks'),
    Input({'type': 'check-button', 'index': ALL}, 'value'),
    Input({'type': 'check-button', 'index': ALL}, 'id'),
    Input('upload-data', 'contents'),

    State('upload-data', 'filename'),
    # State('upload-data', 'last_modified'),

    State('data-store-register', 'data'),
    State('data-store-dfs', 'data'),
    State('data-store-props', 'data'),
    State('upload-summary', 'children'),

    prevent_initial_call=True,
    )
def cb(
    close, check_values, check_ids, list_of_contents,
    list_of_names, register, dfs, props, cards
    ):

    if props == None: props = {}
    if dfs == None: dfs = {}

    ctx = dash.callback_context
    upload_trigger = 'upload-data' in ctx.triggered[0]['prop_id']
    check_button_trigger = 'check-button' in ctx.triggered[0]['prop_id']
    close_button_trigger = 'close-button' in ctx.triggered[0]['prop_id']

    # de/activate dataset
    if check_button_trigger:
        register['active'] = []
        for check_value, check_id in zip(check_values, check_ids):
            if check_value: register['active'] += [check_id['index']]

        return dfs, None, register, cards

    # remove dataset
    if close_button_trigger:
        button_id, _ = ctx.triggered[0]['prop_id'].split('.')
        button_id = json.loads(button_id)
        index_to_remove = button_id['index']

        # remove data from cards and dfs
        cards = [card for card in cards if card['props']['id']['index'] != index_to_remove]
        del dfs[index_to_remove]
        register['active'] = [i for i in register['active'] if i != index_to_remove]

        return dfs, None, register, cards

    # add dataset
    if upload_trigger:

        for content, filename in zip(list_of_contents, list_of_names):
            data_df, props = parse_contents(content, filename)

            register, card_id = r_add_new_file(register)
            card = make_card(filename, data_df, card_id)
            cards += [card]

            dfs[card_id] = data_df

        return dfs, None, register, cards


def r_add_new_file(register):
    card_id = register['new_id']
    register['new_id'] += 1
    register['active'] += [card_id]
    return register, card_id


################################################################################
# UTILS
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        df.columns = [0, 'source', 'data']
    except Exception as e:
        print(e)
        error_msg = """There was an error processing this file. Use pandas dataframes
        saved to disk as csv."""
        return html.Div([error_msg])

    data_df = format_from_df(df, source='/data')
    props = parse_data_properties(data_df)

    return data_df, props


def make_card(filename, data_df, card_id):
    stroke_id_list = list(set(data_df['stroke_id']))
    segment_id_list = list(set(data_df['segment_id']))

    a, b = min(stroke_id_list), max(stroke_id_list)
    c, d = min(segment_id_list), max(segment_id_list)
    table_data = [
    ['filename', filename],
    ['card_id', card_id],
    ['lines', str(data_df.shape[0])],
    ['stroke_id', str(a)+' ... '+str(b)],
    ['segment_id', str(c)+' ... '+str(d)],
    ]

    card = dbc.Card([
        dbc.CardHeader([
            dcc.Checklist(
                id={'type': 'check-button', 'index': card_id},
                options=[{'label': '', 'value': 'on'}],
                value=['on'],
                style={'display': 'inline-block'}
                ),
            dbc.Button(
                id={'type': 'close-button', 'index': card_id},
                className='btn-close',
                style={'display': 'inline-block', 'float': 'right'})
            ]),
        dbc.CardBody([
            dbc.Table([
                html.Tbody([html.Tr([html.Td(i) for i in row]) for row in table_data])
                ]),
            ]),
        ],
        id={'type': 'card', 'index': card_id},
        style={'width': '400px', 'display': 'inline-block'},
    )

    return card


def parse_data_properties(data_df):
    props = {}
    stroke_id_list = list(set(data_df['stroke_id']))
    props['stroke_id_list'] = stroke_id_list
    props['num_strokes'] = len(stroke_id_list)
    segment_id_list = list(set(data_df['segment_id']))
    props['segment_id_list'] = segment_id_list
    props['num_segments'] = len(segment_id_list)

    # create map between stroke and segment ids, vice et versa
    tmp = data_df.groupby('stroke_id').apply(lambda x: list(set(x['segment_id'])))
    stroke_segment_map = {}
    segment_stroke_map = {}
    for i, row in tmp.iteritems():
        stroke_segment_map[i] = row
        for segment in row:
            segment_stroke_map[segment] = i
    props['stroke_segment_map'] = stroke_segment_map
    props['segment_stroke_map'] = segment_stroke_map

    return props


