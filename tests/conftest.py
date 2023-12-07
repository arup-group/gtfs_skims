"""
Test fixtures for `gtfs_skims` package.
These fixtures will be available in any other test module.
E.g., you can define `response` as a fixture and then use it as an input argument in `test_core.py`:
```
def test_content(response):
    assert response.content
```
"""
import os
from pathlib import Path

import pytest

from gtfs_skims.utils import Config, GTFSData

TEST_DATA_DIR = os.path.join(Path(__file__).parent, 'test_data')


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/arup-group/cookiecutter-pypackage')


@pytest.fixture
def config():
    return Config.from_yaml(os.path.join(TEST_DATA_DIR, 'config_demo.yaml'))

@pytest.fixture
def gtfs_data():
    return GTFSData.from_gtfs(os.path.join(TEST_DATA_DIR, 'iow-bus-gtfs.zip'))