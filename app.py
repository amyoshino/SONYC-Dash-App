# -*- coding: utf-8 -*-
import dash
from dash.dependencies import Input, Output, State, Event
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
import plotly
from plotly import graph_objs as go
from plotly.graph_objs import *
from flask import Flask
import pandas as pd
import numpy as np
import os

app = dash.Dash(__name__)
server = app.server

# API keys and datasets
mapbox_access_token = 'pk.eyJ1IjoiYW15b3NoaW5vIiwiYSI6ImNqOXA3dGF2bDJhMjMyd2xnNTJqdXFxc2sifQ.9SoIXAYOZ8qfTiHaw6rWmg'
map_data = pd.read_csv('SONYC_Dataset.csv')
map_data.drop("Unnamed: 0", 1, inplace=True)

# Boostrap CSS.
app.css.append_css({"external_url": "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css"})
# Extra Dash styling.
app.css.append_css({"external_url": 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
# JQuery is required for Bootstrap.
app.scripts.append_script({"external_url": "https://code.jquery.com/jquery-3.2.1.min.js"})
# Bootstrap Javascript.
app.scripts.append_script({"external_url": "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"})

# Components style
def color_scale(map_data):
    color = []
    max_score = map_data['Need Score'].max()
    min_score = map_data['Need Score'].min()
    for row in map_data['Need Score']:
        color.append((row - min_score)/(max_score - min_score))
    return color

def gen_map(map_data):
    # groupby returns a dictionary mapping the values of the first field
    # 'classification' onto a list of record dictionaries with that
    # classification value.
    return {
        "data": [
                {
                    "type": "scattermapbox",
                    "lat": list(map_data['Latitude']),
                    "lon": list(map_data['Longitude']),
                    "text": list(map_data['Need Score']),
                    "mode": "markers",
                    "name": list(map_data['Location Name']),
                    "marker": {
                        "size": 6,
                        "opacity": 1.0,
                        "color": color_scale(map_data),
                        "colorscale":[[0, "#26EC04"],
                                    [0.50, "#FBC901"],
                                    [1.0, "#FD0101"]]
                    }
                }
            ],
        "layout": {
            "title": '''
                Each dot is an NYC Middle School eligible for SONYC funding
            ''',
            "height": 700,
            "width": 950,
            "hovermode": "closest",
            "mapbox": {
                "accesstoken": mapbox_access_token,
                "bearing": 0,
                "center": {
                    "lat": 40.7342,
                    "lon": -73.91251
                },
                "pitch": 0,
                "zoom": 10,
                "style": "light"
            }
        }
    }


# Layout
app.layout = html.Div([
    # Title - Row
    html.Div(
        [
            html.H1(
                'SONYC Sitting Model',
                style={'font-family': 'Helvetica',
                       "text-align": "right",
                       "margin-top": "25",
                       "margin-bottom": "0",
                       "font-size": "280%"},
                className='col-md-8',
            ),
            html.Img(
                src="http://static1.squarespace.com/static/546fb494e4b08c59a7102fbc/t/591e105a6a496334b96b8e47/1497495757314/.png",
                className='col-md-2',
                style={
                    'height': '100',
                    'width': '135',
                    'float': 'right',
                    'position': 'float',
                    "margin-right": "20"
                },
            ),
            html.P(
                'A decision support system for DYCD/DOE\'s 2015 SONYC expansion.',
                style={'font-family': 'Helvetica',
                       "text-align": "center",
                       "font-size": "120%"},
                className='col-md-12',
            ),
        ],
        className='row'
    ),

    # Map + table
    html.Div(
        [
            html.Div(
                [
                    dcc.Graph(id='map-graph',
                              style={'font-family': 'Helvetica',
                                    "text-align": "center",
                                    "font-size": "30%"})
                ], className = "col-md-7"
            ),
            html.Div(
                [
                    dt.DataTable(
                        rows=map_data.ix[:, :-2].to_dict('records'),
                        columns=map_data.ix[:, :-2].columns,
                        row_selectable=True,
                        filterable=True,
                        sortable=True,
                        selected_row_indices=[],
                        id='datatable'),
                ],
                style={'width': '30%', "font-size": 11, "height": 500,
                    "margin-top": 0, "padding-top": 100, "padding-left": 100},
                className="col-md-5"
            )
        ], className="row"
    ),
    html.Div(
        [
            html.Div([dcc.Graph(id="histogram")],
                style={"padding-top": "-1500"},
                className="col-md-12")
        ]
    )
], style={"padding-top": "20px"})

@app.callback(
    Output('datatable', 'selected_row_indices'),
    [Input('histogram', 'clickData')],
    [State('datatable', 'selected_row_indices')])
def update_selected_row_indices(clickData, selected_row_indices):
    if clickData:
        for point in clickData['points']:
            if point['pointNumber'] in selected_row_indices:
                selected_row_indices.remove(point['pointNumber'])
            else:
                selected_row_indices.append(point['pointNumber'])
    return selected_row_indices


@app.callback(
    Output('histogram', 'figure'),
    [Input('datatable', 'rows'),
     Input('datatable', 'selected_row_indices')])
def update_figure(rows, selected_row_indices):
    dff = pd.DataFrame(rows)
    fig = plotly.tools.make_subplots(
        rows=1, cols=1,
        subplot_titles=('School Need Score',),
        shared_xaxes=True)
    marker = {'color': color_scale(dff),
              "colorscale":[[0, "#26EC04"],
                            [0.50, "#FBC901"],
                            [1.0, "#FD0101"]]}
    for i in (selected_row_indices or []):
        marker['color'][i] = '#1500FA'
    fig.append_trace({
        'x': dff['Location Name'],
        'y': dff['Need Score'],
        'type': 'bar',
        'marker': marker
    }, 1, 1)
    fig['layout']['showlegend'] = False
    fig['layout']['height'] = 500
    fig['layout']['margin'] = {
        'l': 40,
        'r': 10,
        't': 60,
        'b': 200
    }
    fig['layout']['yaxis1']['type'] = 'linear'
    return fig

@app.callback(
    Output('map-graph', 'figure'),
    [Input('datatable', 'rows'),
     Input('datatable', 'selected_row_indices')])
def map_selection(rows, selected_row_indices):
    temp_df = map_data.ix[selected_row_indices, :]
    if len(selected_row_indices) == 0:
        return gen_map(map_data)
    return gen_map(temp_df)


if __name__ == '__main__':
    app.run_server(debug=True)
