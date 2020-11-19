from flask_login import current_user
from validate_email import validate_email

from backend.models import Users
from backend.settings import MIN_LENGTH_PASSWORD


class Validators:
    def __init__(self, params: list, p: list, page_fields: list, button_disabled: bool = True):
        self.params = params
        self.formtexts = dict(zip(page_fields, p))
        self.count_fields = len(page_fields)
        self.formcolors = dict(zip(page_fields, ['secondary'] * self.count_fields))
        self.button_disabled = button_disabled

        checked_params = [v if v else '' for v in self.params]
        self.input_params = dict(zip(page_fields, checked_params))

        self.bool_params_of_fields = {
            'valid': {field: False for field in page_fields},
            'invalid': {field: False for field in page_fields}
        }

    def run(self, register_page: bool = False) -> list:
        self.__checking_username()

        if register_page:
            self.__checking_email()

        self.__checking_password()

        self.__checking_confirm_password()

        if sum(self.bool_params_of_fields['valid'].values()) == self.count_fields:
            self.button_disabled = False

        return [
            *list(self.bool_params_of_fields['valid'].values()),
            *list(self.bool_params_of_fields['invalid'].values()),
            *list(self.formtexts.values()),
            *list(self.formcolors.values()),
            self.button_disabled,
        ]

    def __checking_username(self):
        username = self.input_params['username']
        if username:
            if current_user.is_authenticated and username == current_user.username:
                self.__generate_success_formtext_with_color(
                    field_name='username', formtext='Username is good'
                )
            elif Users().get_or_none(Users.username == username):
                self.__generate_danger_formtext_with_color(
                    field_name='username', formtext='Username already exists'
                )
            else:
                self.__generate_success_formtext_with_color(
                    field_name='username', formtext='Username is good'
                )
        else:
            self.__generate_danger_formtext_with_color(
                field_name='username', formtext='Username must not empty'
            )

    def __checking_email(self):
        email = self.input_params['email']
        if email:
            validate_flag = validate_email(email)
            if Users().get_or_none(Users.email == email):
                self.__generate_danger_formtext_with_color(
                    field_name='email', formtext='Email already exists'
                )
            elif validate_flag:
                self.__generate_success_formtext_with_color(
                    field_name='email', formtext='Email is good'
                )
            else:
                self.__generate_danger_formtext_with_color(
                    field_name='email', formtext='Email is not valid'
                )
        else:
            self.__generate_danger_formtext_with_color(
                field_name='email', formtext='Email must not empty'
            )

    def __checking_password(self):
        password = self.input_params['password']
        if password:
            if len(password) < MIN_LENGTH_PASSWORD:
                self.__generate_danger_formtext_with_color(
                    field_name='password',
                    formtext=f"It's a simple password, "
                             f"must be longer than {MIN_LENGTH_PASSWORD}"
                )
            else:
                self.__generate_success_formtext_with_color(
                    field_name='password', formtext='Password is good'
                )
        else:
            self.__generate_danger_formtext_with_color(
                field_name='password', formtext='Password must not empty'
            )

    def __checking_confirm_password(self):
        if self.input_params['confirm']:
            flag_password = self.input_params['password'] == self.input_params['confirm']
            self.bool_params_of_fields['valid']['confirm'] = flag_password
            self.bool_params_of_fields['invalid']['confirm'] = not flag_password
        else:
            self.__generate_danger_formtext_with_color(
                field_name='confirm', formtext='Confirm password must not empty'
            )

    def __generate_danger_formtext_with_color(self, field_name: str, formtext: str):
        self.bool_params_of_fields['valid'][field_name] = False
        self.bool_params_of_fields['invalid'][field_name] = True
        self.formcolors[field_name] = 'danger'
        self.formtexts[field_name] = formtext

    def __generate_success_formtext_with_color(self, field_name: str, formtext: str):
        self.bool_params_of_fields['valid'][field_name] = True
        self.bool_params_of_fields['invalid'][field_name] = False
        self.formcolors[field_name] = 'success'
        self.formtexts[field_name] = formtext
