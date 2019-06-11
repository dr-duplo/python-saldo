import click
from colorama import Fore

from .transactions import print_transaction


class ClickProgressBarUpdater:
    def __init__(self, bar):
        self.bar = bar
        self.progress = 0

    def __call__(self, progress):
        self.bar.update(progress - self.progress)
        self.progress = progress


@click.command(name='fetch', help='Fetch and update account data.')
@click.option('--auto-tag', '-t', is_flag=True, help='Automatically tag new transactions.')
@click.option('--account-id', '-a', type=int, help='Account id to fetch data from.')
@click.pass_obj
def cli_fetch(model, auto_tag, account_id):
    # try get account from option
    account = model.accounts(id=account_id) if account_id else None

    if account:
        accounts = [account]
    else:
        accounts = model.accounts()

    for account in accounts:
        label = Fore.MAGENTA + "[%u]" % account.id + Fore.RESET
        label += " Fetching data from " + Fore.WHITE + account.name + Fore.RESET

        nt = []
        with click.progressbar(length=100, label=label) as bar:
            nt = model.fetch(auto_tag, account, ClickProgressBarUpdater(bar))

        for t in nt:
            print_transaction(t)
