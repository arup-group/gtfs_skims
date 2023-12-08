import itertools

import numpy as np
import pytest

from gtfs_skims import connectors


@pytest.fixture()
def points():
    p = np.arange(-20, 20, 2.5)
    coords = np.array([(x, y, z) for x, y, z in itertools.product(p, p, p)])
    return coords


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
    radius = maxdist * (2**0.5)
    ods = connectors.query_pairs_filter(points, radius)
    is_valid = get_valid_points(points, source_idx, maxdist)

    ds = ods[ods[:, 0] == source_idx, 1]
    assert is_valid[ds].sum() == is_valid.sum()


@pytest.mark.parametrize('source', [(0, 0, 0), (2.5, 2.5, 2.5), (-2.5, 0, 2.5)])
def test_query_all_included_valid(points, source):
    """ All results from the query are valid """
    source_idx = find_index(points, *source)
    maxdist = 10
    
    ods = connectors.query_pairs_filter(points, maxdist)
    is_valid = get_valid_points(points, source_idx, maxdist)

    ds = ods[ods[:, 0] == source_idx, 1]
    assert all(is_valid[ds])
