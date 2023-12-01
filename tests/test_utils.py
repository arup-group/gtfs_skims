import os

import pandas as pd

from gtfs_skims import utils


def test_parse_timestamp():
    assert utils.ts_to_sec('00:00:00') == 0
    assert utils.ts_to_sec('10:01:01') == 36061


def test_get_logger(tmpdir):
    logger = utils.get_logger(os.path.join(tmpdir, 'logs', 'log.log'))
    logger.info('test')


def test_weekday():
    assert utils.get_weekday(20231201) == 'friday'


def test_load_config(config):
    'path_gtfs' in config.__dict__


def test_load_gtfs(gtfs_data):
    for x in ['calendar', 'routes', 'stops', 'stop_times', 'trips']:
        assert isinstance(getattr(gtfs_data, x), pd.DataFrame)


def test_cache_gtfs(gtfs_data, tmpdir):
    gtfs_data.save(tmpdir)
    gtfs_cached = utils.GTFSData.from_parquet(tmpdir)
    for x in ['calendar', 'routes', 'stops', 'stop_times', 'trips']:
        pd.testing.assert_frame_equal(
            getattr(gtfs_data, x), getattr(gtfs_cached, x)
        )
