

import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html

import upload
import processing

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    upload.components+processing.components
)

# @app.callback(Output('data-store', 'data'),
#               Input('submit-val', 'n_clicks'),
#               # State('input-on-submit', 'value'))
#               )
# def process_data(n_clicks):

#     print("process_data", n_clicks)

#     # return 'The input value was "{}" and the button has been clicked {} times'.format(
#     #     value,
#     #     n_clicks
#     # )


import pandas as pd

@app.callback(Output('output-data-test', 'children'),
              Input('data-store', 'data'))
def update_graph(jsonified_cleaned_data):
    if jsonified_cleaned_data is not None:
        print("update_graph", jsonified_cleaned_data)
        dff = pd.read_json(jsonified_cleaned_data, orient='split')

        a = html.Div([
            html.H5(dff.shape[0]),
            ])

    else:
        a = html.Div([])

    return [a]

@app.callback(Output('output-data-upload', 'children'),
              Output('data-store', 'data'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def upload_data(list_of_contents, list_of_names, list_of_dates):
    print("upload_data", list_of_contents, list_of_names, list_of_dates)
    if list_of_contents is not None:
        children = [
            upload.parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]

        last_child = children[0]
        return [last_child[0]], last_child[1]
    else:
        empty = html.Div([html.H5("no data.")])
        return [empty], None

if __name__ == '__main__':
    app.run_server(debug=True)
