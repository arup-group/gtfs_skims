import os
from pathlib import Path

import jsonschema
import yaml

CONFIG_DATA_DIR = os.path.join(Path(__file__).parent, "..", "config")
TEST_DATA_DIR = os.path.join(Path(__file__).parent, "test_data")


def test_config_schema(config):
    with open(os.path.join(CONFIG_DATA_DIR, "schema.yaml"), "r") as f:
        schema = yaml.safe_load(f)

    with open(os.path.join(TEST_DATA_DIR, "config_demo.yaml")) as f:
        config = yaml.safe_load(f)

    jsonschema.validate(config, schema)
