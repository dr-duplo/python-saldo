from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from . import Base
from .column_types import UnixTimestamp

import datetime

def date_to_timestamp(date):
    return datetime.datetime.combine(date, datetime.time(12,0,0, tzinfo=datetime.timezone.utc)).timestamp()

def balance_hash(**kwargs):
    return "%d_%d_%d_%s" % (
    	kwargs.get('account_id'),
    	date_to_timestamp(kwargs.get('date')) if isinstance(kwargs.get('date'), datetime.date) else kwargs.get('date'),
    	int((kwargs.get('value') if kwargs.get('value') else 0) * 100),
    	kwargs.get('currency')
    	)

def balance_hash_builder(context):
    return balance_hash(**context.current_parameters)

class Balance(Base):
    __tablename__ = "balances"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    hash = Column(String, unique=True, default=balance_hash_builder, onupdate=balance_hash_builder)
    date = Column(UnixTimestamp)
    value = Column(Float)
    currency = Column(String)

    account = relationship('Account', primaryjoin = ('Account.id == Balance.account_id'))

    @hybrid_property
    def pre_booked(self):
        return self.date > self.account.balance.date

    def __repr__(self):
        return "Balance(%s, %s, %f %s)" % (
            self.account.account_iban,
            self.date,
            self.value,
            self.currency)
