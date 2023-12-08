from __future__ import annotations
from dataclasses import dataclass
from functools import cached_property
import os
from typing import Optional

import numpy as np
from scipy.spatial import KDTree

from gtfs_skims.utils import Config, GTFSData, get_logger


def query_pairs(coords: np.array, radius: float) -> np.array:
    """Get origin-destination pairs between points, within a radius.
        The connections are forward-looking in z: ie the destination point
            has always greater z coordinate than the origin point.

    Args:
        coords (np.array): Point coordinates (x, y, z)
        radius (float): Maximum distance between points

    Returns:
        np.array: Feasible connections between points.
    """
    ids = coords[:, 2].argsort()

    dtree = KDTree(coords[ids])
    connectors = dtree.query_pairs(r=radius, output_type='ndarray', p=2)

    return ids[connectors]


@dataclass
class TransferConnector:
    """ Manages transfer connectors. """
    coords: np.array
    ods: np.array
    # route_id: np.array
    # service_id: np.array

    @cached_property
    def ocoords(self) -> np.array:
        """Origin coordinates.

        Returns:
            np.array: x, y, z
        """
        return self.coords[self.ods[:, 0]]

    @cached_property
    def dcoords(self) -> np.array:
        """Destination coordinates.

        Returns:
            np.array: x, y, z
        """
        return self.coords[self.ods[:, 1]]

    @cached_property
    def walk(self) -> np.array:
        """Walk distance (euclidean).

        Returns:
            np.array: Distance from origin to destination point (on the xy axis).
        """
        walk = ((self.dcoords[:, :2]-self.ocoords[:, :2])**2).sum(1)**0.5
        return walk

    @cached_property
    def wait(self) -> np.array:
        """Wait distance. It is calculated as the difference between timestamps (dz) 
            and the distance required to walk to the destination.

        Returns:
            np.array: Wait distance.
        """
        wait = self.dcoords[:, 2] - self.ocoords[:, 2] - self.walk
        return wait

    def filter(self, cond: np.array[bool]) -> TransferConnector:
        """Filter (in-place) Connnectors' origin-destination data based on a set of conditions.

        Args:
            cond np.array[bool]: The boolean condition filter to use.

        Returns:
            TransferConnector: Filtered Connectors object.
        """
        self.ods = self.ods[cond]
        self.ocoords = self.ocoords[cond]
        self.dcoords = self.dcoords[cond]
        self.walk = self.walk[cond]
        self.wait = self.wait[cond]
        # self.route_id = self.route_id[cond]
        # self.service_id = self.service_id[cond]

        return self

    def filter_feasible_transfer(self, maxdist):
        is_feasible = (self.wait > 0) & ((self.walk+self.wait) <= maxdist)
        return self.filter(is_feasible)

    def filter_max_walk(self, max_walk):
        pass

    def filter_max_wait(self, max_wait):
        pass

    def filter_same_route(self):
        pass


def get_transfer_connectors(data: GTFSData, config: Config):
    pass


def get_access_connectors(data: GTFSData, config: Config):
    # ... query ball tree
    pass


def get_egress_connectors(data: GTFSData, config: Config):
    # ... query ball tree
    pass


def main(data: GTFSData, config: Config):
    logger = get_logger(os.path.join(
        config.path_outputs, 'log_connectors.log'))

    # get feasible connections
    logger.info('Getting transfer connectors...')
    transfer_connectors = get_transfer_connectors(data, config)
    logger.info('Getting access connectors...')
    access_connectors = get_access_connectors(data, config)
    logger.info('Getting egress connectors...')
    egress_connectors = get_egress_connectors(data, config)

    # save
