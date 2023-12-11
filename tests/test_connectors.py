from collections import defaultdict
import itertools
import os

import numpy as np
import pytest
import unittest.mock as mock

from gtfs_skims import connectors, preprocessing


@pytest.fixture()
def points():
    p = np.arange(-20, 20, 2.5)
    coords = np.array([(x, y, z) for x, y, z in itertools.product(p, p, p)])
    return coords


@pytest.fixture()
def transfer_connectors(points):
    return connectors.TransferConnectors(points, 10)


def find_index(coords, x, y, z):
    idx = np.where(np.all(coords == np.array([x, y, z]), axis=1))[0][0]
    return idx


def get_valid_points(coords, source_idx, max_trasfer_dist):
    dcoords = coords - coords[source_idx]
    walk = (dcoords[:, :2]**2).sum(1)**0.5  # euclidean distance on xy
    wait = dcoords[:, 2] - walk

    is_valid = (wait > 0) & ((walk+wait) <= max_trasfer_dist)

    return is_valid


@pytest.mark.parametrize('source', [(0, 0, 0), (2.5, 2.5, 2.5), (-2.5, 0, 2.5)])
def test_query_all_valid_included(points, source):
    """ All valid points are included in the query results """
    source_idx = find_index(points, *source)
    maxdist = 10
    is_valid = get_valid_points(points, source_idx, maxdist)

    radius = maxdist * (2**0.5)
    ods = connectors.query_pairs(points, radius)

    dest = ods[ods[:, 0] == source_idx, 1]
    assert is_valid[dest].sum() == is_valid.sum()


@pytest.mark.parametrize('source', [(0, 0, 0), (2.5, 2.5, 2.5), (-2.5, 0, 2.5)])
def test_query_all_included_valid(points, source):
    """ All results from the query are valid """
    source_idx = find_index(points, *source)
    maxdist = 10
    is_valid = get_valid_points(points, source_idx, maxdist)

    tc = connectors.TransferConnectors(points, maxdist)
    tc.filter_feasible_transfer(maxdist)
    dest = tc.ods[tc.ods[:, 0] == source_idx, 1]

    assert is_valid[dest].sum() == is_valid.sum()
    assert len(is_valid[dest]) > 0 and all(is_valid[dest])


def test_filter_transfer_walk(transfer_connectors):
    max_walk = 5
    assert transfer_connectors.walk.max() > max_walk
    transfer_connectors.filter_max_walk(max_walk)
    assert transfer_connectors.walk.max() <= max_walk


def test_filter_transfer_wait(transfer_connectors):
    max_wait = 5
    assert transfer_connectors.wait.max() > max_wait
    transfer_connectors.filter_max_wait(max_wait)
    assert transfer_connectors.wait.max() <= max_wait


def test_filter_same_route(transfer_connectors):
    # assume all even-to-even point ID are in the same route
    routes = np.arange(len(transfer_connectors.coords))
    routes = np.where(routes % 2, -1, routes)
    transfer_connectors.filter_same_route(routes)
    assert (transfer_connectors.ods % 2).prod(1).sum() == 0


def get_o_service_transfers(conn, services_d):
    transfer_times = conn.wait + conn.walk
    d = defaultdict(list)
    for i in range(len(services_d)):
        d[(conn.ods[i, 0], services_d[i])
          ].append(transfer_times[i])
    return d


def test_filter_nearest_service(transfer_connectors):
    np.random.seed(0)
    services = np.random.randint(
        0, 2, size=transfer_connectors.coords.shape[0])
    services_d = services[transfer_connectors.ods[:, 1]]

    # for every origin-service pair there are multiple connections
    d_before = get_o_service_transfers(transfer_connectors, services_d)

    assert max(map(len, d_before.values())) > 0

    # after filtering, there is only one and it is the
    # one with the minumum transfer time.
    transfer_connectors.filter_nearest_service(services)
    services_d = services[transfer_connectors.ods[:, 1]]

    d_after = get_o_service_transfers(transfer_connectors, services_d)

    # didn't lose any origin-service pairs
    assert len(d_before) == len(d_after)
    # single connection per origin-service
    assert max(map(len, d_after.values())) == 1

    for o, service in d_before.keys():
        d_after[(o, service)][0] == min(d_before[(o, service)])


def test_get_transfer_array(gtfs_data_preprocessed, config):
    arr = connectors.get_transfer_connectors(gtfs_data_preprocessed, config)
    assert len(arr) > 0
    assert isinstance(arr, np.ndarray)


def test_get_od_pairs():
    ods = connectors.query_pairs_od(
        np.array([[0, 0], [1, 1]]),
        np.array([[0.5, 0.5], [2, 1], [2, 2]]),
        radius=1
    )
    expected = np.array([
        [0, 0],
        [1, 0],
        [1, 1]
    ])
    np.testing.assert_equal(ods, expected)


def test_get_od_walk():
    egress = connectors.AccessEgressConnectors(
        np.array([[0, 0], [1, 1]]),
        np.array([[0.5, 0.5], [2, 1], [2, 2]]),
        max_tranfer_distance=1
    )
    walk = egress.walk
    expected = np.array([
        (2*0.5**2)**0.5, (2*0.5**2)**0.5, 1
    ])
    np.testing.assert_almost_equal(walk, expected)


def test_convert_distance_3d():
    egress = connectors.AccessEgressConnectors(
        np.array([[0, 0, 0]]),
        np.array([[1, 1, 1]]),
        max_tranfer_distance=1
    )
    assert len(egress.ods) == 1  # radius has been adjusted to 3D space


def test_apply_crow_fly_factoring():
    pass


def test_access_indices_are_offset():
    pass


def test_egress_indices_are_offset():
    pass


def test_main_saves_outputs(config, gtfs_data_preprocessed, tmpdir):
    config.path_outputs = tmpdir
    connectors.main(config=config, data=gtfs_data_preprocessed)
    for x in ['transfer', 'access', 'egress']:
        assert os.path.exists(
            os.path.join(tmpdir, f'connectors_{x}.parquet.gzip')
        )