import click
from click_datetime import Datetime
from colorama import Fore, Back

from . import amount_to_str


@click.command(name='balances', help="Show balances.")
@click.option('--date', '-d', type=Datetime(format='%Y-%m-%d'), help='Date to get balance for.')
@click.option('--pre-booked', '-p', is_flag=True, help='Show pre-booked balance if applicable.')
@click.option('--account-id', '-a', type=int, help='Account id to get balance for.')
@click.pass_obj
def cli_balances(model, date, pre_booked, account_id):
    # try find account from id
    account = model.account(id=account_id) if account_id else None

    # show single account
    if account:
        accounts = [account]
    # show all accounts
    else:
        accounts = model.accounts()

    # show them
    for account in accounts:
        print_balance(model.balances(account=account,
                                     date=date.date() if date else None,
                                     pre_booked=pre_booked))


def print_balance(balance):
    line = Fore.MAGENTA + "[%u]" % balance.account.id
    line += Fore.RESET + " %s" % balance.date
    line += " " + amount_to_str(balance.value, balance.currency)
    line += Fore.WHITE + " " + balance.account.name
    line += (" " + Back.RED + Fore.BLACK + "pre-booked") if balance.pre_booked else ""

    click.echo(line + Fore.RESET + Back.RESET)
