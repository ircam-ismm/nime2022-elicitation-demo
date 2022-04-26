import dash
from dash import html

################################################################################
# The following modules contain their own layout and callbacks.
# See https://dash.plotly.com/urls for info about program structure.
import upload
import processing

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    upload.layout+processing.layout
)

if __name__ == '__main__':
    app.run_server(debug=True)
