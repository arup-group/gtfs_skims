from __future__ import annotations

import logging
import os
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

import importlib_resources
import jsonschema
import pandas as pd
import yaml

from gtfs_skims import config as schema_dir


def ts_to_sec(x: str) -> int:
    """Convert a hh:mm:ss timestamp to seconds from midnight.

    Args:
        x (str): Timestamp

    Returns:
        int: Seconds from midnight
    """
    s = [int(i) for i in x.split(":")]
    return 3600 * s[0] + 60 * s[1] + s[2]


def get_weekday(date: int) -> str:
    """Get the weekday of a date

    Args:
        date (int): Date as yyyymmdd

    Returns:
        str: Day name
    """
    weekday = datetime.strptime(str(date), "%Y%m%d")
    weekday = datetime.strftime(weekday, "%A").lower()
    return weekday


def get_logger(path_output: Optional[str] = None) -> logging.Logger:
    """Get the library logger.

    Args:
        path_output (Optional[str], optional): Path to save the logs. Defaults to None.

    Returns:
        logging.Logger: Logger.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    if len(logger.handlers) == 0:
        logger.addHandler(handler)
    else:
        logger.handlers[0] = handler

    if path_output is not None:
        parent_dir = Path(path_output).parent.absolute()
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        file_handler = logging.FileHandler(path_output, mode="w")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_schema() -> dict:
    """Get the config schema.

    Returns:
        dict: Config yaml file schema.
    """
    path = importlib_resources.files(schema_dir).joinpath("schema.yaml")
    with open(path, "r") as f:
        schema = yaml.safe_load(f)
    return schema


@dataclass
class Config:
    """Config file

    Example config file:

    ```
    paths:
        path_gtfs: ./iow-bus-gtfs.zip
        path_outputs: /mnt/efs/otp/gtfs_transfers/skims_iow
        path_origins: ./centroids.csv # path to the origin points
        path_destinations: ./centroids.csv # path to the destination points

    settings:
        calendar_date : 20190515 # yyyymmdd | Date for filtering the GTFS file.
        start_s : 32400 # sec | Start time of the journey.
        end_s : 41400 # sec | Max end time of a journey.
        walk_distance_threshold : 2000  # m | Max walk distance in a leg
        walk_speed : 4.5  # kph | Walking speed
        crows_fly_factor : 1.3 # Conversion factor from euclidean to routed distances
        max_transfer_time : 1800 # Max combined time of walking and waiting (sec)
        k : 500 # max nearest neighbours when calculating distances
        max_wait : 1800  # sec | Max wait time at a stop
        bounding_box : null
        epsg_centroids: 27700 # coordinate system of the centroids file. Needs to be Cartesian and in meters.


    steps:
    - preprocessing
    - connectors
    - graph
    ```

    """

    path_gtfs: str
    path_outputs: str
    path_origins: str
    path_destinations: str
    calendar_date: int
    crows_fly_factor: float
    max_transfer_time: int
    end_s: int
    bounding_box: dict
    epsg_centroids: int
    max_wait: int
    start_s: int
    walk_distance_threshold: int
    walk_speed: float
    weight_walk: float
    weight_wait: float
    penalty_interchange: float
    steps: list

    @classmethod
    def from_yaml(cls, path: str) -> Config:
        """Construct class from a config yaml file.

        Args:
            path (str): Path to the yaml config.

        Returns:
            Config: Config object
        """
        with open(path, "r") as f:
            config = yaml.safe_load(f)

        # validate
        schema = get_schema()
        jsonschema.validate(config, schema, cls=jsonschema.Draft202012Validator)

        config_flat = {**config["paths"], **config["settings"], "steps": config["steps"]}
        return cls(**config_flat)

    def __repr__(self) -> str:
        s = "Config file\n"
        s += "-" * 50 + "\n"
        s += yaml.dump(self.__dict__)
        return s


@dataclass
class Data(ABC):
    @classmethod
    def from_gtfs(cls, path_gtfs: str) -> Data:
        """Load GTFS tables from a standard zipped GTFS file.

        Args:
            path_gtfs (str): Path to a zipped GTFS dataset.

        Returns:
            GTFSData: GTFS data object.
        """
        data = {}
        with ZipFile(path_gtfs, "r") as zf:
            for name in cls.__annotations__.keys():
                with zf.open(f"{name}.txt") as f:
                    data[name] = pd.read_csv(f, low_memory=False)
        return cls(**data)

    @classmethod
    def from_parquet(cls, path: str) -> Data:
        """Construct class from pre-processed GTFS tables in Parquet format.

        Args:
            path (str): Path to tables.

        Returns:
            GTFSData: GTFS data object.
        """
        data = {}
        for name in cls.__annotations__.keys():
            data[name] = pd.read_parquet(os.path.join(path, f"{name}.parquet.gzip"))
        return cls(**data)

    def save(self, path_outputs: str) -> None:
        """Export all tables in zipped parquet format.

        Args:
            path_outputs (str): Directory to save outputs.
        """
        if not os.path.exists(path_outputs):
            os.makedirs(path_outputs)

        for k, v in self.__dict__.items():
            v.to_parquet(os.path.join(path_outputs, f"{k}.parquet.gzip"), compression="gzip")


@dataclass
class GTFSData(Data):
    calendar: pd.DataFrame
    calendar_dates: pd.DataFrame
    routes: pd.DataFrame
    stops: pd.DataFrame
    stop_times: pd.DataFrame
    trips: pd.DataFrame


@dataclass
class ConnectorsData(Data):
    connectors_transfer: pd.DataFrame
    connectors_access: pd.DataFrame
    connectors_egress: pd.DataFrame
