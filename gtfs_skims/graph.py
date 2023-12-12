from functools import partial
import multiprocessing
from typing import Optional

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


def add_gc(edges: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Calculate generalised time and add it as a column to the 'edges' table.

    Args:
        edges (pd.DataFrame): Edges dataframe. Should include these columns: 
            ['ivt', 'walk', 'wait', 'transfer']
        config (Config): Config object.

    Returns:
        pd.DataFrame: Edges dataframe, with the generalised time ("gc") column included.
    """
    edges['gc'] = edges['ivt'] +\
        edges['walk'] * config.weight_walk +\
        edges['wait'] * config.weight_wait +\
        edges['transfer'] * config.penalty_interchange

    # adding unweighted time as well
    edges['time'] = edges[['ivt', 'walk', 'wait']].sum(1)

    return edges['gc']


def build_graph(
        edges: pd.DataFrame,
        vars=['ivt', 'walk', 'wait', 'time', 'gc']
) -> Graph:
    """Build a network graph from the edges table.

    Args:
        edges (pd.DataFrame): Edges table. Should include the 'gc' and 'time' columns from the 'add_gc' method.
        vars (list): list of variables to include in the graph as edge properties.

    Returns:
        Graph: Connected GTFS graph
    """
    eprops = [(x, 'int') for x in vars]
    g = Graph(
        edges[['onode', 'dnode']+vars].values,
        hashed=False,
        eprops=eprops
    )
    return g


def get_shortest_distances_single(
        graph: Graph,
        onode: int,
        dnodes: list[int],
        max_dist: Optional[float] = None,
        attribute: str = 'gc'
) -> np.ndarray:
    d = shortest_distance(graph, onode, dnodes,
                          weights=graph.edge_properties[attribute], dense=False,
                          max_dist=max_dist, directed=True)
    d = np.concatenate([np.array([onode]), d])

    return d


def get_shortest_distances(
        graph: Graph,
        onodes: list[int],
        dnodes: list[int],
        max_dist: Optional[float] = None,
        attribute: str = 'gc'
) -> pd.DataFrame:
    n_cpus = multiprocessing.cpu_count() - 1
    dist_wrapper = partial(get_shortest_distances_single, graph, dnodes=dnodes,
                           max_dist=max_dist, attribute=attribute)
    with multiprocessing.Pool(n_cpus) as pool_obj:
        dists = pool_obj.map(dist_wrapper, onodes)

    dists = np.array(dists)
    dists = dists[dists[:, 0].argsort()]  # sort by source node

    # convert to dataframe and reindex
    dists = pd.DataFrame(dists[:, 1:], index=dists[:, 0], columns=dnodes)
    dists = dists.loc[onodes]

    return dists


def main():
    pass
