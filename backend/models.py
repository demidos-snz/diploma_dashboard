from flask_login import UserMixin
from flask_peewee.auth import BaseUser
from peewee import SqliteDatabase, Model, \
    CharField, ForeignKeyField, DateField, IntegerField, FloatField, BooleanField, fn

from backend.settings import DB_NAME, ADMIN_DEFAULT_PASSWORD, ADMIN_DEFAULT_EMAIL
from backend.request_handlers.map_data_requester import MapDataRequester

db = SqliteDatabase(DB_NAME, pragmas={'foreign_keys': 1})


def make_table_name(model_class: Model) -> str:
    table_name = ['_' + sym if sym.isupper() and i != 0 else sym
                  for i, sym in enumerate(model_class.__name__)]
    return ''.join(table_name).lower()


class BaseModel(Model):
    class Meta:
        database = db
        table_function = make_table_name

    def add_metric_row(self, date_id: int, metric_data: dict):
        pass

    def insert_default_values(self):
        pass


class ModelWithTwoId(Model):
    def get_data_from_joining_models(self, start_date: str, end_date: str, select_name_column: str,
                                     order_name_column: str, model) -> list:
        start_date_id = Date().get(date=start_date)
        end_date_id = Date().get(date=end_date)
        query = self.select(model.name, self._meta.columns[select_name_column]).\
            join(model, on=self._meta.columns[order_name_column] == model.id).\
            where(
                self._meta.columns['date_id'] >= start_date_id,
                self._meta.columns['date_id'] <= end_date_id
            ).tuples()
        return [row for row in query]


class Date(BaseModel):
    date = DateField(formats='%Y-%m-%d', unique=True)

    @property
    def min_date(self) -> str:
        query = self.select(self._meta.columns['date']).\
            order_by(self._meta.columns['date']).limit(1)
        for row in query:
            return row.date

    @property
    def max_date(self) -> str:
        query = self.select(self._meta.columns['date']).\
            order_by(self._meta.columns['date'].desc()).limit(1)
        for row in query:
            return row.date


class HoursInDay(BaseModel):
    name = DateField(formats='%H:%M:%S', unique=True)

    def insert_default_values(self):
        for i in range(0, 24):
            self.insert(id=i+1, name=f'{i:0>2}:00:00').execute()

    @property
    def hours(self) -> list:
        query = self.select(self._meta.columns['name'])
        return [row.name for row in query]


class VisitsCountByHour(BaseModel, ModelWithTwoId):
    date_id = ForeignKeyField(model=Date, field=Date.id, on_delete='CASCADE')
    hour_id = ForeignKeyField(
        model=HoursInDay, field=HoursInDay.id, on_delete='CASCADE'
    )
    visits_count_by_hour = IntegerField()

    def add_metric_row(self, date_id: int, metric_data: dict):
        hour = metric_data['dimensions'][0]['name'].split(' ')[1],
        visits_count_by_hour = metric_data['metrics'][0]
        hour_id = HoursInDay().get(name=hour)
        self.insert(
            date_id=date_id,
            hour_id=hour_id,
            visits_count_by_hour=visits_count_by_hour
        ).execute()


class Cities(BaseModel):
    city = IntegerField(unique=True)
    name = CharField(max_length=50)
    code_country = CharField(max_length=2)
    lat = FloatField()
    long = FloatField()


class RegionsMap(BaseModel):
    date_id = ForeignKeyField(model=Date, field=Date.id, on_delete='CASCADE')
    city_id = ForeignKeyField(model=Cities, field=Cities.id, on_delete='CASCADE')
    users_count = IntegerField()

    def add_metric_row(self, date_id: int, metric_data: dict):
        city = metric_data['dimensions'][0]['id']
        name_city = metric_data['dimensions'][0]['name']
        iso_name = metric_data['dimensions'][0]['iso_name']
        country_code = iso_name[:2] if iso_name else ''
        city_id = Cities().get_or_none(Cities.city == city)
        if city_id is None:
            map_params = MapDataRequester().get_data_from_map(
                name_city=name_city, country_code=country_code
            )
            city_id = Cities.insert(
                city=city, name=metric_data['dimensions'][0]['name'],
                code_country=map_params[2], lat=map_params[1], long=map_params[0]
            ).execute()
        self.insert(
            date_id=date_id,
            city_id=city_id,
            users_count=metric_data['metrics'][0]
        ).execute()

    def get_list_with_city_name_code_country_coord(self, start_date: str, end_date: str) -> list:
        start_date_id = Date().get(date=start_date)
        end_date_id = Date().get(date=end_date)
        query = self.select(Cities.name, Cities.code_country,
                            Cities.lat, Cities.long,
                            fn.SUM(self._meta.columns['users_count'])).\
            join(Cities, on=self._meta.columns['city_id'] == Cities.id).\
            where(
                self._meta.columns['date_id'] >= start_date_id,
                self._meta.columns['date_id'] <= end_date_id
            ).group_by(
                Cities.name, Cities.code_country,
                Cities.lat, Cities.long
            ).tuples()
        return [row for row in query]


