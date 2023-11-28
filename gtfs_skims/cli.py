"""Console script for gtfs_skims."""

import click


@click.version_option(package_name="gtfs_skims")
@click.command()
def cli(args=None):
    """Console script for gtfs_skims."""
    click.echo(
        "Replace this message by putting your code into gtfs_skims.cli.cli"
    )
    click.echo("See click documentation at https://click.palletsprojects.com/")
    return 0
