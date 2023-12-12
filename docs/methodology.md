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

