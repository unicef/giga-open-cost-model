# Application Documentation

You can use the script below to run the total cost scenario by doing the following:

```bash
./total_cost_scenario.py --workspace <path-to-data-workspace>
					     --output-file <desired-output-file> # e.g. costs.csv
					     --scenario-type minimum-cost # minimum-cost, fiber, cellular, or satellite
```

The script above will use the school, fiber, and cellular data in the workspace specified, to create an output .csv table that contains cost information for each school in the input data set.
Additionally, you can specify the scenario type by choosing between a `minimum-cost` scenario or a single technology cost scenario (`fiber`, `cellular`, `satellite`).

## Preparing a Workspace

You can create a new workspace or update an existing workspace that houses the data needed to drive the models.
This data is composed of the following:
* Fiber nodes: fiber node locations in the region of interest
* Cell towers: cell tower locations, height, and technology availability in the region of interest
* Electricity: electricity availability at the schools of interest
* School data: school location, and connectivity information in the region of interest.

There are three steps involved in creating a workspace that can run the models end to end:
1. Aggregate the external non-connectivity data needed to run the models: fiber node locations, cell towers, electricity availability. You can find the reference datasets [here](https://drive.google.com/drive/folders/1XwXNGr4DPifuIOW1cAesE8_wJOvOlKC0?usp=share_link).
2. Populate the workspace with the up to date school information from project connect APIs
3. Generate any additional artifacts that can be used in a cache

To add the latest school set from the project connect APIs you can run the following:

```bash
./update_schools.py --workspace-directory <model-workspace> --country <country-of-interest> --api-token <project-connect-api-token>
```

You can generate a pairwise distance cache to help warm-start the fiber model for efficient compute using the CLI below:

```bash
./create_fiber_distance_cache.py --workspace <model-workspace>
```

You can generate a pairwise distance cache to help warm-start the cellular model using the CLI below:

```bash
./create_cellular_distance_cache.py --workspace <model-workspace>
```

After each run completes, the cache will be written to the model workspace.
If you load the model data space from that workspace, it will automatically use and load the distance cache for model calculations when it exists. 
