# Running Argo

To run argo simply type this command on the command line:
```
gtfs_skims run <CONFIG_PATH>
```
, where <CONFIG_PATH> is the path to the config yaml file.

An example config file is shown below:
```
paths:
  path_gtfs: ./tests/test_data/iow-bus-gtfs.zip
  path_outputs: ./tests/test_data/outputs
  path_origins: ./tests/test_data/centroids.csv # path to the origin points
  path_destinations: ./tests/test_data/centroids.csv # path to the destination points

settings:
  calendar_date : 20190515 # yyyymmdd | Date for filtering the GTFS file.
  start_s : 32400 # sec | Start time of the journey.
  end_s : 41400 # sec | Max end time of a journey.
  walk_distance_threshold : 2000  # m | Max walk distance in a leg
  walk_speed : 4.5  # kph | Walking speed
  crows_fly_factor : 1.3 # Conversion factor from euclidean to routed distances
  max_transfer_time : 1800 # Max combined time of walking and waiting (sec) of a transfer
  max_wait : 1800  # sec | Max wait time at a stop / leg
  bounding_box : null
  epsg_centroids: 27700 # coordinate system of the centroids file. Needs to be Cartesian and in meters.
  weight_walk: 2 # value of walk time, ratio to in-vehicle time
  weight_wait: 2 # value of wait time, ratio to in-vehicle time
  penalty_interchange: 300 # seconds added to generalised cost for each interchange

steps:
  - preprocessing
  - connectors
  - graph
```

More information about the config can be found in the schema definition [here](https://github.com/arup-group/gtfs_skims/blob/main/gtfs_skims/config/schema.yaml).

To run the example provided by the repo, use:
```
gtfs_skims run ./tests/test_data/config_demo.yaml
```

The time matrices will be saved in the `output_path` directory defined in the config file, in the `skims.parquet.gzip` file. An easy way to read the file is with pandas:
```
import pandas as pd
df = pd.read_parquet('<OUTPUT_PATH>/skims.parquet.gzip')
df
```