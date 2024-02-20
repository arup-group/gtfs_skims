from __future__ import annotations

import os
from functools import cached_property
from typing import Optional

import numpy as np
import pandas as pd
from scipy.spatial import KDTree

from gtfs_skims.utils import Config, ConnectorsData, GTFSData, get_logger
from gtfs_skims.variables import DATA_TYPE


def query_pairs(coords: np.ndarray, radius: float) -> np.array:
    """Get origin-destination pairs between points, within a radius.
        The connections are forward-looking in z: ie the destination point
            has always greater z coordinate than the origin point.

    Args:
        coords (np.ndarray): Point coordinates (x, y, z)
        radius (float): Maximum distance between points

    Returns:
        np.array: Feasible connections between points.
    """
    ids = coords[:, 2].argsort()

    dtree = KDTree(coords[ids])
    connectors = dtree.query_pairs(r=radius, output_type="ndarray", p=2)

    return ids[connectors]


class TransferConnectors:
    def __init__(self, coords: np.ndarray, max_transfer_distance: float) -> None:
        """Manages transfer connectors.

        Args:
            coords (np.ndarray): Point coordinates (x, y, z)
            max_transfer_distance (float): Maximum distance between points
        """
        self.coords = coords
        radius = max_transfer_distance * (2**0.5)
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
        walk = ((self.dcoords[:, :2] - self.ocoords[:, :2]) ** 2).sum(1) ** 0.5
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

    def filter(self, cond: np.ndarray[bool]) -> None:
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
        is_feasible = (self.wait > 0) & ((self.walk + self.wait) <= maxdist)
        self.filter(is_feasible)

    def filter_max_walk(self, max_walk: float) -> None:
        """Remove any connections beyond a walk-distance threshold.

        Args:
            max_walk (float): Max walk distance
        """
        cond = self.walk <= max_walk
        self.filter(cond)

    def filter_max_wait(self, max_wait: float) -> None:
        """Remove any connections beyond a wait distance threshold.

        Args:
            max_wait (float): Maximum stop (leg) wait time.
        """
        self.filter(self.wait <= max_wait)

    def filter_same_route(self, routes: np.ndarray) -> None:
        """Remove connections between services of the same route.

        Args:
            routes (np.array): Route IDs array. Its indexing matches the self.coords table.
        """
        self.filter(routes[self.ods[:, 0]] != routes[self.ods[:, 1]])

    def filter_nearest_service(self, services: np.ndarray) -> None:
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
        order_o = int(np.floor(np.log10(services.max())) + 1)
        comb = (self.ods[:, 0] + 1) * 10**order_o + services_d

        # get first instance of each origin-service combination
        # (which corresponds to the most efficient transfer)
        keep = idx_sorted[np.unique(comb[idx_sorted], return_index=True)[1]]
        cond = np.isin(np.arange(len(comb)), keep)

        self.filter(cond)


def query_pairs_od(
    coords_origins: np.ndarray, coords_destinations: np.ndarray, radius: float
) -> np.array:
    """Get origin-destination pairs between points, within a radius.

    Args:
        coords_origins (np.array): Coordinates of origin points
        coords_destinations (np.array): Coordinates of destination points
        radius (float): Maximum distance between points

    Returns:
        np.array: Feasible connections between points.
    """
    tree_origins = KDTree(coords_origins)
    tree_destinations = KDTree(coords_destinations)

    ods = tree_origins.query_ball_tree(tree_destinations, r=radius)

    # flatten
    ods = np.column_stack(
        [np.repeat(range(len(coords_origins)), list(map(len, ods))), np.concatenate(ods)]
    ).astype(DATA_TYPE)

    return ods


class AccessEgressConnectors(TransferConnectors):
    """Connections between zones/endpoints and stops"""

    def __init__(
        self,
        coords_origins: np.ndarray,
        coords_destinations: np.ndarray,
        max_transfer_distance: float,
    ) -> None:
        self.coords_origins = coords_origins
        self.coords_destinations = coords_destinations

        radius = max_transfer_distance
        if coords_origins.shape[1] == 3:
            radius += max_transfer_distance * (2**0.5)

        self.ods = query_pairs_od(coords_origins, coords_destinations, radius=radius)

    @cached_property
    def ocoords(self) -> np.array:
        """Origin coordinates.

        Returns:
            np.array: x, y (, z)
        """
        return self.coords_origins[self.ods[:, 0]]

    @cached_property
    def dcoords(self) -> np.array:
        """Destination coordinates.

        Returns:
            np.array: x, y (,z)
        """
        return self.coords_destinations[self.ods[:, 1]]


def get_transfer_connectors(data: GTFSData, config: Config) -> np.array:
    """Get all transfer connectors (between stops).

    Args:
        data (GTFSData): GTFS data object.
        config (Config): Config object.

    Returns:
        np.ndarray: [origin id, destination id, walk time, wait time]
    """
    time_to_distance = config.walk_speed / 3.6  # km/hr to meters
    max_transfer_distance = config.max_transfer_time * time_to_distance
    max_wait_distance = config.max_wait * time_to_distance

    # get candidate connectors
    coords = data.stop_times[["x", "y", "departure_s"]].values
    coords[:, :2] = coords[:, :2] * config.crows_fly_factor  # crow's fly transformation
    tc = TransferConnectors(coords, max_transfer_distance)

    # apply more narrow filters:
    # enough time to make transfer
    tc.filter_feasible_transfer(max_transfer_distance)

    # maximum walk
    if config.walk_distance_threshold < max_transfer_distance:
        tc.filter_max_walk(config.walk_distance_threshold)

    # maximum wait
    if max_wait_distance < max_transfer_distance:
        tc.filter_max_wait(max_wait_distance)

    # not same route
    routes = data.stop_times["trip_id"].map(data.trips.set_index("trip_id")["route_id"]).values
    tc.filter_same_route(routes)

    # most efficient transfer to service
    services = data.stop_times["trip_id"].map(data.trips.set_index("trip_id")["service_id"]).values
    tc.filter_nearest_service(services)

    # construct array
    arr = (
        np.concatenate(
            [
                tc.ods,  # origin and destination index
                (tc.walk / time_to_distance).reshape(-1, 1),  # walk time (seconds)
                (tc.wait / time_to_distance).reshape(-1, 1),  # wait time (seconds)
            ],
            axis=1,
        )
        .round(1)
        .astype(DATA_TYPE)
    )

    return arr


