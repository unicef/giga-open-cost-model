# Application Documentation

You can use the script below to run the total cost scenario by doing the following:

```bash
./total_cost_scenario.py --workspace <path-to-data-workspace>
					     --output-file <desired-output-file> # e.g. costs.csv
					     --scenario-type minimum-cost # minimum-cost, fiber, cellular, or satellite
```

The script above will use the school, fiber, and cellular data in the workspace specified, to create an output .csv table that contains cost information for each school in the input data set.
Additionally, you can specify the scenario type by choosing between a `minimum-cost` scenario or a single technology cost scenario (`fiber`, `cellular`, `satellite`).

You can generate a pairwise distance cache to help warm-start the models for efficient comput using the CLI below:

```bash
./giga/app/create_distance_cache.py --country brazil --workspace-directory <data-workspace>
```
You can select `sample`, `brazil`, or `rwanda` as countries.

After the run completes, the cache will be written to the workspace. If you load the model data space from that workspace, it will automatically use and load the distance cache for model calculations when it exists. 
