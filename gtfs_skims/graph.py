import os

from graph_tool import Graph
from graph_tool.topology import shortest_distance
import numpy as np
import pandas as pd

from gtfs_skims.utils import Config, GTFSData, ConnectorsData, get_logger


def get_ivt_edges(stop_times: pd.DataFrame) -> pd.DataFrame:
    """Get in-vehicle times between stops.

    Args:
        stop_times (pd.DataFrame): The stoptimes GTFS table.

    Returns:
        np.ndarray: [origin id, destination id, in-vehicle time]
    """
    edges_ivt = pd.Series(range(len(stop_times)))
    trip_id = stop_times.reset_index()['trip_id']
    departures = stop_times.reset_index()['departure_s']

    edges_ivt = pd.concat([
        edges_ivt,
        edges_ivt.groupby(trip_id).shift(-1),
        departures.groupby(trip_id).shift(-1) - departures,
    ], axis=1).dropna().map(int)
    edges_ivt.columns = ['onode', 'dnode', 'ivt']

    return edges_ivt


def get_all_edges(gtfs_data: GTFSData, connectors_data: ConnectorsData) -> pd.DataFrame:
    """Get all edges for the accessibility graph.

    Args:
        gtfs_data (GTFSData): GTFS data object.
        connectors_data (ConnectorsData): Connectords data object.

    Returns:
        pd.DataFrame: ['onode', 'dnode', 'ivt', 'walk', 'wait', 'transfer']
    """
    edges = pd.concat([
        get_ivt_edges(gtfs_data.stop_times),
        connectors_data.connectors_transfer.assign(transfer=1),
        connectors_data.connectors_access,
        connectors_data.connectors_egress,
    ], axis=0).fillna(0).map(int)

    return edges
