import click
from flask import current_app as app
from flask.cli import with_appcontext
from app import service as svc, utils
from app.scheduler import processor as proc


@click.group()
def processor():
    pass


@processor.command()
@with_appcontext
def process():
    proc.preflight()
    proc.process()


def init_app(app):
    app.cli.add_command(processor)
