import base64
import datetime
import io

from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash import callback
from dash import dash_table

import numpy as np
import pandas as pd

from utils import format_from_json, format_from_df


################################################################################
# LAYOUT
layout = [
    # io
    dcc.Upload(
        id='upload-data',
        children=html.Div(['Drag and Drop or ',html.A('Select Files')]),
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
    html.Div(id='upload-summary'),
    html.Hr(),
    ]


################################################################################
# CALLBACK
@callback(
    Output('upload-summary', 'children'),
    Output('data-store-file', 'data'),
    Output('data-store-small', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    )
def upload_data(list_of_contents, list_of_names, list_of_dates):
    # print("upload_data", list_of_contents, list_of_names, list_of_dates)
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)
            ]
        a, b, c = children[0]
        return [a], b, c
    else:
        summary = html.Div([html.H5("no data.")])
        return [summary], None, None


################################################################################
# UTILS
def parse_contents(contents, filename, date):

    print("parse content")

    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
            df.columns = [0, 'source', 'data']
    except Exception as e:
        print(e)
        return html.Div([
            """There was an error processing this file. Use pandas dataframes
            saved to disk as csv."""
        ])

    jsonified_cleaned_data = df.to_json(date_format='iso', orient='split')

    data_df = format_from_df(df, source='/data')
    small_data = {}
    stroke_id_list = list(set(data_df['stroke_id']))
    small_data['stroke_id_list'] = stroke_id_list
    small_data['num_strokes'] = len(stroke_id_list)

    # table to sum up file upload
    a, b = min(stroke_id_list), max(stroke_id_list),
    table_data = [
    ['filename', filename],
    ['lines', str(df.shape[0])],
    ['stroke_id', str(a)+' ... '+str(b)],
    ]
    html_table = html.Div([
        html.Table([
            # Header
            html.Thead(html.Tr([html.Th(col) for col in ('key', 'value')])),
            # Body
            html.Tbody([html.Tr([html.Td(i) for i in row]) for row in table_data])
            ])
        ])

    return html_table, jsonified_cleaned_data, small_data




