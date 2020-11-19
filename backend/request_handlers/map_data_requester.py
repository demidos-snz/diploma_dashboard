from backend.settings import URL_MAP
from backend.request_handlers.requester import Requester


class MapDataRequester(Requester):
    def get_data_from_map(self, name_city: str, country_code: str) -> list:
        if not country_code:
            name_city = name_city.replace('-', ' ')
        rsp = self.get(url=URL_MAP.format(name_city))
        res = self.__get_list_lat_long_cc(response=rsp,
                                          country_code=country_code) if rsp else []
        if res:
            return res
        elif name_city.find('-') != -1:
            name_city = name_city.replace('-', ' ')
            return self.get_data_from_map(
                name_city=name_city, country_code=country_code
            )
        else:
            return [0, 0, '']

    @staticmethod
    def __get_list_lat_long_cc(response: dict, country_code: str) -> list:
        response = response['response']['GeoObjectCollection']['featureMember']
        for row in response:
            row = row['GeoObject']
            if country_code:
                rsp_code_country = row['metaDataProperty']['GeocoderMetaData']['Address'].get('country_code')
                if rsp_code_country != country_code:
                    continue
            row['Point']['pos'] += f' {country_code}'
            return row['Point']['pos'].split(' ')
