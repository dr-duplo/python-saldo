#!/usr/bin/env python3

import gettext
import os
from random import choice

import click
import click_log
import colorama
import keyring

from .cli.accounts import cli_accounts
from .cli.balances import cli_balances
from .cli.fetch import cli_fetch
from .cli.tags import cli_tags
from .cli.transactions import cli_transactions
from .model import Model, logger

colorama.init()

gettext.install("saldo")

click_log.basic_config(logger)


@click.group()
@click.option('--db',
              default=os.path.join(os.path.expanduser("~"), ".config/saldo/db.sqlite3"),
              type=click.Path(),
              help="Database file name")
@click.option('--db-password',
              hide_input=True,
              default=None,
              help="Database file password")
@click_log.simple_verbosity_option(logger)
@click.pass_context
def cli(ctx, db_password, db):
    keyring_avail = keyring.get_keyring() is not None

    if not os.path.isfile(db):
        click.echo("Database file %s doesn't exist." % db)
        if not click.confirm("Create it now?"):
            click.Abort()

        # generate password
        if keyring_avail and db_password is None:
            db_password = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789%^*(-_=+)') for i in range(16)])

    if keyring_avail and db_password is None:
        db_password = keyring.get_password("saldo", db);

    if not db_password:
        db_password = click.prompt("Please enter the database password", hide_input=True)

    assert (db_password is not None)

    if keyring_avail:
        keyring.set_password("saldo", db, db_password);

    ctx.obj = Model(db, db_password);


@cli.command(help="Start graphical user interface.")
@click.pass_obj
def gui(model):
    from saldo.gui import SaldoUi
    SaldoUi(model).run()


def main():
    cli.add_command(cli_fetch)
    cli.add_command(cli_accounts)
    cli.add_command(cli_balances)
    cli.add_command(cli_tags)
    cli.add_command(cli_transactions)
    cli(obj=None)


if __name__ == "__main__":
    main()
