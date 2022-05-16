import numpy as np

from dash_extensions.enrich import Output, Input, State
from dash_extensions.enrich import html, dcc
from dash_extensions.enrich import callback
import dash_bootstrap_components as dbc
import dash_daq as daq

################################################################################
# LAYOUT
layout = [
    html.Div([
        html.Div([daq.NumericInput(id='button-card-id', label='card:', value=-1, min=0, max=1e3),],
                 className='col-1'),
        html.Div([daq.NumericInput(id='button-stroke-id', label='stroke:', value=-1, min=0, max=1e3),],
                 className='col-1'),
        html.Div([daq.NumericInput(id='button-segment-id', label='segment:',value=-1, min=0, max=1e3),],
                 className='col-1'),
        ],
    className='row'),

    html.Div([
        dcc.Graph(id='fig-card',),
        ],
        style={'width': '49%', 'display': 'inline-block'},
        ),

    html.Div([
        dbc.Col([
            dcc.Graph(id='fig-stroke',),
            dcc.Graph(id='fig-speed',),
            ]),
        ],
        style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'},
    ),
]


################################################################################
# CALLBACKS

@callback(
    Output('button-card-id', 'value'),
    Input('data-store-register', 'data'),
    State('data-store-props', 'data'),
    prevent_initial_call=True,
)
def cb(register, props):
    active = register.get('active', None)
    active = active[0] if active else active

    return active


# @callback(
#     Output('button-card-id', 'value'),
#     Output('button-card-id', 'min'),
#     Output('button-card-id', 'max'),
#     Output('button-stroke-id', 'min'),
#     Output('button-stroke-id', 'max'),
#     Output('button-segment-id', 'min'),
#     Output('button-segment-id', 'max'),
#     Input('data-store-register', 'data'),
#     State('data-store-props', 'data'),
#     prevent_initial_call=True
#     )
# def cb(register, props):
#     """Set the range for stroke selection based on stroke ids in the data.
#     """
#     print("update buttons", register, props)
#     for active in register['active']:
#         card_props = props[str(active)]

#         stroke_id_list = np.array(card_props['stroke_id_list'])
#         segment_id_list = np.array(card_props['segment_id_list'])

    # stroke_id_list = np.array(small_data['stroke_id_list'])

    # return stroke_id_list.min(), stroke_id_list.max()

# @callback(
#     Output('button-segment-id', 'min'),
#     Output('button-segment-id', 'max'),
#     Input('data-store-props', 'data'),
#     prevent_initial_call=True
#     )
# def cb(small_data):
#     """Set the range for segment selection based on segment ids in the data.
#     """
#     segment_id_list = np.array(small_data['segment_id_list'])
#     return segment_id_list.min(), segment_id_list.max()

# @callback(
#     Output('button-stroke-id', 'value'),
#     Input('button-segment-id', 'value'),
#     Input('data-store-props', 'data'),
#     prevent_initial_call=True
#     )
# def cb(numinput, small_data):
#     """Set the stroke id from a segment id selection or on page load.
#     """
#     if numinput != -1:
#         segment_stroke_map = small_data['segment_stroke_map']
#         stroke_id = segment_stroke_map[str(numinput)]
#     else:
#         stroke_id_list = np.array(small_data['stroke_id_list'])
#         stroke_id = stroke_id_list.min()

#     return stroke_id



# @callback(
#     Output('fig-all', 'figure'),
#     Input('data-store-register', 'data'),
#     # Input('button-stroke-id', 'value'),
#     State('data-store-dfs', 'data'),
#     # State('data-store-fig-all', 'data'),
#     # State('data-store-sk', 'data'),
#     prevent_initial_call=True,
#     )
# def cb(register, dfs):
#     """Update the scatter with all points with a specific stroke.
#     """
#     data_df = select_active_dfs(dfs, register)

#     # if sk_data is None:
#     #     return dash.no_update

#     # mms = mms_from_json(sk_data)
#     # stroke_df = select(df, stroke_id=numinput)

#     # if stroke_df.shape[0] > 0:
#     #     p_scaled = mms.transform(stroke_df['p'].values.reshape(-1,1)).reshape(-1)
#     #     fig_b = px.scatter(data_frame=stroke_df, x='x', y='y', custom_data=['stroke_id', 'p'], opacity=1)
#     #     fig_b.update_traces(marker=dict(size=p_scaled))

#     if data_df.shape[0] > 0:
#         fig = px.scatter(
#             data_frame=data_df, x='x', y='y', color='card_id',
#             custom_data=['card_id', 'stroke_id', 'p'], opacity=0.3,
#             color_discrete_sequence=px.colors.qualitative.T10,
#             )
#         fig = go.Figure(data=fig.data)
#     else:
#         fig = go.Figure()

