import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input
import plotly.graph_objects as go
import pandas as pd

from server import app
from backend.models import Date, HoursInDay, VisitsCountByHour,\
    Devices, PageViewsByDevices, TrafficSource,\
    VisitsCountByTrafficSource, RegionsMap


d = Date()
h = HoursInDay()
v = VisitsCountByHour()
pvd = PageViewsByDevices()
vcts = VisitsCountByTrafficSource()
rm = RegionsMap()

dander_alert = dbc.Alert('Select a date', color='danger', dismissable=True)


def get_success_alert(date: str) -> dbc.Alert:
    return dbc.Alert(f'You have chosen a date: {date}',
                     color='success', dismissable=True)


def bar_figure_visits_count_by_traffic_source(date: str) -> go.Figure:
    visits_count_by_traffic_source = vcts.get_data_from_joining_models(
        date=date,
        select_name_column='visits_count',
        order_name_column='traffic_source_id',
        model=TrafficSource
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=[row[0] for row in visits_count_by_traffic_source],
            y=[row[1] for row in visits_count_by_traffic_source]
        )
    )

    fig.update_layout(
        title_font_size=25, title_x=0.5,
        title_text='visits_count_by_traffic_source'
    )
    return fig


def pie_figure_page_views_by_devices(date: str) -> (html.H1, go.Figure):
    page_views_by_devices = pvd.get_data_from_joining_models(
        date=date,
        select_name_column='page_views',
        order_name_column='device_id',
        model=Devices
    )

    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=[row[0] for row in page_views_by_devices],
        values=[row[1] for row in page_views_by_devices]
    ))

    fig.update_traces(
        hoverinfo='label+percent', textinfo='value',
        textfont_size=20, marker=dict(line=dict(color='#000000', width=2)))

    fig.update_layout(
        title_font_size=25, title_x=0.5,
        title_text='page_views_by_devices'
    )
    sum_visits = sum([row[1] for row in page_views_by_devices])
    count_visits_string = html.H1(f'Count visits: {sum_visits}')
    return count_visits_string, fig


def scatter_figure_visits_count_by_hour(date: str) -> go.Figure:
    visits_count_by_every_hour = v.get_data_from_joining_models(
        date=date,
        select_name_column='visits_count_by_hour',
        order_name_column='hour_id'
    )

    values_x_axis = [i for i in range(len(h.hours))]
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=values_x_axis,
        y=visits_count_by_every_hour,
        mode='markers',
    ))

    fig.update_layout(
        xaxis=dict(
            tickvals=values_x_axis,
            ticktext=h.hours
        ),
        xaxis_title=f'Hours of {date}',
        yaxis_title='Visits',
        title_font_size=25, title_x=0.5,
        title_text='visits_count_by_hour'
    )
    return fig


def scattergeo_figure_regions_map(date: str) -> go.Figure:
    mapping_data = rm.get_list_with_city_name_code_country_coord(date=date)

    text = 'City: {0}<br>Country index: {1}' \
           '<br>Count visitors: {2}'

    df = pd.DataFrame({
        'text': [text.format(row[0], row[1], row[4]) if row[1]
                 else text.format(row[0], 'not defined', row[4])
                 for row in mapping_data],
        'lat': [row[2] for row in mapping_data],
        'long': [row[3] for row in mapping_data],
        'users_count': [row[4] for row in mapping_data],
    })

    fig = go.Figure()

    limits = [
        [1, 2, 3], [3, 6, 2.75], [7, 10, 2.25],
        [11, 15, 2], [16, 3000, 1.5]
    ]
    colors = ['royalblue', 'crimson', 'lightseagreen', 'orange', 'black']

    for i, lim in enumerate(limits):
        if lim != limits[-1]:
            name = f'{lim[0]} - {lim[1]}'
            df_sub = df.query('@lim[0] <= users_count <= @lim[1]')
        else:
            name = f'{lim[0]} <'
            df_sub = df[df['users_count'] >= lim[0]]

        fig.add_trace(go.Scattermapbox(
            lat=df_sub['lat'], lon=df_sub['long'],
            text=df_sub['text'], name=name,
            mode='markers',
            marker=dict(
                # size=2. * max(df['users_count']) / lim[2] ** 2,
                size=2 * 45 / lim[2] ** 2,
                color=colors[i],
                sizemode='area'
            ),
        ))

    fig.update_layout(
        title_font_size=25, title_x=0.5,
        title_text='regions_map',
        margin={'l': 0, 't': 40, 'b': 0, 'r': 0},
        mapbox={
            'center': {'lon': 40, 'lat': 40},
            'style': 'stamen-terrain',
            'zoom': 1.5
        }
    )
    return fig


@app.callback(
    [Output('date-alert', 'children'),
     Output('visits-count', 'children'),
     Output('graph-visits-count-by-hour', 'figure'),
     Output('graph-page-views-by-devices', 'figure'),
     Output('graph-visits-count-by-traffic-source', 'figure'),
     Output('graph-regions_map', 'figure')],
    [Input('date-picker-single', 'date')])
def update_output(date):
    date, alert = [date, True] if date is not None else [d.max_date, False]
    scatter = scatter_figure_visits_count_by_hour(date=date)
    all_visits, pie = pie_figure_page_views_by_devices(date=date)
    bar = bar_figure_visits_count_by_traffic_source(date=date)
    scattergeo = scattergeo_figure_regions_map(date=date)
    if alert:
        return get_success_alert(date=date), all_visits, scatter, pie, bar, scattergeo
    else:
        return dander_alert, all_visits, scatter, pie, bar, scattergeo


def layout():
    return html.Div([
        html.Div(id='date-alert'),
        dbc.Row([
            dbc.Col(
                html.Div(id='visits-count'),
                width=6
            ),
            dbc.Col(
                dcc.DatePickerSingle(
                    id='date-picker-single',
                    display_format='DD-MM-YYYY',
                    min_date_allowed=d.min_date,
                    max_date_allowed=d.max_date,
                    initial_visible_month=d.max_date,
                    date=d.max_date,
                    clearable=True,
                    with_portal=True,
                    placeholder='Select a date',
                    style=dict(float='right')
                ),
                width=6
            ),
        ]),
        dbc.Row([
            dbc.Col(
                dcc.Graph(id='graph-visits-count-by-traffic-source'),
                width=8
            ),
            dbc.Col(
                dcc.Graph(id='graph-page-views-by-devices'),
                width=4
            ),
        ]),
        html.Br(),
        dbc.Row(
            dbc.Col(
                dcc.Graph(id='graph-visits-count-by-hour'),
                width=12
            ),
        ),
        html.Br(),
        dbc.Row(
            dbc.Col(
                dcc.Graph(id='graph-regions_map'),
                width=12
            ),
        ),
        html.Br(),
        html.Br(),
    ])
