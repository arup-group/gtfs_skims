"""Console script for gtfs_skims."""

import click
from typing import Optional

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
@click.option("--output_directory_override", default=None, help="override output directory")
def run(config_path: str, output_directory_override: Optional[str] = None):
    config = Config.from_yaml(config_path)
    if output_directory_override is not None:
        config.path_outputs = output_directory_override
    steps = config.steps

    if 'preprocessing' in steps:
        main_preprocessing(config=config)

    if 'connectors' in steps:
        main_connectors(config=config)
