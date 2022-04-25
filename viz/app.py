

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
import plotly.graph_objs as go

@app.callback(Output('fig_all', 'figure'),
              Input('data-store', 'data'))
def update_graph(jsonified_cleaned_data):
    # print("update_graph", jsonified_cleaned_data)
    data = pd.read_json(jsonified_cleaned_data, orient='split')
    data.columns = [0, 'source', 'data']

    print('data', data.head())
    select = processing.select(data, source='/data')
    print('select', select)

    data_df = processing.format_data(select)

    print(data_df.head())

    fig = go.Figure()

    # hovertext = np.c_[data['n_stroke'].index, data['n_stroke'].values]
    scatter = go.Scatter(x=data_df['x'], y=data_df['y'], mode='markers',)
                         # hovertext=hovertext,
                         # opacity=.1, marker={'color':'black'},)
    fig.add_trace(scatter)
    fig.update_layout(
        autosize=False,
        width=1000,
        height=1000,
    )
    return fig



    return [a]


@app.callback(Output('output-data-test', 'children'),
              Input('data-store', 'data'))
def update_graph(jsonified_cleaned_data):
    print("update_graph", jsonified_cleaned_data)
    dff = pd.read_json(jsonified_cleaned_data, orient='split')

    a = html.Div([
        html.H5(dff.shape[0]),
        ])

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

        # print(last_child)

        return [last_child[0]], last_child[1]

if __name__ == '__main__':
    app.run_server(debug=True)