class Devices(BaseModel):
    device = CharField(max_length=10, unique=True)
    name = CharField(max_length=10, unique=True)


class PageViewsByDevices(BaseModel, ModelWithTwoId):
    date_id = ForeignKeyField(model=Date, field=Date.id, on_delete='CASCADE')
    device_id = ForeignKeyField(model=Devices, field=Devices.id, on_delete='CASCADE')
    page_views = IntegerField()

    def add_metric_row(self, date_id: int, metric_data: dict):
        device_name = metric_data['dimensions'][0]['id']
        page_views = metric_data['metrics'][0]
        device_id = Devices().get_or_none(device=device_name)
        if device_id is None:
            name = metric_data['dimensions'][0]['name']
            device_id = Devices().insert(device=device_name, name=name).execute()
        self.insert(
            date_id=date_id,
            device_id=device_id,
            page_views=page_views
        ).execute()


class TrafficSource(BaseModel):
    traffic_source_name = CharField(max_length=20, unique=True)
    name = CharField(max_length=50, unique=True)


class VisitsCountByTrafficSource(BaseModel, ModelWithTwoId):
    date_id = ForeignKeyField(model=Date, field=Date.id, on_delete='CASCADE')
    traffic_source_id = ForeignKeyField(
        model=TrafficSource,
        field=TrafficSource.id,
        on_delete='CASCADE'
    )
    visits_count = IntegerField()

    def add_metric_row(self, date_id: int, metric_data: dict):
        traffic_source_name = metric_data['dimensions'][0]['id']
        visits_count = metric_data['metrics'][0]
        ts_id = TrafficSource().get_or_none(traffic_source_name=traffic_source_name)
        if ts_id is None:
            name = metric_data['dimensions'][0]['name']
            ts_id = TrafficSource().insert(
                traffic_source_name=traffic_source_name,
                name=name
            ).execute()
        self.insert(
            date_id=date_id,
            traffic_source_id=ts_id,
            visits_count=visits_count
        ).execute()


class Users(BaseModel, BaseUser, UserMixin):
    username = CharField(max_length=15, unique=True)
    email = CharField(max_length=50, unique=True)
    password = CharField(max_length=50)
    active = BooleanField(default=True)
    admin = BooleanField(default=False)

    def insert_default_values(self):
        self.set_password(str(ADMIN_DEFAULT_PASSWORD))
        self.insert(
            username='admin',
            email=ADMIN_DEFAULT_EMAIL,
            password=self.password,
            active=True,
            admin=True
        ).execute()

    def add_user(self, username: str, email: str, password: str) -> int:
        self.set_password(password)
        return self.insert(
            username=username,
            email=email,
            password=self.password
        ).execute()

    def change_user(self, username: str, email: str):
        self.update(username=username).\
            where(self._meta.columns['email'] == email).execute()

    def change_password(self, password: str, email: str):
        self.set_password(password)
        self.update(password=self.password).\
            where(self._meta.columns['email'] == email).execute()

    @property
    def check_exists_admin_user(self) -> bool:
        query = self.select().where(
            self._meta.columns['username'] == 'admin',
            self._meta.columns['email'] == ADMIN_DEFAULT_EMAIL,
            self._meta.columns['active'] == 1,
            self._meta.columns['admin'] == 1
        )
        return True if [row for row in query] else False


db.connect()
db.create_tables([Date, VisitsCountByHour, Cities, RegionsMap,
                  Devices, TrafficSource, PageViewsByDevices,
                  VisitsCountByTrafficSource])


cases_of_create_default_models = [HoursInDay, Users]
for default_model in cases_of_create_default_models:
    if default_model._meta.table_name not in db.get_tables():
        db.create_tables([default_model])
        default_model().insert_default_values()

db.close()
