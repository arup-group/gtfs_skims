import os
from pathlib import Path

import importlib_resources
import jsonschema
import yaml

from gtfs_skims import config as schema_dir

TEST_DATA_DIR = os.path.join(Path(__file__).parent, "test_data")


def test_config_schema():
    path = importlib_resources.files(schema_dir).joinpath("schema.yaml")
    with open(path, "r") as f:
        schema = yaml.safe_load(f)

    with open(os.path.join(TEST_DATA_DIR, "config_demo.yaml")) as f:
        config = yaml.safe_load(f)

    jsonschema.validate(config, schema, cls=jsonschema.Draft202012Validator)