#     fig.update_traces(
#         hovertemplate="card:%{customdata[0]} <br>stroke:%{customdata[1]} <br>p:%{customdata[2]:.2f}<extra></extra>"
#         )
#     fig.layout.update(
#         title='Position (x, y) of all touch points for cards {}'.format(register['active']),# with stroke {} in blue.'.format(numinput),
#         xaxis_title='x-position',
#         yaxis_title='y-position',
#         showlegend=False,
#         autosize=False,
#         width=1000,
#         height=1000,)
#     return fig


# @callback(
#     Output('data-store-sk', 'data'),
#     ServersideOutput('data-store-fig-all', 'data'),
#     Input('data-store-register', 'data'),
#     State('data-store-dfs', 'data'),
#     prevent_initial_call=True,
#     )
# def cb(register, dfs):
#     """Create a scatter with all points.
#     """

#     data_sk = {}
#     data_figall = {}

#     for active in register['active']:
#         df = dfs[active]

#         mms = skprep.MinMaxScaler(feature_range=(10, 80))
#         p_scaled = mms.fit_transform(df['p'].values.reshape(-1,1)).reshape(-1)

#         fig = px.scatter(data_frame=df, x='x', y='y', custom_data=['stroke_id', 'p'], opacity=0.05,)
#         fig.update_traces(marker=dict(color='black', size=p_scaled))

#         data_figall[active] = fig
#         data_sk[active] = mms_to_json(mms)

#     return data_sk, data_figall



# @callback(
#     Output('fig-trace', 'figure'),
#     Input('fig-speed', 'relayoutData'),
#     Input('data-store-dfs', 'data'),
#     Input('data-store-sk', 'data'),
#     Input('button-stroke-id', 'value'),
#     prevent_initial_call=True,
#     )
# def cb(layout_data, df, sk_data, numinput):
#     """Display a single stroke (x, y) with its segments coloured individually.
#     """
#     if sk_data is None:
#         return dash.no_update

#     if layout_data is not None:
#         tmin = layout_data.get('xaxis.range[0]', None)
#         tmax = layout_data.get('xaxis.range[1]', None)

#     stroke_i = select(df, stroke_id=numinput).copy()

#     if stroke_i.shape[0] > 0:
#         mms = mms_from_json(sk_data)
#         stroke_i['size'] = mms.transform(stroke_i['p'].values.reshape(-1,1)).reshape(-1)
#         stroke_i['color'] = ['rgba'+str(tab10[int(i)%10]+(1,)) for i in stroke_i['segment_id']]

#         if (tmin and tmax):
#             subset = stroke_i[(stroke_i['ts'] > tmin) & (stroke_i['ts'] < tmax)]
#         else:
#             subset = stroke_i

#         fig = px.scatter(
#                 data_frame=subset, x='x', y='y', color='color', size='size',
#                 custom_data=['segment_id'], color_discrete_map='identity',
#                 )

#     fig = go.Figure(data=fig.data)
#     fig.update_traces(
#         hovertemplate="ID:%{customdata}<extra></extra>"
#         )
#     fig.layout.update(
#         title='Position (x, y) of stroke {}<br>with segments coloured individually.'.format(numinput),
#         xaxis_title='x-position',
#         yaxis_title='y-position',
#         showlegend=False,
#         autosize=False,
#         width=500,
#         height=500,
#     )

#     return fig

# @callback(
#     Output('fig-speed', 'figure'),
#     Input('data-store-dfs', 'data'),
#     Input('button-stroke-id', 'value'),
#     prevent_initial_call=True,
#     )
# def cb(df, numinput):
#     """Display a single stroke (ts, s) with its segments coloured individually.
#     """
#     if df is None:
#         return dash.no_update

#     stroke_i = select(df, stroke_id=numinput).copy()

#     if stroke_i.shape[0] > 0:
#         stroke_i['color'] = ['rgba'+str(tab10[int(i)%10]+(1,)) for i in stroke_i['segment_id']]

#         fig = px.scatter(
#                 data_frame=stroke_i, x='ts', y='s', color='color',
#                 custom_data=['segment_id'], color_discrete_map='identity',
#                 )

#     fig = go.Figure(data=fig.data)
#     fig.update_traces(
#         hovertemplate="ID:%{customdata} <br>t:%{x} <br>s:%{y:.2f}<extra></extra>"
#         )
#     fig.update_layout(
#         title='Feature profile of stroke {}<br>with segments coloured individually.'.format(numinput),
#         xaxis_title='timestamp [ms]',
#         yaxis_title='speed',
#         showlegend=False,
#         autosize=False,
#         width=500,
#         height=500,
#         )

#     return fig
