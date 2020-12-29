import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_daq as daq
from dash.dependencies import Input, Output
from flask_login import current_user, logout_user

try:
    from pages.auth_pages import login, registration
    from server import app
    from pages import home, profile
    from backend.settings import DEBUG
except ImportError:
    exit('copy settings.py.default->settings.py and '
         'set TOKEN, TOKEN_MAP and SECRET_KEY_SERVER')


header = dbc.Navbar(
    dbc.Container([
        dbc.NavbarBrand('Test Dash Project', href='/home'),
        dbc.Nav([
            dbc.NavItem(dbc.NavLink('Home', id='home', href='/home')),
            dbc.NavItem(dbc.NavLink(id='profile', href='/profile')),
            dbc.NavItem(dbc.NavLink(id='user-action', href='/login')),
            dbc.NavItem(dbc.NavLink(daq.ToggleSwitch(
                id='darktheme-daq-toggleswitch', className='dark-theme-control', size=35
            ))),
        ], id='navigation_panel', style=dict(display='none')),
    ]),
    className='mb-5',
)

app.layout = html.Div([
    header,
    html.Div(dbc.Container(id='page-content')),
    dcc.Location(id='base-url', refresh=False)
])


@app.callback(
    Output('page-content', 'children'),
    [Input('base-url', 'pathname')])
def router(pathname):
    print('routing to', pathname)
    if not current_user.is_authenticated:
        if pathname in ['/', '/login', '/home']:
            return login.layout()
        elif pathname == '/register':
            return registration.layout()

    if current_user.is_authenticated:
        if pathname == '/logout':
            logout_user()
            return login.layout()
        elif pathname == '/' or pathname == '/home':
            return home.layout()
        elif pathname == '/profile':
            return profile.layout()

    return html.Div(html.Strong(html.H1('Error 404! Page not found!')),
                    style=dict(textAlign='center'))


@app.callback(
    [Output('user-action', 'children'),
     Output('user-action', 'href'),
     Output('profile', 'children'),
     Output('navigation_panel', 'style')],
    [Input('page-content', 'children')])
def user_logout(input):
    if current_user.is_authenticated:
        return 'Logout', '/logout', html.Div(current_user.username), {}
    else:
        return 'Sign In', '/login', '', dict(display='none')


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=DEBUG)
