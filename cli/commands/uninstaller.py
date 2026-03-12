import click

@click.command()
def uninstall():
    """Uninstall a module"""
    click.echo("Uninstalling module...")