import click

@click.command()
def validate():
    """Validate a module"""
    click.echo("Validating module...")