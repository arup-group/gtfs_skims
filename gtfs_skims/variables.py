import numpy as np

DATA_TYPE = np.uint32

# route types lookup
# source: https://developers.google.com/transit/gtfs/reference#routestxt
# and https://developers.google.com/transit/gtfs/reference/extended-route-types
ROUTE_TYPES = {
    0: 'tram',  # Tram, Streetcar, Light rail.
    1: 'underground',  # Subway, Metro.
    2: 'rail',  # Rail. Used for intercity or long-distance travel.
    3: 'bus',  # Bus. Used for short- and long-distance bus routes.
    4: 'ferry',  # Ferry. Used for short- and long-distance boat service.
    5: 'cable',
    6: 'cable aerial',
    7: 'furnicular',  # Funicular. Any rail system designed for steep inclines.
    11: 'trolley',  # Trolleybus.
    12: 'monorail',  # Monorail.
    200: 'coach',  # Coach Service
    401: 'undergound',  # Metro Service
    402: 'underground',  # Underground Service
}