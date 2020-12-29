import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

from flask_login import login_user

from pages.auth_pages.validate_input_fields.validator import Validators
from server import app
from backend.models import Users


REGISTRATIONS_FIELDS = ['username', 'email', 'password', 'confirm']


def layout():
    return dbc.Row(
        dbc.Col([
            dcc.Location(id='register-url', refresh=True),
            html.Div(1, id='register-trigger', style=dict(display='none')),
            html.Div(id='register-alert'),
            dbc.FormGroup([
                dbc.Input(id='register-username'),
                dbc.FormText(id='register-formtext-username'),
                html.Br(),

                dbc.Input(id='register-email'),
                dbc.FormText(id='register-formtext-email'),
                html.Br(),

                dbc.Input(id='register-password', type='password'),
                dbc.FormText(id='register-formtext-password'),
                html.Br(),

                dbc.Input(id='register-confirm', type='password'),
                dbc.FormText('Confirm password', id='register-formtext-confirm'),
                html.Br(),

                dbc.Button('Registration', id='register-button', color='primary', disabled=True),

                html.Br(),
                html.Br(),
                dcc.Link('Login', href='/login'),
            ])
        ], id='row_registration', style=dict(visibility='hidden'), width=6)
    )


@app.callback(
    [Output('register-'+field, 'value') for field in REGISTRATIONS_FIELDS],
    [Input('register-trigger', 'children')]
)
def registrations_fields_default(trigger):
    if trigger:
        return '', '', '', ''


@app.callback(
    [Output('register-'+field, 'valid') for field in REGISTRATIONS_FIELDS] +
    [Output('register-'+field, 'invalid') for field in REGISTRATIONS_FIELDS] +
    [Output('register-formtext-'+field, 'children') for field in REGISTRATIONS_FIELDS] +
    [Output('register-'+field, 'color') for field in REGISTRATIONS_FIELDS] +
    [Output('register-button', 'disabled')] +
    [Output('row_registration', 'style')],
    [Input('register-'+field, 'value') for field in REGISTRATIONS_FIELDS]
)
def validate_registration_params(username, email, password, confirm):
    validator = Validators(
        params=[username, email, password, confirm],
        p=['Username', 'Email', 'Password', 'Confirm password'],
        page_fields=REGISTRATIONS_FIELDS
    )
    return validator.run(register_page=True)


@app.callback(
    [Output('register-url', 'pathname')],
    [Input('register-button', 'n_clicks')],
    [State('register-'+field, 'value') for field in REGISTRATIONS_FIELDS[:-1]],
)
def registrations_success(n_clicks, username, email, password):
    if n_clicks:
        if Users().add_user(username=username, email=email, password=password):
            login_user(user=Users.get(Users.username == username))
            return ['/home']
