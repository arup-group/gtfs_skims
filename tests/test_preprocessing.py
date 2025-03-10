import os

import pandas as pd

from gtfs_skims import preprocessing


def test_filter_date(gtfs_data):
    assert 14 in gtfs_data.calendar.service_id.values
    preprocessing.filter_day(gtfs_data, 20180507)
    assert list(gtfs_data.calendar.service_id) == [14]
    assert set(gtfs_data.trips["service_id"]) == set([14])

def test_filter_calendar_dates(gtfs_data):
    gtfs_data.calendar_dates = pd.DataFrame([
        {"service_id": 900001, "date": 20180507, "exception_type": 1}, # add service
        {"service_id": 14, "date": 20180507, "exception_type": 2}, # remove service
    ])
    gtfs_data.trips = pd.concat([
        gtfs_data.trips,
        pd.DataFrame([
            {"route_id": 900001, "service_id": 900001, "trip_id": 900001}
        ])
    ], ignore_index=True)
    preprocessing.filter_day(gtfs_data, 20180507)
    assert 900001 in list(gtfs_data.trips["service_id"])
    assert 14 not in list(gtfs_data.trips["service_id"])


def test_filter_time(gtfs_data):
    start_time = 9 * 3600
    end_time = 10 * 3600
    preprocessing.filter_time(gtfs_data, start_time, end_time)
    assert gtfs_data.stop_times["arrival_s"].min() >= start_time
    assert gtfs_data.stop_times["departure_s"].max() <= end_time


def test_projected_coords_within_bounds(gtfs_data):
    preprocessing.add_coordinates(gtfs_data)
    # check that the BNG coordinates fall within an Isle-of-Wight bounding box
    xmin, ymin = 423104, 69171
    xmax, ymax = 471370, 101154

    assert gtfs_data.stops["x"].min() > xmin
    assert gtfs_data.stops["x"].max() < xmax
    assert gtfs_data.stops["y"].min() > ymin
    assert gtfs_data.stops["y"].max() < ymax


def test_within_bounding_box(gtfs_data):
    preprocessing.add_coordinates(gtfs_data)

    # filter for Cowes
    xmin, ymin = 447477, 92592
    xmax, ymax = 451870, 96909
    assert gtfs_data.stops["x"].min() < xmin
    preprocessing.filter_bounding_box(gtfs_data, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)

    assert gtfs_data.stops["x"].min() > xmin
    assert gtfs_data.stops["x"].max() < xmax
    assert gtfs_data.stops["y"].min() > ymin
    assert gtfs_data.stops["y"].max() < ymax


def test_run_preprocessing_demo(config, tmpdir):
    path_outputs = os.path.join(tmpdir, "outputs")
    config.path_outputs = path_outputs
    preprocessing.main(config)
    for x in ["calendar", "routes", "stops", "stop_times", "trips"]:
        assert os.path.exists(os.path.join(path_outputs, f"{x}.parquet.gzip"))
