from colorama import Back, Fore
import click
from click_datetime import Datetime
from .transactions import print_transaction

@click.group(name='tags', help='Show and manage transaction tags.')
@click.pass_obj
def cli_tags(model):
    pass

@cli_tags.command(help="List all availabel tags.")
@click.pass_obj
def list(model):
    tags = model.tags()
    for t in tags:
        if not t.parent:
            print_tag(t, 0)

@cli_tags.command(help="Show tag likelihood for a transaction.")
@click.argument('transaction', type=int, required=True)
@click.argument('tag', required=False)
@click.pass_obj
def likelihood(model, transaction, tag):
    transaction = model.transactions(id=transaction)

    if not transaction:
        click.echo("Unknown transaction.")
        clic.abort()

    tags = None

    if tag:
        if tag.isdigit():
            tag = model.tags(id=tag)
        elif str(tag):
            tag = model.tags(name=tag)

        if not tag:
            click.echo("Unknown tag.")

    lh = transaction.tag_likelihood(tag)
    for tag, l in lh:
        line  = Fore.MAGENTA + "[%2u]" % tag.id
        line += Fore.YELLOW + " " + " %5.1f%%" % (l * 100)
        line += Fore.WHITE + " " + tag.name
        click.echo(line + Fore.RESET + Back.RESET)

@cli_tags.command(help="Assign tags to transactions.")
@click.argument('transaction', type=int, required=True)
@click.argument('tag', required=True)
@click.pass_obj
def assign(model, transaction, tag):
    transaction = model.transactions(id=transaction)

    if not transaction:
        click.echo("Unknown transaction.")
        clic.abort()

    if tag.isdigit():
        tag = model.tags(id=tag)
    elif str(tag):
        tag_name = tag
        tag = model.tags(name=tag_name)
        if not tag:
            if click.confirm('Create new tag [%s]?' % str(tag_name)):
                tag = model.create_tag(tag_name)
            else:
                clic.abort()

    if not tag:
        click.echo("Unknown tag.")

    model.assign_tag(transaction, tag)
    print_transaction(transaction)

def print_tag(tag, level, travers=True):
    line  = Fore.MAGENTA + "[%2u]" % tag.id
    line += Fore.WHITE + " " * (level + 1) + ("- " if level else "") + tag.name
    line += Fore.RESET + " " + " %u" % tag.usage()[0]

    click.echo(line + Fore.RESET + Back.RESET)

    if travers:
        for t in tag.children:
            print_tag(t, level + 1)
