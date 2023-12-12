from functools import partial
import multiprocessing
import os
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

    return edges


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
    """Get shortest distances from a single origin.

    Args:
        graph (Graph): GTFS graph.
        onode (int): Source node.
        dnodes (list[int]): Destination nodes.
        max_dist (Optional[float], optional): Maximum search distance. Defaults to None.
        attribute (str, optional): Edge weights attribute. Defaults to 'gc'.

    Returns:
        np.ndarray: Shortest distances. The first value is the source node.
    """
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
    """Get shortest distances from a set of origins to a set of destinations.

    Args:
        graph (Graph): GTFS graph.
        onode (int): Source nodes.
        dnodes (list[int]): Destination nodes.
        max_dist (Optional[float], optional): Maximum search distance. Defaults to None.
        attribute (str, optional): Edge weights attribute. Defaults to 'gc'.

    Returns:
        pd.DataFrame: Shortest distances matrix.
            The dataframe indices are the origin nodes,
                and the column indices are the destination nodes.
    """
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


def main(
    config: Config,
    gtfs_data: Optional[GTFSData] = None,
    connectors_data: Optional[ConnectorsData] = None
) -> pd.DataFrame:
    # read
    logger = get_logger(os.path.join(
        config.path_outputs, 'log_graph.log'))

    logger.info('Reading files...')
    if gtfs_data is None:
        gtfs_data = GTFSData.from_parquet(path=config.path_outputs)
    if connectors_data is None:
        connectors_data = ConnectorsData.from_parquet(path=config.path_outputs)
    origins = pd.read_csv(config.path_origins, index_col=0)
    destinations = pd.read_csv(config.path_destinations, index_col=0)

    # graph
    logger.info('Building graph...')
    edges = get_all_edges(gtfs_data, connectors_data)
    edges = add_gc(edges=edges, config=config)
    g = build_graph(edges=edges)

    # shortest paths
    logger.info('Calculating shortest distances...')
    origins['idx'] = range(len(origins))
    origins['idx'] += len(gtfs_data.stop_times)
    destinations['idx'] = range(len(destinations))
    destinations['idx'] += (len(gtfs_data.stop_times)+len(origins))

    onodes_graph = list(origins[origins['idx'].isin(edges['onode'])]['idx'])
    dnodes_graph = list(
        destinations[destinations['idx'].isin(edges['dnode'])]['idx'])
    distmat = get_shortest_distances(
        g, onodes=onodes_graph, dnodes=dnodes_graph)

    # map labels
    distmat.index = distmat.index.map(
        origins.reset_index().set_index('idx')['name']
    )
    distmat.columns = distmat.columns.map(
        destinations.reset_index().set_index('idx')['name']
    )

    # diagonal infilling

    # save
    path = os.path.join(config.path_outputs, 'skims.parquet.gzip')
    logger.info(f'Saving results to {path}...')
    distmat.to_parquet(path, compression='gzip')

    return distmat
