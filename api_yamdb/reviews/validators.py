import datetime

from django.core.exceptions import ValidationError


def year_validation(value):
    if value > datetime.datetime.now().year:
        raise ValidationError(
            '%(value) не может быть больше текущего года!',
            params={'value': value},
        )
