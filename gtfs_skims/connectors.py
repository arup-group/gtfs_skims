import os

import numpy as np
from scipy.spatial import KDTree

from gtfs_skims.utils import Config, GTFSData, get_logger


def query_pairs(coords: np.array, radius: float) -> np.array:
    ids = coords[:, 2].argsort()

    dtree = KDTree(coords[ids])
    connectors = dtree.query_pairs(r=radius, output_type='ndarray', p=2)

    return ids[connectors]


def query_pairs_filter(coords: np.array, maxdist: float) -> np.array:
    radius = maxdist * (2**0.5)
    connectors = query_pairs(coords, radius)
    coords_o = coords[connectors[:, 0]]
    coords_d = coords[connectors[:, 1]]

    dcoords = coords_d - coords_o
    walk = (dcoords[:, :2]**2).sum(1)**0.5  # euclidean distance on xy
    wait = dcoords[:, 2] - walk

    is_feasible = (wait > 0) & ((walk+wait) <= maxdist)
    connectors = connectors[is_feasible]

    return connectors


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
