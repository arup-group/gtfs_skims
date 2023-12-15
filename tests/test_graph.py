from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
from graph_tool import Graph

from gtfs_skims import graph


@pytest.fixture()
def mock_config(mocker):
    mock = Mock()
    mock.weight_wait = 3
    mock.weight_walk = 2
    mock.penalty_interchange = 600
    return mock


@pytest.fixture()
def small_graph() -> Graph:
    edges = pd.DataFrame({"onode": [0, 0, 1, 2], "dnode": [1, 2, 3, 3], "gc": [10, 20, 15, 4]})
    return graph.build_graph(edges, vars=["gc"])


@pytest.fixture()
def small_graph_birectional() -> Graph:
    edges = pd.DataFrame(
        {
            "onode": [0, 0, 1, 2, 1, 2, 3, 3],
            "dnode": [1, 2, 3, 3, 0, 0, 1, 2],
            "gc": [10, 20, 15, 4, 10, 20, 15, 4],
        }
    )
    return graph.build_graph(edges, vars=["gc"])


def test_get_ivt_times():
    stop_times = pd.DataFrame({"trip_id": [0, 1, 0, 1], "departure_s": [100, 105, 120, 150]})
    ivt_edges = graph.get_ivt_edges(stop_times)
    expected = np.array([[0, 2, 20], [1, 3, 45]])
    np.testing.assert_equal(ivt_edges.values, expected)


def test_get_all_edges(gtfs_data_preprocessed, connectors_data):
    edges = graph.get_all_edges(gtfs_data_preprocessed, connectors_data)

    # all connections are included
    len_expected = (
        len(gtfs_data_preprocessed.stop_times)
        - gtfs_data_preprocessed.stop_times["trip_id"].nunique()
    )
    len_expected += len(connectors_data.connectors_transfer)
    len_expected += len(connectors_data.connectors_access)
    len_expected += len(connectors_data.connectors_egress)
    assert len(edges) == len_expected

    # all variables are included
    assert list(edges.columns) == ["onode", "dnode", "ivt", "walk", "wait", "transfer"]


def test_calculate_gc(mock_config):
    edges = pd.DataFrame({"ivt": [100, 200], "walk": [30, 10], "wait": [10, 5], "transfer": [0, 1]})
    graph.add_gc(edges, mock_config)
    assert list(edges["gc"]) == [190, 835]


def test_get_shortest_distance_single(small_graph):
    dists = graph.get_shortest_distances_single(small_graph, 0, [3, 2, 1, 0])
    expected = np.array([24, 20, 10, 0])
    assert dists[0] == 0  # the first value is the source
    np.testing.assert_equal(dists[1:], expected)


def test_get_distance_matrix(small_graph_birectional):
    distmat = graph.get_shortest_distances(small_graph_birectional, [0, 1, 2], [1, 2])
    expected = np.array([[10, 20], [0, 19], [19, 0]])
    assert list(distmat.index) == [0, 1, 2]
    assert list(distmat.columns) == [1, 2]

    np.testing.assert_equal(distmat.values, expected)


def test_correct_labels(config, gtfs_data_preprocessed, connectors_data, tmpdir):
    origins = pd.read_csv(config.path_origins, index_col=0)
    destinations = pd.read_csv(config.path_destinations, index_col=0)
    config.path_outputs = tmpdir
    distmat = graph.main(
        config=config, gtfs_data=gtfs_data_preprocessed, connectors_data=connectors_data
    )

    assert list(distmat.index) == list(origins.index)
    assert list(distmat.columns) == list(destinations.index)
