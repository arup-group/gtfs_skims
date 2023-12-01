

from gtfs_skims.utils import GTFSData, get_weekday


def filter_day(data: GTFSData, date: int) -> None:
    """Filter the GTFS for a specific date  in the calendar.

    Args:
        data (Data): GTFS data object
        date (int): Date as yyyymmdd
    """
    weekday = get_weekday(date)
    data.calendar = data.calendar[
        (data.calendar['start_date'] <= date) &
        (data.calendar['end_date'] >= date) &
        (data.calendar[weekday] == 1)
    ]

    data.trips = data.trips[
        data.trips['service_id'].isin(
            set(data.calendar['service_id'])
        )
    ]

    data.routes = data.routes[
        data.routes['route_id'].isin(
            set(data.trips['route_id'])
        )
    ]

    data.stop_times = data.stop_times[
        data.stop_times['trip_id'].isin(
            set(data.trips['trip_id'])
        )
    ]

    data.stops = data.stops[
        data.stops['stop_id'].isin(
            set(data.stop_times['stop_id'])
        )
    ]
