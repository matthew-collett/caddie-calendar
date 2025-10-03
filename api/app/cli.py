import click
from app.scheduler import processor as proc
from flask.cli import with_appcontext


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
