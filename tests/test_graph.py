import os

import numpy as np
import pandas as pd
import pytest

from gtfs_skims import graph


def test_get_ivt_times():
    stop_times = pd.DataFrame({
        'trip_id': [0, 1, 0, 1],
        'departure_s': [100, 105, 120, 150]
    })
    ivt_edges = graph.get_ivt_edges(stop_times)
    expected = np.array([
        [0, 2, 20],
        [1, 3, 45]
    ])
    np.testing.assert_equal(ivt_edges.values, expected)


def test_get_all_edges(gtfs_data_preprocessed, connectors_data):
    edges = graph.get_all_edges(gtfs_data_preprocessed, connectors_data)

    len_expected = len(gtfs_data_preprocessed.stop_times) - gtfs_data_preprocessed.stop_times['trip_id'].nunique()
    len_expected += len(connectors_data.connectors_transfer)
    len_expected += len(connectors_data.connectors_access)
    len_expected += len(connectors_data.connectors_egress)
    assert len(edges) == len_expected

    assert list(edges.columns) == [
        'onode', 'dnode', 'ivt', 'walk', 'wait', 'transfer']
