from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import text
from .column_types import IBANColumnType, UrlColumnType
from . import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    bank_country = Column(String)
    bank_code = Column(String)
    bank_branch_id = Column(String)
    owner = Column(String)
    account_number = Column(String)
    account_suffix = Column(String)
    account_iban = Column(IBANColumnType, nullable=False, unique=True)
    login = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    url = Column(UrlColumnType, nullable=False)

    transactions = relationship("Transaction",
                                back_populates="account",
                                order_by="desc(Transaction.date)")
    balances = relationship("Balance",
                                back_populates="account",
                                order_by="desc(Balance.date)")
    @hybrid_property
    def balance(self):
        return self.balances[0]

    def __repr__(self):
        return u"Account(%s)" % (self.account_iban)
