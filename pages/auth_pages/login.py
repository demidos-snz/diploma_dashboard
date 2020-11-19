import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash import no_update

from flask_login import login_user
from flask_peewee.utils import check_password

from backend.models import Users
from backend.settings import ADMIN_DEFAULT_EMAIL, ADMIN_DEFAULT_PASSWORD
from server import app


failure_alert = dbc.Alert(
    'Login or password unsuccessful. Try again.',
    color='danger',
    dismissable=True
)


def layout():
    return dbc.Row(
        dbc.Col([
            dcc.Location(id='login-url', refresh=True, pathname='/login'),
            html.Div(id='login-alert'),
            dbc.FormGroup([
                dbc.Alert(
                    f'Try admin or {ADMIN_DEFAULT_EMAIL} / {ADMIN_DEFAULT_PASSWORD}',
                    color='info',
                    dismissable=True
                ),
                html.Br(),

                dbc.Input(id='login-email', autoFocus=True),
                dbc.FormText('Username or Email'),

                html.Br(),
                dbc.Input(id='login-password', type='password'),
                dbc.FormText('Password'),

                html.Br(),
                dbc.Button('Submit', color='primary', id='login-button'),

                html.Br(),
                html.Br(),
                dcc.Link('Registration', href='/register'),
            ])
        ], width=6)
    )


@app.callback(
    [Output('login-url', 'pathname'),
     Output('login-alert', 'children')],
    [Input('login-button', 'n_clicks')],
    [State('login-email', 'value'),
     State('login-password', 'value')]
)
def user_login(n_clicks, username_or_email, password):
    if n_clicks:
        user_username = Users.get_or_none(Users.username == username_or_email)
        user_email = Users.get_or_none(Users.email == username_or_email)
        users = [user_username, user_email]
        for user in users:
            if user is not None:
                flag_password = check_password(raw_password=password,
                                               enc_password=user.password)
                if flag_password:
                    login_user(user=user)
                    return '/home', ''
        return no_update, failure_alert
