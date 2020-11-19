import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

from flask_login import current_user
from backend.models import Users
from pages.auth_pages.validate_input_fields.validator import Validators
from server import app


PROFILE_FIELDS = ['username', 'password', 'confirm']


def layout():
    return dbc.Row(
        dbc.Col([
            html.Div(1, id='profile-trigger', style=dict(display='none')),
            html.H3('Profile', id='profile-title'),
            html.Div(id='profile-alert'),
            html.Div(id='profile-alert-login'),
            html.Div(id='profile-login-trigger', style=dict(display='none')),
            html.Br(),

            dbc.FormGroup([
                dbc.Label(id='profile-label-username'),
                dbc.Input(placeholder='Change username...', id='profile-username'),
                dbc.FormText(id='profile-formtext-username'),
                html.Br(),

                dbc.Label(id='profile-label-email'),
                dbc.FormText('Cannot change email'),
                html.Hr(),

                dbc.Label('Change password', id='profile-label-password'),
                dbc.Input(placeholder='Change password...', id='profile-password', type='password'),
                dbc.FormText('Change password', id='profile-formtext-password'),
                html.Br(),
                dbc.Input(placeholder='Confirm password...', id='profile-confirm', type='password'),
                dbc.FormText('Confirm password', id='profile-formtext-confirm'),
                html.Hr(),
                html.Br(),

                dbc.Button('Save changes', color='primary', id='profile-button', disabled=True),
            ])
        ], width=6)
    )


@app.callback(
    [Output('profile-label-'+field, 'children') for field in ['username', 'email']] +
    [Output('profile-'+field, 'value') for field in PROFILE_FIELDS],
    [Input('profile-trigger', 'children')]
)
def profile_values(trigger):
    if current_user.is_authenticated and trigger:
        return [
            ['Username: ', html.Strong(current_user.username)],
            ['Email: ', html.Strong(current_user.email)],
            current_user.username,
            '',
            ''
        ]


@app.callback(
    [Output('profile-'+field, 'valid') for field in PROFILE_FIELDS] +
    [Output('profile-'+field, 'invalid') for field in PROFILE_FIELDS] +
    [Output('profile-formtext-'+field, 'children') for field in PROFILE_FIELDS] +
    [Output('profile-'+field, 'color') for field in PROFILE_FIELDS] +
    [Output('profile-button', 'disabled')],
    [Input('profile-'+field, 'value') for field in PROFILE_FIELDS]
)
def profile_validate_inputs(username, password, confirm):
    validator = Validators(
        params=[username, password, confirm],
        p=['Username', 'Password', 'Confirm password'],
        page_fields=PROFILE_FIELDS
    )
    return validator.run()


@app.callback(
    [Output('profile-trigger', 'children'),
     Output('profile-alert', 'children')],
    [Input('profile-button', 'n_clicks')],
    [State('profile-{}'.format(field), 'value') for field in PROFILE_FIELDS]
)
def profile_save_changes(n_clicks, username, password, confirm):
    if n_clicks:
        email = current_user.email
        data_changes = []
        if username != current_user.username:
            data_changes.append('Username changed.')
            Users().change_user(username=username, email=email)
        if Users().set_password(password) != current_user.password:
            data_changes.append('Password changed.')
            Users().change_password(password=password, email=email)
        if data_changes:
            data_changes.append('Changes saved successfully.')
            text_alert = ' '.join(data_changes)
            return 1, [dbc.Alert(text_alert, color='success')]
