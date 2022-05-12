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

    ServersideOutput('data-store-file', 'data', arg_check=False),
    Output('data-store-small', 'data'),
    Output('data-store-register', 'data'),
    Output('upload-summary', 'children'),

    Input({'type': 'close-button', 'index': ALL}, 'n_clicks'),
    Input('upload-data', 'contents'),

    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),

    State('data-store-register', 'data'),
    State('data-store-file', 'data'),
    State('data-store-small', 'data'),
    State('upload-summary', 'children'),

    prevent_initial_call=True,
    )
def cb(close, list_of_contents, list_of_names, list_of_dates, register, data_file, small_data, cards):

    if small_data == None: small_data = {}
    if data_file == None: data_file = {}


    ctx = dash.callback_context
    close_button_trigger = 'close-button' in ctx.triggered[0]['prop_id']

    # remove dataset
    if close_button_trigger:
        button_id, _ = ctx.triggered[0]['prop_id'].split('.')
        button_id = json.loads(button_id)
        index_to_remove = button_id['index']

        # remove data from cards and data_file
        children = [child for child in cards
            if child['props']['id']['index'] != index_to_remove]
        del data_file[index_to_remove]

        print(close_button_trigger, cards, small_data, data_file)

        return data_file, None, register, children

    # file dropped
    if (not close_button_trigger) and (list_of_contents is not None):

        contents = []
        for c, n, d in zip(list_of_contents, list_of_names, list_of_dates):
            contents.append(parse_contents(c, n, d))

        updated_cards = cards
        for i, content in enumerate(contents):

            data_df, small_data = content
            filename = list_of_names[i]
            register, card_id = r_add_new_file(register)
            card = make_card(filename, data_df, card_id)
            updated_cards += [card]
            data_file[card_id] = data_df

        return data_file, None, register, updated_cards


def r_add_new_file(register):
    card_id = register.setdefault('new_id', 0)
    register['new_id'] += 1
    return register, card_id




################################################################################
# UTILS
def parse_contents(contents, filename, date):
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
    small_data = parse_small_data(data_df)

    return data_df, small_data


def parse_small_data(data_df):
    # parse small data
    small_data = {}
    stroke_id_list = list(set(data_df['stroke_id']))
    small_data['stroke_id_list'] = stroke_id_list
    small_data['num_strokes'] = len(stroke_id_list)
    segment_id_list = list(set(data_df['segment_id']))
    small_data['segment_id_list'] = segment_id_list
    small_data['num_segments'] = len(segment_id_list)

    # create map between stroke and segment ids, vice et versa
    tmp = data_df.groupby('stroke_id').apply(lambda x: list(set(x['segment_id'])))
    stroke_segment_map = {}
    segment_stroke_map = {}
    for i, row in tmp.iteritems():
        stroke_segment_map[i] = row
        for segment in row:
            segment_stroke_map[segment] = i
    small_data['stroke_segment_map'] = stroke_segment_map
    small_data['segment_stroke_map'] = segment_stroke_map

    return small_data


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
            # html.P("content", className="card-text"),
            dbc.Table([
                # Header
                html.Thead(html.Tr([html.Th(col) for col in ('key', 'value')])),
                # Body
                html.Tbody([html.Tr([html.Td(i) for i in row]) for row in table_data])
                ]),
            ]),
        ],
        id={'type': 'card', 'index': card_id},
        style={'width': '400px', 'display': 'inline-block'},
    )

    return card






# @callback(
#     # Output('upload-summary', 'children'),

#     Input('data-store-file', 'data'),
#     Input('data-store-register', 'data'),

#     Input({'type': 'close-button', 'index': ALL}, 'n_clicks'),
#     State({'type': 'close-button', 'index': ALL}, 'id'),

#     State('upload-summary', 'children'),
#     )
# def cb(data_df, register, a, b, cards):

#     ctx = dash.callback_context

#     print("make cards", register, ctx.triggered)

#     # on page load
#     if data_df is None:
#         return dash.no_update
#         # summary = html.Div([html.H5('No data, upload a file using the box above.')])
#         # return [summary]

#     # add a new file
#     prop_ids = [i['prop_id'] for i in ctx.triggered]
#     if any([(i in prop_ids) for i in ['data-store-file.data', 'data-store-register.data']]):

#         filename = register['current']
#         obj = [i for i in register['data'] if i['filename'] == filename][0]
#         n_files = len(register['data'])

#         card = make_card(obj['filename'], data_df, n_files)
#         new_cards = cards+[card]
#         return new_cards

#     else:
#         button_id, _ = ctx.triggered[0]["prop_id"].split(".")
#         print('ctx', ctx, button_id)

#         return []

#     # if any([(i in prop_ids) for i in ['data-store-file.data', 'data-store-register.data']]):
#     # remove a file






# @callback(
#     Input('data-store-register', 'data')
#     )
# def func(data):
#     print('data-store-register', data)


# @callback(
#     Output('upload-summary', 'children'),
#     Input({'type': 'close-button', 'index': ALL}, 'n_clicks'),
#     State({'type': 'close-button', 'index': ALL}, 'id'),
#     State('upload-summary', 'children'),
#     )
# def cb(a, b, children):
#     print(a, b)

#     ctx = dash.callback_context

#     if not ctx.triggered:
#         return dash.no_update

#     else:
#         button_id, _ = ctx.triggered[0]["prop_id"].split(".")

#         print('ctx', ctx, button_id)

#         button_id = json.loads(button_id)
#         index_to_remove = button_id["index"]
#         children = [
#             child
#             for child in children
#             if child["props"]["id"]["index"] != index_to_remove
#         ]

#         return children
