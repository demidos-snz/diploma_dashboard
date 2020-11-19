try:
    from backend.main import Worker
    from backend.models import Users
except ImportError:
    exit('copy settings.py.default->settings.py and '
         'set TOKEN, TOKEN_MAP and SECRET_KEY_SERVER')


if __name__ == '__main__':
    u = Users()
    if not u.check_exists_admin_user:
        u.insert_default_values()
    t = Worker()
    t.run(delta_days=1)
