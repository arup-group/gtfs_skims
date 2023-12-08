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


class TransferConnectors:
    """ Manages transfer connectors. """

    def __init__(self, coords: np.array, max_tranfer_distance: float) -> None:
        self.coords = coords
        radius = max_tranfer_distance * (2**0.5)
        self.ods = query_pairs(coords, radius=radius)

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

    def filter(self, cond: np.array[bool]) -> None:
        """Filter (in-place) Connnectors' origin-destination data based on a set of conditions.

        Args:
            cond np.array[bool]: The boolean condition filter to use.
        """
        ods = self.ods
        ocoords = self.ocoords
        dcoords = self.dcoords
        walk = self.walk
        wait = self.wait

        self.ods = ods[cond]
        self.ocoords = ocoords[cond]
        self.dcoords = dcoords[cond]
        self.walk = walk[cond]
        self.wait = wait[cond]

        return self

    def filter_feasible_transfer(self, maxdist: float) -> None:
        """Remove any connections with insufficient transfer time.


        Args:
            maxdist (float): Maximum transfer distance (walk+wait)
        """
        is_feasible = (self.wait > 0) & ((self.walk+self.wait) <= maxdist)
        self.filter(is_feasible)

    def filter_max_walk(self, max_walk: float) -> None:
        """Remove any connections beyond a walk-distance threshold.

        Args:
            max_walk (float): Max walk distance
        """
        cond = (self.walk <= max_walk)
        self.filter(cond)

    def filter_max_wait(self, max_wait: float) -> None:
        """Remove any connections beyond a wait distance threshold.

        Args:
            max_wait (float): Maximum stop (leg) wait time.
        """
        self.filter(self.wait <= max_wait)

    def filter_same_route(self, routes: np.array) -> None:
        """Remove connections between services of the same route.

        Args:
            routes (np.array): Route IDs array. Its indexing matches the self.coords table.
        """
        self.filter(
            routes[self.ods[:, 0]] != routes[self.ods[:, 1]]
        )

    def filter_nearest_service(self, services: np.array) -> None:
        """If a service can be accessed from a origin through multiple stops,
            then only keep the most efficient transfer for that connection.

        Args:
            services (np.array): Service IDs array. Its indexing must match the self.coords table.
        """
        services_d = services[self.ods[:, 1]]  # destination service

        # sort by trasfer distance
        transfer = self.wait + self.walk
        idx_sorted = transfer.argsort()

        # create origin-service combinations
        order_o = int(np.floor(np.log10(services.max()))+1)
        comb = (self.ods[:, 0]+1) * 10**order_o + services_d

        # get first instance of each origin-service combination
        # (which corresponds to the most efficient transfer)
        keep = idx_sorted[np.unique(comb[idx_sorted], return_index=True)[1]]
        cond = np.isin(np.arange(len(comb)), keep)

        self.filter(cond)


def get_transfer_connectors(data: GTFSData, config: Config) -> np.array:
    time_to_distance = config.walk_speed/3.6  # km/hr to meters
    max_tranfer_distance = config.max_transfer_time * time_to_distance
    max_wait_distance = config.max_wait * time_to_distance

    # get candidate connectors
    coords = data.stop_times[['x', 'y', 'departure_s']]
    tc = TransferConnectors(coords, max_tranfer_distance)

    # apply narrower filters
    tc.filter_feasible_transfer(max_tranfer_distance)

    if config.walk_distance_threshold < max_tranfer_distance:
        tc.filter_max_walk()

    if max_wait_distance < max_tranfer_distance:
        tc.filter_max_wait()

    routes = data.stop_times['trip_id'].map(
        data.trips.set_index('trip_id')['route_id']
    )
    tc.filter_same_route(routes)

    services = data.stop_times['trip_id'].map(
        data.trips.set_index('trip_id')['service_id']
    )
    tc.filter_nearest_service(services)

    arr = np.array([
        tc.ods[:, 0],  # origin index
        tc.ods[:, 1],  # destination index
        tc.walk,  # walk distance (meters)
        tc.wait/time_to_distance*3600  # wait time (seconds???)
    ])
    return arr


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
