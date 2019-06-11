from urllib.parse import urlparse

import click
from colorama import Back, Fore
from schwifty import IBAN


@click.group(name='accounts', help='Show and manage accounts.')
@click.pass_obj
def cli_accounts(model):
    pass


@cli_accounts.command(help='List all accounts.')
@click.option('--all', '-a', is_flag=True, help='Show all')
@click.option('--secrets', '-s', is_flag=True, help='Show secrets, too!')
@click.pass_obj
def list(model, all, secrets):
    # reconfirm to show secrets
    secrets = secrets and click.confirm('Really show account login and password?')
    # gather accounts
    accounts = model.accounts()
    for account in accounts:
        print_account(account, all, secrets)


@cli_accounts.command(help="Add a new account")
@click.option('--name', '-n', prompt="Account name", required=True, help='Account name.')
@click.option('--owner', '-o', prompt="Account owner", required=True, help='Account owner.')
@click.option('--iban', '-i', prompt="Account IBAN", required=True, type=IBAN, help='Account IBAN.')
@click.option('--url', '-u', type=urlparse, help='Bank FinTS URL.')
@click.option('--login', '-l', prompt="Account login", required=True, help='Account login.')
@click.option('--password', '-p', prompt="Account password", hide_input=True, required=True, help='Account password.')
@click.option('--test', '-t', prompt="Test before adding", is_flag=True, help='Test account login before adding.')
@click.pass_obj
def add(model, name, owner, iban, url, login, password, test):
    import fints_url

    try:
        if not url:
            url = urlparse(fints_url.find(iban))
    except:
        url = click.prompt('Bank FinTS URL', type=urlparse)

    try:
        # test first
        if test:
            model.test_account(iban, url, login, password)
        # now add it
        account = model.add_account(name, owner, iban, url, login, password)
    except Exception as e:
        click.echo(str(e))
        click.Abort()
    else:
        click.echo("Account added")
        print_account(account, True)


def print_account(account, all=False, secrets=False):
    line = Fore.MAGENTA + "[%u]" % account.id
    line += " " + Fore.CYAN + account.account_iban.formatted
    line += " " + Fore.WHITE + account.name
    if all:
        line += " " + Fore.YELLOW + account.owner
        line += " " + Fore.RESET + account.url.geturl()
        if secrets:
            line += " " + Back.RED + Fore.BLACK + account.login
            line += " " + Back.RED + Fore.BLACK + account.pincode

    click.echo(line + Fore.RESET + Back.RESET)
