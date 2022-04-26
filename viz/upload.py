import base64
import datetime
import io

from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash import callback
from dash import dash_table

import pandas as pd


################################################################################
# LAYOUT
layout = [
    dcc.Store(id='data-store'),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
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
    html.Div(id='output-data-upload'),
    # html.Button('Submit', id='submit-val', n_clicks=0),
    html.Hr(),
    # html.Div(id='output-data-test'),

    ]



################################################################################
# CALLBACK

@callback(
    Output('output-data-upload', 'children'),
    Output('data-store', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    )
def upload_data(list_of_contents, list_of_names, list_of_dates):
    print("upload_data", list_of_contents, list_of_names, list_of_dates)
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]

        last_child = children[0]
        return [last_child[0]], last_child[1]
    else:
        empty = html.Div([html.H5("no data.")])
        return [empty], None


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    table_data = [
    ['filename', filename],
    ['lines', str(df.shape[0])],
    ['stroke_id', '86 ... 89'],
    ]


    a = html.Div([
        # html.H5(filename),
        # html.H6(datetime.datetime.fromtimestamp(date)),
        # html.H6(str(df.shape[0])+" lines"),

        html.Table(
        # Header
            [html.Thead(html.Tr([html.Th(col) for col in ('key', 'value')])) ] +
        # Body
            [html.Tbody(
            [html.Tr([html.Td(i) for i in row]) for row in table_data]
            )
            ]
        )

        # dash_table.DataTable()
        #     df.to_dict('records'),
        #     [{'name': i, 'id': i} for i in df.columns]
        # ),

        # html.Hr(),  # horizontal line

        # # For debugging, display the raw contents provided by the web browser
        # html.Div('Raw Content'),
        # html.Pre(contents[0:200] + '...', style={
        #     'whiteSpace': 'pre-wrap',
        #     'wordBreak': 'break-all'
        # })
    ])

    b = df.to_json(date_format='iso', orient='split')

    return a, b