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


RADIUS_OF_CITIES_ON_MAP = [3, 2.75, 2.25, 2, 1.5]

d = Date()

dander_alert = dbc.Alert('Select a date', color='danger', dismissable=True)


def get_success_alert(start_date: str, end_date: str) -> dbc.Alert:
    return dbc.Alert(
        f'You have chosen a start date {start_date}, end date {end_date}',
        color='success', dismissable=True
    )


def bar_figure_visits_count_by_traffic_source(start_date: str, end_date: str) -> go.Figure:
    visits_count_by_traffic_source = VisitsCountByTrafficSource().get_data_from_joining_models(
        start_date=start_date,
        end_date=end_date,
        select_name_column='visits_count',
        order_name_column='traffic_source_id',
        model=TrafficSource
    )

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=[row[0] for row in visits_count_by_traffic_source],
        y=[row[1] for row in visits_count_by_traffic_source],
        hovertemplate='%{x}: %{y:.f}<extra></extra>',
    ))

    fig.update_layout(
        title_font_size=25, title_x=0.5,
        title_text='visits_count_by_traffic_source'
    )
    return fig


def pie_figure_page_views_by_devices(start_date: str, end_date: str) -> (html.H1, go.Figure):
    page_views_by_devices = PageViewsByDevices().get_data_from_joining_models(
        start_date=start_date,
        end_date=end_date,
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


def scatter_figure_visits_count_by_hour(start_date: str, end_date: str) -> go.Figure:
    visits_count_by_every_hour = VisitsCountByHour().get_data_from_joining_models(
        start_date=start_date,
        end_date=end_date,
        select_name_column='visits_count_by_hour',
        order_name_column='hour_id',
        model=HoursInDay
    )

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=HoursInDay().hours,
        y=[row[1] for row in visits_count_by_every_hour],
        mode='markers',
    ))

    fig.update_layout(
        xaxis_title=f'Hours of {start_date} - {end_date}',
        yaxis_title='Visits',
        title_font_size=25, title_x=0.5,
        title_text='visits_count_by_hour'
    )
    return fig


def scattergeo_figure_regions_map(start_date: str, end_date: str) -> go.Figure:
    mapping_data = RegionsMap().get_list_with_city_name_code_country_coord(
        start_date=start_date,
        end_date=end_date
    )

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

    limits = get_limits_params_for_map(
        counts_users=list({row[-1] for row in mapping_data})
    )
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


def get_limits_params_for_map(counts_users: list) -> list:
    counts_users.sort(key=lambda x: x)
    len_diapason = len(counts_users) // len(RADIUS_OF_CITIES_ON_MAP) + 1
    limits = []
    start = 0
    for i in RADIUS_OF_CITIES_ON_MAP:
        diapason = counts_users[start:] if start + len_diapason >= len(counts_users) \
            else counts_users[start:start + len_diapason]
        l_diapason = len(diapason)
        if l_diapason == 1:
            limits.append([diapason[0], diapason[0], i])
            break
        elif l_diapason == 0:
            diapason = counts_users[start - len_diapason:-1]
            limits[-1] = [diapason[0], diapason[-1], i]
            limits.append([counts_users[-1], counts_users[-1], i])
            break
        else:
            limits.append([diapason[0], diapason[-1], i])
        start += len_diapason
    return limits


@app.callback(
    [Output('date-alert', 'children'),
     Output('visits-count', 'children'),
     Output('graph-visits-count-by-hour', 'figure'),
     Output('graph-page-views-by-devices', 'figure'),
     Output('graph-visits-count-by-traffic-source', 'figure'),
     Output('graph-regions_map', 'figure')],
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     ])
def update_output(start_date: str, end_date: str):
    start_date, end_date, alert = check_input_date(start_date=start_date, end_date=end_date)
    scatter = scatter_figure_visits_count_by_hour(start_date=start_date, end_date=end_date)
    all_visits, pie = pie_figure_page_views_by_devices(start_date=start_date, end_date=end_date)
    bar = bar_figure_visits_count_by_traffic_source(start_date=start_date, end_date=end_date)
    scattergeo = scattergeo_figure_regions_map(start_date=start_date, end_date=end_date)
    if alert:
        return get_success_alert(
            start_date=start_date, end_date=end_date
        ), all_visits, scatter, pie, bar, scattergeo
    else:
        return dander_alert, all_visits, scatter, pie, bar, scattergeo


def check_input_date(start_date: str, end_date: str) -> list:
    alert = True
    if start_date is None and end_date is None:
        start_date = d.min_date
        end_date = d.max_date
        alert = False
    if end_date is None:
        end_date = d.max_date
        alert = False
    return [start_date, end_date, alert]


def layout():
    return html.Div([
        html.Div(id='date-alert'),
        dbc.Row([
            dbc.Col(
                html.Div(id='visits-count'),
                width=6
            ),
            dbc.Col(
                dcc.DatePickerRange(
                    id='date-picker',
                    display_format='DD-MM-YYYY',
                    min_date_allowed=d.min_date,
                    max_date_allowed=d.max_date,
                    initial_visible_month=d.max_date,
                    start_date=d.min_date,
                    end_date=d.max_date,
                    clearable=True,
                    with_portal=True,
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
