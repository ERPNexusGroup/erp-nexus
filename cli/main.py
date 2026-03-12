import click
from rich.console import Console
from cli.commands.creator import create
from cli.commands.validator import validate
from cli.commands.installer import install
from cli.commands.uninstaller import uninstall

console = Console()

@click.group()
def cli():
    """ERP Nexus CLI Tool"""
    pass

cli.add_command(create)
cli.add_command(validate)
cli.add_command(install)
cli.add_command(uninstall)

if __name__ == '__main__':
    cli()