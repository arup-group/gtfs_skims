"""Console script for gtfs_skims."""

import click


from gtfs_skims.preprocessing import main as main_preprocessing
from gtfs_skims.connectors import main as main_connectors
from gtfs_skims.utils import Config


@click.version_option(package_name="gtfs_skims")
@click.group
def cli(args=None):
    """Console script for gtfs_skims."""
    click.echo(
        "Console script for Argo (gtfs_skims)."
    )
    return 0


@cli.command()
@click.argument('config_path')
def run(config_path: str):
    config = Config.from_yaml(config_path)
    steps = config.steps

    if 'preprocessing' in steps:
        main_preprocessing(config=config)

    if 'connectors' in steps:
        main_connectors(config=config)
