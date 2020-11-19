from datetime import date, timedelta
from importlib import import_module

from backend.models import Date
from backend.request_handlers.requester import Requester

try:
    from backend.settings import URL, HEADER, QUERY, CASES_OF_MODEL_QUERY, ADMIN_DEFAULT_EMAIL, ADMIN_DEFAULT_PASSWORD
except ImportError:
    exit('copy settings.py.default->settings.py and '
         'set TOKEN, TOKEN_MAP and SECRET_KEY_SERVER')


class DeltaDaysIsNotInt(Exception):
    def __str__(self):
        return "Parameter 'delta_days' must be integer!"


class Worker:
    QUERY = QUERY

    def __init__(self):
        self.date_work = None
        self.date_id = 0

    def run(self, delta_days: int = 1):
        try:
            self.__checking_delta_days(delta_days=delta_days)
            for i in range(delta_days, 0, -1):
                self.__init_params(delta_days=i)
                self.__insert_metric_data_to_db()
        except Exception as exc:
            print(exc)
            self.__del_bad_inserted_data()

    @staticmethod
    def __checking_delta_days(delta_days: int):
        if not isinstance(delta_days, int):
            raise DeltaDaysIsNotInt()

    def __init_params(self, delta_days: int = 1):
        self.date_work = date.today() - timedelta(days=delta_days)
        query_date = {
            'date1': f'{self.date_work}',
            'date2': f'{self.date_work}',
        }
        self.QUERY.update(query_date)
        self.date_id = Date.get_or_create(date=self.date_work)
        if not self.date_id[1]:
            exit(print('Такая дата уже есть в БД!'))
        else:
            self.date_id = self.date_id[0]

    def __insert_metric_data_to_db(self):
        for name_model, query in CASES_OF_MODEL_QUERY.items():
            self.QUERY.update(query)
            class_model = getattr(import_module('backend.models'), name_model)
            for item in self.__get_data_from_metric:
                class_model().add_metric_row(date_id=self.date_id, metric_data=item)

    @property
    def __get_data_from_metric(self) -> list:
        response = Requester().get(url=URL, params=QUERY, headers=HEADER)
        return response['data']

    def __del_bad_inserted_data(self):
        if self.date_work:
            if not self.date_id:
                self.date_id = Date().get_id_value(name_column='date',
                                                   value=str(self.date_work))
            Date.delete().where(Date.id == self.date_id).execute()
