# Methodology

Argo calculates generalised time matrices between a set of origin and destination points.

Generalised time is defined as follows:

$$
gc = ivt + \beta_{wait} \cdot wait\_time + \beta_{walk} \cdot walk\_time + \beta_{interchange\_penalty} \cdot n\_transfers
$$

Some example values for the leg component weights are: 

$$
\beta_{wait} = \beta_{walk} = 2-3
$$

and 

$$
\beta_{\text{interchange\_penalty}} = 5 \text{ to } 10 \text{ minutes}
$$

Walk distance is calculated as the crow's fly distance between two points, multiplied by a factor specified in the config file (typically ~1.3).

The library creates a graph representation of the GTFS dataset, where the edges represent vehicle movements or connections (access/egress/transfer legs). It then applied a shortest-paths algorithm, using generalised time as edge weights.

To achieve high performance, the user can limit the search space by:
* selecting a time scope and maximum travel time
* selecting a specific day
* selecting a maximum walk, wait and trasfer time for legs
* applying a spatial bounding box

We further improve performance by:
* using K-dimensional trees to organise spatial data
* using the effiecient graph-tool library to calculate shortest distances
* parallelising the shortest distances calculation, and vectorising data transformation tasks
* saving files to a compressed parquet format