import datetime
import logging

from math import exp, log
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy import text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, Session

from . import Base
from .column_types import UnixTimestamp, IBANColumnType
from .tag import Tag
from .transaction_tag import TransactionTag

logging.getLogger("saldo.transaction")


def date_to_timestamp(date):
    return datetime.datetime.combine(date, datetime.time(12, 0, 0, tzinfo=datetime.timezone.utc)).timestamp()


def transaction_hash(account_id, date, r_account_iban, r_bank_code, r_bank_branch_id, r_account_number, value):
    h = "%d_%d_" % \
        (account_id, date_to_timestamp(date if isinstance(date, datetime.date) else date))

    if r_account_iban:
        h += r_account_iban.compact
    else:
        h += r_bank_code or ""
        h += r_bank_branch_id or ""
        h += r_account_number or ""

    h += "_"
    h += str(int((value if value else 0) * 100))

    return h


def transaction_hash_kw(**kwargs):
    return transaction_hash(
        kwargs.get('account_id'),
        kwargs.get('date'),
        kwargs.get('r_account_iban'),
        kwargs.get('r_bank_code'),
        kwargs.get('r_bank_branch_id'),
        kwargs.get('r_account_number'),
        kwargs.get('value'))


def transaction_hash_builder(context):
    return transaction_hash_kw(**context.current_parameters)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    hash = Column(String, unique=True, default=transaction_hash_builder, onupdate=transaction_hash_builder)
    r_country = Column(String)
    r_bank_code = Column(String)
    r_bank_branch_id = Column(String)
    r_account_number = Column(String)
    r_account_suffix = Column(String)
    r_account_iban = Column(IBANColumnType)
    r_name = Column(String)
    r_bic = Column(String)
    date = Column(UnixTimestamp)
    valuta_date = Column(UnixTimestamp)
    value = Column(Float)
    value_currency = Column(String)
    fees = Column(Float)
    fees_currency = Column(String)
    type_code = Column(String)
    purpose = Column(String)
    raw = Column(String)

    account = relationship('Account', back_populates="transactions");
    tags = relationship('TransactionTag', cascade="all, delete-orphan")

    # prepare term frequency statement
    __stm_term_frequency = text("""
        SELECT
            :tag_id AS tag_id,
            tag_tokens.token AS token,
            SUM((tag_tokens.tag_id == :tag_id) * p_count) AS p_count,
            SUM((tag_tokens.tag_id != :tag_id) * p_count) AS n_count
            FROM tag_tokens
            JOIN (
            SELECT DISTINCT token FROM tokenizer
            WHERE INPUT=(
                SELECT text FROM transaction_text WHERE transaction_id=:transaction_id
            ) AND LENGTH(token) > 2
            ) AS transaction_tokens
            ON tag_tokens.token = transaction_tokens.token GROUP BY tag_tokens.token;""")

    @hybrid_property
    def pre_booked(self):
        return self.valuta_date > self.account.balance.date

    def __repr__(self):
        return "Transaction(%s, %s, %s, %f %s, %s)" % (
            self.account.account_iban or '-',
            self.type_code or '-',
            self.date,
            self.value or 0.0,
            self.value_currency or 'EUR',
            self.tags[0].tag.name if len(self.tags) else '-')

    def __chi2P(self, chi, df):
        m = chi / 2.0;
        sum = term = exp(-m);
        for i in range(1, int(df / 2) + 1):
            term *= m / i;
            sum += term;

        return min(sum, 1.0);

    def __term_frequency(self, tag):
        result = Session.object_session(self).execute(self.__stm_term_frequency,
                                                      {'transaction_id': self.id, 'tag_id': tag.id}).fetchall();

        terms = {}
        for row in result:
            terms[row[1]] = (row[2], row[3])

        return terms

    def __tag_likelihood(self, tag):
        # transaction term frequency
        terms = self.__term_frequency(tag)

        # number of transactions taged / not taged
        numTagged, numNotTagged = tag.usage()

        # The following algorithm is based on Gary Robinsons "Chi-Squared-Spam-Detection-Algorithm".
        # Please refer to [http://www.linuxjournal.com/article/6467] for more information.
        h_pos = 1  # positive hypothesis
        h_neg = 1  # negative hypothesis
        try:
            # for all terms
            for term in terms:
                F_tag_term = 0.5
                if (not (len(term) <= 2)) and \
                        (not (term.isdigit() and len(term) <= 3)):
                    # overall frequency of term
                    H_term = terms[term][0] + terms[term][1];
                    if H_term:
                        # Probability of tagged transaction contains term
                        P_term_p_tag = float(terms[term][0]) / numTagged if numTagged else 0.5;
                        # Probability of not tagged transaction contains term
                        P_term_n_tag = float(terms[term][1]) / numNotTagged if numNotTagged else 0.5;
                        # Probability of term occurs in tagged transaction
                        P_tag_term = P_term_p_tag / (P_term_p_tag + P_term_n_tag);
                        F_tag_term = (0.5 + H_term * P_tag_term) / (1.0 + H_term);

                # product of positive hypothesis terms
                h_pos *= F_tag_term;
                # product of negative hypothesis terms
                h_neg *= (1.0 - F_tag_term);

            # p-value of positive hypothesis
            h_pos = self.__chi2P(-2.0 * log(h_pos), 2.0 * len(terms));
            # p-value of negative hypothesis
            h_neg = self.__chi2P(-2.0 * log(h_neg), 2.0 * len(terms));
            # classification indicator I in [0, 1]
            I = ((h_pos - h_neg) + 1.0) / 2.0;
            # check for NaN
            return I
        except Exception as e:
            logging.warn(e)
            return 0.5

    def tag_likelihood(self, tag=None):
        if not tag:
            return [(tag, self.__tag_likelihood(tag)) for tag in
                    Session.object_session(self).query(Tag).all()]
        else:
            tag = Session.object_session(self).merge(tag)
            return [(tag, self.__tag_likelihood(tag))]

    def auto_tag(self, threshold=0.975):
        lh = sorted(self.tag_likelihood(), key=lambda tup: tup[1], reverse=True)
        if lh and lh[0][1] >= threshold:
            self.tags.clear()
            self.tags.append(TransactionTag(
                transaction=self,
                tag=lh[0][0],
                share=1.0))

    @property
    def timestamp(self):
        return date_to_timestamp(self.date)
