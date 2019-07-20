import base64
import logging
import pickle
import re
import time
from datetime import datetime, time as dtime, date, timedelta

import sqlparse
from fints.client import FinTS3PinTanClient
from schwifty import IBAN
from sqlalchemy import create_engine, text, exc, desc, or_
from sqlalchemy.orm import sessionmaker, scoped_session, load_only

from .orm import INIT_SQL
from .orm.account import Account
from .orm.balance import Balance, balance_hash
from .orm.tag import Tag
from .orm.transaction import Transaction, transaction_hash
from .orm.transaction_tag import TransactionTag

logger = logging.getLogger("saldo." + __name__)

# Saldo product id from registrierung@hbci-zka.de
_SALDO_PRODUCT_ID = 'B82657106E79F1BBD33E7366F'

class Model:
    def __init__(self, db_file: str, password: str):
        logger.debug("Using %s" % db_file)

        # create database engine/session
        self.__engine = create_engine("sqlite+pysqlcipher://:%s@/%s" % (password, db_file))
        # scoped session
        self.__session = scoped_session(sessionmaker(bind=self.__engine))

        # init DB structure
        for s in sqlparse.split(INIT_SQL):
            self.__session().execute(text(s))

    def tags(self, id=None, name=None):
        if id:
            return self.__session().query(Tag).filter(Tag.id == id).first()
        elif name:
            return self.__session().query(Tag).filter(Tag.name.like(name)).first()
        else:
            return self.__session().query(Tag).all()

    def create_tag(self, name):
        session = self.__session()
        tag = Tag(name=name)
        session.add(tag)
        session.commit()
        return tag

    def assign_tag(self, transaction, tag, share_value=None):
        session = self.__session.object_session(transaction)
        transaction.tags.clear()
        if transaction and tag:
            session.merge(tag)
            print(transaction, tag, share_value, (share_value / transaction.value) if share_value is not None else None)
            transaction.tags.append(TransactionTag(
                transaction_id=transaction.id,
                tag_id=tag.id,
                share=(share_value / transaction.value) if share_value is not None else None))
        session.commit()

    def transactions(self, id=None, hash=None, account=None, from_date=None, to_date=None, search=None, cols=None,
                     transfer=None):
        if id:
            return self.__session().query(Transaction).get(id)
        elif hash:
            return self.__session().query(Transaction).filter(Transaction.hash == hash).first()
        else:
            query = self.__session().query(Transaction)

            if account is None and transfer is not None:
                query = query.outerjoin(Account, Transaction.r_account_iban == Account.account_iban)
                if transfer == True:
                    query = query.filter(Account.id.isnot(None))
                elif transfer == False:
                    query = query.filter(Account.id == None)

            if account:
                query = query.filter(Transaction.account == account)
            if from_date:
                query = query.filter(Transaction.date >= from_date)
            if to_date:
                query = query.filter(Transaction.date <= to_date)
            if search:
                if isinstance(search, str):
                    search = [search]

                # find tags with given search terms
                tag_ids = [t.id for t in self.__session().query(Tag.id).filter(
                    or_(*[Tag.name.like("%%%s%%" % v) for v in search])).all()]

                # regex for value terms
                value_regex = r"^[+-]?[1-9][0-9]*([,.][0-9]+)?$"

                # find transactions with given search terms/values or tag ids
                query = query.filter(or_(
                    or_(*[Transaction.r_name.like("%%%s%%" % v) for v in search]),
                    or_(*[Transaction.purpose.like("%%%s%%" % v) for v in search]),
                    or_(Transaction.value.in_(
                        [float(v.replace(',', '.')) for v in search if re.match(value_regex, v)])),
                    or_(Transaction.tags.any(TransactionTag.tag_id.in_(tag_ids)))))

            if cols:
                query = query.options(load_only(*cols))

            return query.order_by(desc(Transaction.date))

    def accounts(self, id=None):
        if id:
            return self.__session().query(Account).get(id)
        else:
            return self.__session().query(Account).all()

    @staticmethod
    def test_account(iban, url, login, password):
        client = FinTS3PinTanClient(
            iban.bank_code,
            login,
            password,
            url.geturl()
        )

        # find account we are looking for
        sepa_accounts = client.get_sepa_accounts()

        try:
            sepa_account = [a for a in sepa_accounts if a.iban == iban][0]
        except IndexError:
            # remote sepa accounts don't include requested one
            logger.exception("Account with iban %s not found" % iban)

    def add_account(self, name, owner, iban, url, login, password):
        a = Account(
            owner=owner,
            name=name,
            bank_country=iban.country_code,
            bank_branch_id=iban.bic.branch_code if iban.bic else None,
            account_number=iban.account_code,
            account_iban=iban,
            bank_code=iban.bank_code,
            url=url,
            login=login,
            pincode=password)

        self.__session().add(a);
        try:
            self.__session().commit();
        except exc.IntegrityError:
            raise Exception("Account already exists.")

        return a

    def balances(self, account=None, date=None, hash=None, from_date=None, to_date=None, pre_booked=False):
        if account:
            account = self.__session().merge(account)

            if date:  # get balance of specific date
                sql = text("""
                    SELECT base_value + IFNULL(delta_value, 0), currency FROM (
                    SELECT b.value AS base_value, b.sign_delta_date * SUM(t.value) AS delta_value, b.currency FROM
                    (
                        SELECT
                            id,
                            account_id,
                            date,
                            target_date,
                            value,
                            currency,
                            ABS(target_date - date) AS delta_date,
                            ((target_date >= date) * 2 - 1) AS sign_delta_date
                        FROM balances
                        JOIN (SELECT :target_date AS target_date)
                        ON account_id=:account_id ORDER BY delta_date ASC, id DESC LIMIT 1
                    ) AS b LEFT OUTER JOIN transactions AS t
                    ON t.account_id = b.account_id AND (
                        (b.sign_delta_date == 1 AND t.date > b.date AND t.date <= b.target_date) OR
                        (b.sign_delta_date == -1 AND t.date <= b.date AND t.date > b.target_date)
                    ));""")

                d = int(
                    time.mktime(datetime.combine(date, dtime(hour=23, minute=59, second=59, tzinfo=None)).timetuple()));
                b = self.__session().execute(sql,
                                             {'target_date': d, 'account_id': account.id}
                                             ).fetchall()[0]

                return Balance(account=account, date=date, value=b[0], currency=b[1])

            elif from_date and to_date:  # get daily balances of a date range
                d = from_date
                delta = timedelta(days=1)
                b = {}
                balances = []
                while d <= to_date:
                    balances.append(self.balances(account=account, date=d))
                    d += delta

                return balances

            elif pre_booked:  # get pre-booked balance
                return self.balances(account=account, date=account.transactions[0].date)

            else:  # get most recent balance available
                return self.__session().query(Balance) \
                    .filter(Balance.account_id == account.id) \
                    .order_by(Balance.date.desc()) \
                    .limit(1).first()
        elif hash:
            return self.__session().query(Balance) \
                .filter(Balance.hash == hash) \
                .order_by(Balance.date.desc()) \
                .limit(1).first()
        else:
            raise Exception("No account/date/date range or hash given.")

    @staticmethod
    def _multi_progress(total_steps, n_steps, sub_progress):
        return n_steps / total_steps * 100 + sub_progress / total_steps

    def refresh(self):
        self.__session().expire_all()

    def fetch(self, auto_assign=True, account=None, progress_callback=None):

        # acquire target account(s)
        if account:
            accounts = [self.__session().merge(account)]
        else:
            accounts = self.__session().query(Account).all()

        # container for newly imported transactions
        new_transactions = []

        # do for all target accounts
        for i, account in enumerate(accounts):

            # report progress and eventually cancel fetch
            if progress_callback and progress_callback(self._multi_progress(len(accounts), i, 0)):
                return None

            logger.debug("Fetching transactions for %s" % account.account_iban)

            # setup fints client
            client = FinTS3PinTanClient(
                bank_identifier=account.bank_code,
                user_id=account.login,
                pin=account.pincode,
                server=account.url.geturl(),
                product_id=_SALDO_PRODUCT_ID
            )

            # find account we are looking for
            try:
                # request sepa accounts
                sepa_accounts = client.get_sepa_accounts()
                sepa_account = [a for a in sepa_accounts if a.iban == account.account_iban][0]
            except IndexError:
                # remote sepa accounts don't include requested one
                logger.error("Account %s not found" % account)
                continue

            # report progress and eventually cancel fetch
            if progress_callback and progress_callback(self._multi_progress(len(accounts), i, 10)):
                return None

            # get account balance
            balance = client.get_balance(sepa_account)

            # report progress and eventually cancel fetch
            if progress_callback and progress_callback(self._multi_progress(len(accounts), i, 40)):
                return None

            # request all available account transactions
            try:
                statements = client.get_transactions(sepa_account)
            except Exception as e:
                logger.error("Error gathering account transactions", exc_info=e)
                continue

            # report progress and eventually cancel fetch
            if progress_callback and progress_callback(self._multi_progress(len(accounts), i, 60)):
                return None

            transactions = []
            hashes = []
            oldest_date = date.today()

            for j, s in enumerate(statements):
                # construct transaction object

                # report progress and eventually cancel fetch
                if progress_callback and progress_callback(
                        self._multi_progress(len(accounts), i, 60 + (j / len(statements)) * 20)):
                    return None

                raw = base64.b64encode(pickle.dumps(s.data))

                try:
                    bic = None
                    iban = IBAN(s.data['applicant_iban']) if s.data['applicant_iban'] else None
                except ValueError:
                    # fallback to account IBAN
                    # this transactions comes most likely from accounts bank
                    iban = None
                    bic = account.account_iban.bic

                try:
                    bic = bic or (iban.bic if iban else None)
                except ValueError:
                    bic = None

                th = transaction_hash(
                    account_id=account.id,
                    date=s.data['date'],
                    r_account_iban=iban,
                    r_bank_code=iban.bank_code if iban else None,
                    r_bank_branch_id=bic.branch_code if bic else None,
                    r_account_number=iban.account_code if iban else None,
                    value=s.data['amount'].amount
                )

                oldest_date = min(oldest_date, s.data['date'])
                hashes.append(th)

                # import transaction if not already in db
                if not self.__session().query(Transaction).filter(Transaction.hash == th).count():
                    t = Transaction(
                        account_id=account.id,
                        account=account,
                        r_country=iban.country_code if iban else None,
                        r_bank_code=iban.bank_code if iban else None,
                        r_bank_branch_id=bic.branch_code if bic else None,
                        r_account_number=iban.account_code if iban else None,
                        r_account_suffix=None,
                        r_account_iban=iban,
                        r_name=s.data['applicant_name'],
                        r_bic=bic.compact if bic else None,
                        date=s.data['date'],
                        valuta_date=s.data['entry_date'] if 'entry_date' in s.data else s.data['date'],
                        value=s.data['amount'].amount,
                        value_currency=s.data['amount'].currency,
                        fees=None,
                        fees_currency=None,
                        type_code=s.data['id'],
                        purpose=s.data['purpose'],
                        raw=raw
                    )

                    # skipping standing orders
                    # e.g. norisbank issues this before the final transaction
                    if s.data['id'].upper() == 'NSTO':
                        logger.info("Skipping standing order: %s" % str(t))
                        continue

                    self.__session().add(t)
                    transactions.append(t)

            # try find transactions that aren't there anymore (error of bank)
            # hacki workaround for transactions which disappear after some time
            orphaned_transactions = self.__session().query(Transaction) \
                .filter(Transaction.account == account) \
                .filter(Transaction.date > oldest_date + timedelta(days=1)) \
                .filter(~Transaction.hash.in_(hashes)).all()

            for t in orphaned_transactions:
                logger.info("Delete Orphaned Transactions (omitted): %s" % t)
                # FIXME self.__session().delete(t)

            # construct balance object
            b = Balance(
                account_id=account.id,
                account=account,
                date=balance.date,
                value=balance.amount.amount,
                currency=balance.amount.currency)

            # import balance if not already in db
            if not self.__session().query(Balance).filter(Balance.hash == balance_hash(**b.__dict__)).count():
                self.__session().add(b)
                logger.debug("Imported: %s" % b)

            # commit transactions
            self.__session().commit()

            # automatically assign tags to them
            for j, t in enumerate(transactions):

                # report progress and eventually cancel fetch
                if progress_callback and progress_callback(
                        self._multi_progress(len(accounts), i, 80 + (j / len(transactions)) * 20)):
                    return None

                if auto_assign:
                    t.auto_tag()

                logger.debug("Imported: %s" % t)

            # commit assignments
            self.__session().commit()

            # collect new transactions
            new_transactions.extend(transactions)

        if progress_callback:
            progress_callback(100)

        return new_transactions
