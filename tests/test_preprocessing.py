from gtfs_skims import preprocessing


def test_filter_date(gtfs_data):
    a = 1
    assert 14 in gtfs_data.calendar.service_id.values
    preprocessing.filter_day(gtfs_data, 20180507)
    assert list(gtfs_data.calendar.service_id) == [14]
    assert set(gtfs_data.trips['service_id']) == set([14])
