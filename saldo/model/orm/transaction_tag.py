from sqlalchemy import event, text
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.hybrid import hybrid_property
from . import Base
from .column_types import UnixTimestamp, IBANColumnType
from math import exp, log
import datetime
import logging

logging.getLogger("saldo.transaction_tags")

class TransactionTag(Base):
    __tablename__ = "transaction_tags"

    transaction_id = Column(Integer, ForeignKey('transactions.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)
    share = Column(Float, nullable=True)

    transaction = relationship('Transaction', uselist=False);
    tag = relationship('Tag', uselist=False)

    @hybrid_property
    def name(self):
        return  self.tag.name

    @hybrid_property
    def value(self):
        return  (self.share if self.share else 1.0) * self.transaction.value
