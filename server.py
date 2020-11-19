import dash
import dash_bootstrap_components as dbc
from flask_login import LoginManager
from flask_peewee.auth import Auth
from flask_peewee.db import Database as DataBase
from flask_peewee.admin import Admin
# from flask_peewee.rest import RestAPI


from backend.models import Cities, Date, Devices, HoursInDay, PageViewsByDevices, \
    RegionsMap, TrafficSource, VisitsCountByHour, VisitsCountByTrafficSource, Users
from backend.settings import DB_NAME, SECRET_KEY_SERVER

if not SECRET_KEY_SERVER:
    exit('SECRET_KEY_SERVER has to be not NULL, set value!')

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

app.config.suppress_callback_exceptions = True
# app.css.config.serve_locally = True
# app.scripts.config.serve_locally = True
app.title = 'Test Dash Project'

server = app.server
DATABASE = {
    'name': DB_NAME,
    'engine': 'peewee.SqliteDatabase',
}
DEBUG = True
SECRET_KEY = SECRET_KEY_SERVER
server.config.from_object(__name__)

db = DataBase(server)

auth = Auth(app=server, db=db, user_model=Users)

admin = Admin(app=server, auth=auth)
admin.register(model=Cities)
admin.register(model=Date)
admin.register(model=Devices)
admin.register(model=HoursInDay)
admin.register(model=PageViewsByDevices)
admin.register(model=RegionsMap)
admin.register(model=TrafficSource)
admin.register(model=Users)
admin.register(model=VisitsCountByHour)
admin.register(model=VisitsCountByTrafficSource)
admin.setup()

# Setup the LoginManager for the server
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'


@login_manager.user_loader
def load_user(user_id: int):
    return Users.get(Users.id == user_id)
