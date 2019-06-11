from sqlalchemy.types import TypeDecorator
from sqlalchemy.types import INTEGER, TEXT
from schwifty import IBAN
from urllib.parse import urlparse
import datetime

def date_to_timestamp(date):
    return datetime.datetime.combine(date, datetime.time(12,0,0, tzinfo=datetime.timezone.utc)).timestamp()

class UnixTimestamp(TypeDecorator):
    impl = INTEGER

    def __init__(self):
        TypeDecorator.__init__(self)

    def process_bind_param(self, value, dialect):
        return date_to_timestamp(value)

    def process_result_value(self, value, dialect):
        return datetime.datetime.utcfromtimestamp(value).date()

class IBANColumnType(TypeDecorator):
    impl = TEXT

    def __init__(self):
        TypeDecorator.__init__(self)

    def process_bind_param(self, value, dialect):
        return value.compact if value else None

    def process_result_value(self, value, dialect):
        try:
            return IBAN(value)
        except:
            return None

class UrlColumnType(TypeDecorator):
    impl = TEXT

    def __init__(self):
        TypeDecorator.__init__(self)

    def process_bind_param(self, value, dialect):
        return value.geturl() if value else None

    def process_result_value(self, value, dialect):
        return urlparse(value) if value else None
