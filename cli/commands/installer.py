import click

@click.command()
def install():
    """Install a module"""
    click.echo("Installing module...")