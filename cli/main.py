import click
from rich.console import Console

console = Console()

@click.group()
def cli():
    """ERP Nexus CLI Tool"""
    pass

if __name__ == '__main__':
    cli()