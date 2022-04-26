

import dash
# from dash.dependencies import Input, Output, State
from dash import html

import upload
import processing

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    upload.layout+processing.layout
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

# @app.callback(Output('output-data-test', 'children'),
#               Input('data-store', 'data'))
# def update_graph(jsonified_cleaned_data):
#     if jsonified_cleaned_data is not None:
#         print("update_graph", jsonified_cleaned_data)
#         dff = pd.read_json(jsonified_cleaned_data, orient='split')

#         a = html.Div([
#             html.H5(dff.shape[0]),
#             ])

#     else:
#         a = html.Div([])

#     return [a]

if __name__ == '__main__':
    app.run_server(debug=True)
