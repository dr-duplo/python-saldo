import datetime

import click
from click_datetime import Datetime
from colorama import Fore, Back

from . import amount_to_str


@click.command(name='transactions', help='Show transactions.')
@click.option('--date', '-d', type=Datetime(format='%Y-%m-%d'), help='Date (or end of date range) to get balance for.')
@click.option('--from-date', '-f', type=Datetime(format='%Y-%m-%d'), help='Start of date range to get balance for.')
@click.option('--account-id', '-a', type=int, help='Account id to get transactions for.')
@click.option('--transaction-id', '-t', type=int, help='Specific transaction.')
@click.option('--untagged', '-u', type=int, help='Only untagged transactions.')
@click.option('--search', '-s', help='Text search in transactions.')
@click.pass_obj
def cli_transactions(model, date, from_date, account_id, transaction_id, untagged, search):
    account = model.accounts(id=account_id) if account_id else None

    # set default date range to current month
    to_date = date or datetime.date.today()
    if date and not from_date:
        from_date = to_date
    elif not date and not from_date:
        from_date = to_date.replace(day=1)

    search_token = None
    if search:
        import re
        matches = re.findall(r"((\"[^\"]{2,}\")|\S{2,})+", search)
        search_token = [m[0].strip('""') for m in matches] if matches else None

    transactions = ([model.transactions(id=transaction_id)] if transaction_id else None) \
                   or model.transactions(account=account, to_date=to_date, from_date=from_date, search=search_token)

    transaction_total = 0
    for t in transactions:
        print_transaction(t)
        transaction_total += t.value

    if search:
        print_transaction_total(transaction_total)


def print_transaction(t):
    line = Fore.MAGENTA + "[%5u]" % t.id
    line += Fore.CYAN + "@[%u]" % t.account.id
    line += Fore.RESET + " %s" % t.date
    line += " " + amount_to_str(t.value, t.value_currency)
    line += Fore.YELLOW + " " + " ".join(t.r_name.split() if t.r_name else ['-'])
    line += Fore.WHITE + " %s" % " ".join(t.purpose.split() if t.purpose else ['-'])
    line += Fore.RESET + (" %s" % t.tags[0].name) if t.tags else ''
    line += (" " + Back.RED + Fore.BLACK + "pre-booked") if t.pre_booked else ""

    click.echo(line + Fore.RESET + Back.RESET)

    # try:
    #    click.echo(pickle.loads(base64.b64decode(t.raw)))
    # except:
    #    pass


def print_transaction_total(transaction_total):
    line = Fore.WHITE + "-------"
    line += "----"
    line += " ---- Total"
    line += " " + amount_to_str(transaction_total, 'EUR')

    click.echo(line + Fore.RESET + Back.RESET)