def get_access_connectors(data: GTFSData, config: Config, origins: pd.DataFrame) -> np.ndarray:
    """Get all access connectors (between origins and stops).

    Args:
        data (GTFSData): GTFS data object.
        config (Config): Config object.
        origins (pd.DataFrame):
            Origin coordinates dataframe.
            Must include 'x' and 'y' columns, providing the cartesian coordinates of the trip start points.

    Returns:
        np.ndarray: [origin id, destination id, walk time, wait time]
    """
    time_to_distance = config.walk_speed / 3.6  # km/hr to meters
    max_transfer_distance = config.max_transfer_time * time_to_distance
    max_wait_distance = config.max_wait * time_to_distance

    # get candidate connectors
    coords_stops = data.stop_times[["x", "y", "departure_s"]].values
    coords_stops[:, :2] = coords_stops[:, :2] * config.crows_fly_factor  # crow's fly transformation
    coords_origins = (origins[["x", "y"]] * config.crows_fly_factor).assign(z=config.start_s).values

    ac = AccessEgressConnectors(coords_origins, coords_stops, max_transfer_distance)

    # more narrow filtering
    ac.filter_feasible_transfer(max_transfer_distance)
    if config.walk_distance_threshold < max_transfer_distance:
        ac.filter_max_walk(config.walk_distance_threshold)
    if max_wait_distance < max_transfer_distance:
        ac.filter_max_wait(max_wait_distance)

    arr = (
        np.concatenate(
            [
                ac.ods,  # origin and destination index
                (ac.walk / time_to_distance).reshape(-1, 1),  # walk time (seconds)
                (ac.wait / time_to_distance).reshape(-1, 1),  # wait time (seconds)
            ],
            axis=1,
        )
        .round(1)
        .astype(DATA_TYPE)
    )

    return arr


def get_egress_connectors(data: GTFSData, config: Config, destinations: pd.DataFrame) -> np.ndarray:
    """Get all egress connectors (between stops and destinations).

    Args:
        data (GTFSData): GTFS data object.
        config (Config): Config object.
        destinations (pd.DataFrame):
            Destination coordinates dataframe.
            Must include 'x' and 'y' columns, providing the cartesian coordinates of the trip ends.

    Returns:
        np.ndarray: [origin id, destination id, walk time, wait time]
    """
    time_to_distance = config.walk_speed / 3.6  # km/hr to meters

    # get candidate connectors
    coords_stops = data.stop_times[["x", "y"]].values
    coords_stops[:, :2] = coords_stops[:, :2] * config.crows_fly_factor  # crow's fly transformation
    coords_destinations = (destinations[["x", "y"]] * config.crows_fly_factor).values

    ec = AccessEgressConnectors(coords_stops, coords_destinations, config.walk_distance_threshold)

    arr = (
        np.concatenate(
            [
                ec.ods,  # origin and destination index
                (ec.walk / time_to_distance).reshape(-1, 1),  # walk time (seconds)
                np.array([0] * len(ec.ods)).reshape(-1, 1),  # wait time = 0
            ],
            axis=1,
        )
        .round(1)
        .astype(DATA_TYPE)
    )

    return arr


def main(config: Config, data: Optional[GTFSData] = None) -> ConnectorsData:
    """Get feasible connections (transfers, access, egress).

    Args:
        config (Config): Config object.
        data (Optional[GTFSData], optional): GTFS data object.
            If not provided, reads the stored parquet files from the outputs directory.
            Defaults to None.

    Returns:
        ConnectorsData: Connectors object, holding the three output tables.
    """
    logger = get_logger(os.path.join(config.path_outputs, "log_connectors.log"))

    if data is None:
        data = GTFSData.from_parquet(config.path_outputs)
    origins = pd.read_csv(config.path_origins, index_col=0)
    destinations = pd.read_csv(config.path_destinations, index_col=0)

    # get feasible connections
    logger.info("Getting transfer connectors...")
    connectors_transfer = get_transfer_connectors(data, config)
    logger.info("Getting access connectors...")
    connectors_access = get_access_connectors(data, config, origins)
    logger.info("Getting egress connectors...")
    connectors_egress = get_egress_connectors(data, config, destinations)

    # convert to dataframe
    colnames = ["onode", "dnode", "walk", "wait"]
    connectors_transfer = pd.DataFrame(connectors_transfer, columns=colnames)
    connectors_access = pd.DataFrame(connectors_access, columns=colnames)
    connectors_egress = pd.DataFrame(connectors_egress, columns=colnames)

    # offset IDs for endpoints
    connectors_access["onode"] += len(data.stop_times)
    connectors_egress["dnode"] += len(data.stop_times) + len(origins)

    # save
    logger.info(f"Saving connectors to {config.path_outputs}...")
    connectors = ConnectorsData(
        connectors_transfer=connectors_transfer,
        connectors_access=connectors_access,
        connectors_egress=connectors_egress,
    )
    connectors.save(config.path_outputs)

    return connectors
