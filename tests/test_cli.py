"""Tests for `gtfs_skims` CLI."""
import os
from pathlib import Path

from click.testing import CliRunner

from gtfs_skims import cli

TEST_DATA_DIR = os.path.join(Path(__file__).parent, 'test_data')


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.cli)
    assert result.exit_code == 0
    help_result = runner.invoke(cli.cli, ["--help"])
    assert help_result.exit_code == 0
    assert (
        "Console script for gtfs_skims.\n\nOptions:\n  "
        "--version  Show the version and exit.\n  "
        "--help     Show this message and exit.\n"
        in help_result.output
    )


def test_run_steps_saves_outputs(tmpdir):
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ['run', os.path.join(TEST_DATA_DIR, 'config_demo.yaml'),
         '--output_directory_override', tmpdir]
    )

    assert result.exit_code == 0

    for x in ['calendar', 'routes', 'stops', 'stop_times', 'trips']:
        assert os.path.exists(
            os.path.join(tmpdir, f'{x}.parquet.gzip')
        )

    for x in ['transfer', 'access', 'egress']:
        assert os.path.exists(
            os.path.join(tmpdir, f'connectors_{x}.parquet.gzip')
        )