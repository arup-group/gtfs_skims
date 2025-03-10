import os

import pyproj

from gtfs_skims.utils import Config, GTFSData, get_logger, get_weekday, ts_to_sec


def filter_day(data: GTFSData, date: int) -> None:
    """Filter the GTFS for a specific date  in the calendar.

    Args:
        data (Data): GTFS data object
        date (int): Date as yyyymmdd
    """
    weekday = get_weekday(date)
    data.calendar = data.calendar[
        (data.calendar["start_date"] <= date)
        & (data.calendar["end_date"] >= date)
        & (data.calendar[weekday] == 1)
    ]

    data.calendar_dates = data.calendar_dates[
        data.calendar_dates["date"] == date
    ]

    service_ids = set(data.calendar["service_id"])
    service_ids |= set(data.calendar_dates[data.calendar_dates["exception_type"]==1]["service_id"])
    service_ids -= set(data.calendar_dates[data.calendar_dates["exception_type"]==2]["service_id"])

    data.trips = data.trips[data.trips["service_id"].isin(service_ids)]

    data.routes = data.routes[data.routes["route_id"].isin(set(data.trips["route_id"]))]

    data.stop_times = data.stop_times[data.stop_times["trip_id"].isin(set(data.trips["trip_id"]))]

    data.stops = data.stops[data.stops["stop_id"].isin(set(data.stop_times["stop_id"]))]


def filter_time(data: GTFSData, start_time: int, end_time: int) -> None:
    """Filter the GTFS for a specified time window.

    Args:
        data (Data): GTFS data object
        start_time (int): Start of the time window (seconds from midnight)
        end_time (int): End of the time window (seconds from midnight)
    """
    # filter stop times
    data.stop_times["departure_s"] = data.stop_times["departure_time"].apply(ts_to_sec)
    data.stop_times["arrival_s"] = data.stop_times["arrival_time"].apply(ts_to_sec)
    data.stop_times = data.stop_times[
        (data.stop_times["arrival_s"] >= start_time) & (data.stop_times["departure_s"] <= end_time)
    ]

    # filter stops
    data.stops = data.stops[data.stops["stop_id"].isin(set(data.stop_times["stop_id"]))]

    # filter trips
    data.trips = data.trips[data.trips["trip_id"].isin(set(data.stop_times["trip_id"]))]

    # filter routes
    data.routes = data.routes[data.routes["route_id"].isin(set(data.trips["route_id"]))]


def add_coordinates(data: GTFSData, epsg: int = 27700) -> None:
    """Add BNG coordinates to the stop and stoptime tables.

    Args:
        data (Data): Data object.
        epsg (int): The target coordinate system
    """
    transformer = pyproj.Transformer.from_crs(
        pyproj.transformer.CRS("epsg:4326"), pyproj.transformer.CRS(f"epsg:{epsg}"), always_xy=True
    )

    data.stops["x"], data.stops["y"] = transformer.transform(
        data.stops["stop_lon"], data.stops["stop_lat"]
    )

    data.stops["x"] = data.stops["x"].round().map(int)
    data.stops["y"] = data.stops["y"].round().map(int)

    data.stop_times["x"] = data.stop_times["stop_id"].map(data.stops.set_index("stop_id")["x"])
    data.stop_times["y"] = data.stop_times["stop_id"].map(data.stops.set_index("stop_id")["y"])


def filter_bounding_box(data: GTFSData, xmin: int, xmax: int, ymin: int, ymax: int) -> None:
    """Filter a GTFS with a bounding box. Coordinates are using the BNG projection.

    Args:
        data (Data): Data object.
        xmin (int): Min Easting.
        xmax (int): Max Easting.
        ymin (int): Min Northing.
        ymax (int): Max Northing
    """
    data.stops = data.stops[
        (data.stops["x"] >= xmin)
        & (data.stops["x"] <= xmax)
        & (data.stops["y"] >= ymin)
        & (data.stops["y"] <= ymax)
    ]

    # filter stop times
    data.stop_times = data.stop_times[
        data.stop_times["stop_id"].isin(set(list(data.stops["stop_id"])))
    ]

    # filter trips
    data.trips = data.trips[data.trips["trip_id"].isin(set(data.stop_times["trip_id"]))]

    # filter routes
    data.routes = data.routes[data.routes["route_id"].isin(set(data.trips["route_id"]))]


def main(config: Config) -> GTFSData:
    """Run the preprocessing pipeline and save resulting tables to disk.

    Args:
        config (Config): Config object.

    Returns:
        GTFSData: Pre-processed GTFS data object.
    """
    logger = get_logger(os.path.join(config.path_outputs, "log_preprocessing.log"))

    logger.info("Reading files...")
    data = GTFSData.from_gtfs(path_gtfs=config.path_gtfs)

    logger.info("Time filtering..")
    filter_day(data, config.calendar_date)
    filter_time(data, config.start_s, config.end_s)
    add_coordinates(data, epsg=config.epsg_centroids)

    if config.bounding_box is not None:
        logger.info("Cropping to bounding box..")
        filter_bounding_box(data, **config.bounding_box)

    logger.info(f"Saving outputs at {config.path_outputs}")
    data.save(config.path_outputs)

    logger.info("Preprocessing complete.")

    return data
