import requests


def checking_response(func):
    def wrapper(*args, **kwargs) -> dict:
        res = func(*args, **kwargs)
        if res.status_code == 200:
            res = res.json()
            if 'errors' in res:
                print(res['errors']['message'])
            else:
                return res
        else:
            print('Status_code:', res.status_code)
        return {}
    return wrapper


class Requester:
    @checking_response
    def get(self, url: str, **kwargs):
        return requests.get(url=url, **kwargs)
