import click

@click.command()
def create():
    """Create a new module"""
    click.echo("Creating module...")