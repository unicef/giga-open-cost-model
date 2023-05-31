
# Giga Model Data

This document describes the input data Giga models use and how to modify this data.

Jump to:
* [Fetching country data](#fetching-country-data)
* [Adding a new country](#adding-a-new-country)
* [Preparing a data workspace](#preparing-a-data-workspace)
* [Data schemas](#data-schemas)

---

## Fetching country data

To generate a school dataset for a given country, we can use the API client in the library that can fetch school data from the project connect API - spec can be found [here](https://uni-connect-services-dev.azurewebsites.net/api/v1/#/School/get_api_v1_schools_country__country_id_).
The client can fetch school data by specified country, currently `Brazil` and `Rwanda` are supported.
The number of schools in a given country isn't available through the API and has be determined dynamically.
The default request parameters should fetch all the schools for the two countries above in a single request.

```python
client = GigaAPIClient(token) # auth token provisioned by Giga

country = 'Brazil'
schools = client.get_schools(country) # ~141,000 schools available for Brazil
```

To create a table of the schools after they've been fetched from the project connect API:
```python
from giga.schemas.school import GigaSchoolTable

table = GigaSchoolTable(schools=schools)

# to reduce the data to a table of just lat/lon coordinates
coordinate_table = table.to_coordinates()
```

---

## Adding a New Country

The library provides a number of helpers to add new countries that can be supported in the models.
There are a few steps that need to be completed in order to do this. 

1. Determine the default cost drivers for the country, and the code for the country that can be used with Project Connect APIs. Create a json file that has these parameters, see [here](conf/countries/rwanda.json) for an example of how to structure this file.
2. To drive the models, you need additional data for this country: electricity (optional), fiber node data, cellular tower data. You can find the format for these in the sub-sections below. Aggregate the data that you will need and place it in the workspace for this country.
3. You can add a new country by using the CLI as follows:  `./run add-new-country <your-country-parameters.json> <path-to-country-workspace> <PROJECT_CONNECT_API_TOKEN>`. This will register the country and make it available to the library models, fetch the most up to date school data for that country, merge that data with any existing workspace data like electricity data, and create a cache for schools and infrastructure data
4. Synchronize the new country data with remote storage, the current CLI is setup to work with an object store called Google Cloud Store, where all the workspace blobs/artifacts are persisted and updated using `./run upload-workspace <path-to-country-workspace>`
5. You are all set! After the updated version of the application has been re-deployed, the new country will be available to run models against 

Note that step 3 above combines multiple commands into a single executable for simplicity.
If you want to run each of these commands separately see the [Appendix](#appendix) for more information.

For more information on how you can use the `run` CLI, see the descriptions below (to generate the help text, execute `./run` from command line without any input arguments, see [here](run#L53) for the description):

```
  upload-workspace <workspace-dir> 				Copies the data workspace from the specified target directory to a storage bucket
  fetch-workspace <workspace-dir> 				Copies the data workspace from a storage bucket to the specified target directory
  register-country <parameter-file> 				Registers a new country in the modeling library
  fetch-school-data <workspace> <api-key> <country> 		Pulls up to date school data from Project Connect APIs
  create-cache <workspace> 					Creates a cache of pairwise distances that can be used by the models
  add-new-country <parameter-file> <workspace> <api-key> 	Registers country, pulls school data, creates cache
  remove-country <parameter-file> 				Removes a country from the modeling library
```

> **Note**: The individual steps for registering a new country can be found below.
These steps are combined in the command: `./run add-new-country <your-country-parameters.json> <path-to-country-workspace> <PROJECT_CONNECT_API_TOKEN>`.
> 
> 1. Register the country using the CLI: `./run register-country <your-country-parameters.json>`
> 2. Now the country is registered and will be available to the models. However, to drive the models, you need additional data for this country: electricity (optional), fiber node data, cellular tower data. You can find the format for these in the sub-sections below. Aggregate the data that you will need and place it in the workspace for this country.
> 3. Generate the most up to date school dataset for this country by using the CLI: `./run fetch-school-data <path-to-country-workspace> <PROJECT_CONNECT_API_TOKEN> <country-name>`
> 4. [OPTIONAL] If you would like, create a cache for the schools and infrastructure data that can be used to improve compute times in the models by using the CLI: `./run create-cache <path-to-country-workspace>`

### Supplemental Data

Supplemental data is currently not available through Project Connect APIs, and is thus managed independently.
If you have access to supplemental data of the schools in your country of interest, you can populate the workspace with a .csv table that contains entries of the following form:

| Field         | Type          | Description                   |
| ------------- | ------------- | ----------------------------- |
| giga_id_school | str           | Unique school identifier |
| has_electricity    | bool   | Whether the school has electricity   |
| fiber    | bool   | Whether the school has existing fiber connectivity   |
| coverage_type    | str   | The type of cellular coverage at the schools |
| num_students    | int   | The number of students at the school  |

If no supplemental data is provided all schools will be defaulted to the following:
* `has_electricity`: False
* `fiber`: False
* `coverage_type`: None
* `num_students`: None


### Fiber Node Data

Fiber nodes for a country can be specified as unique coordinates using the schema below in a csv table of the countries' workspace:


| Field         | Type          | Description                   |
| ------------- | ------------- | ----------------------------- |
| coordinate_id | str           | Unique coordinate identifier |
| coordinate    | LatLonPoint   | Latitude and longitude point  |
| properties    | json (optional) | Additional properties         |

---

### Cell Tower Data

Cell tower data for a country can be specified using the schema below in a csv table of the countries' workspace:

| Field        | Type                     | Description                      |
| ------------ | ------------------------ | -------------------------------- |
| tower_id     | str                      | Unique tower identifier          |
| operator     | str                      | Cellular tower operator          |
| outdoor      | bool                     | Whether the tower is outdoor     |
| lat          | float                    | Latitude of the tower            |
| lon          | float                    | Longitude of the tower           |
| height       | float                    | Height of the tower in meters    |
| technologies | List[CellTechnology]     | List of supported technologies [2G, 3G, 4G, LTE] |

---

## Preparing a Data Workspace

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

You can generate a line-of-sight cache to help warm-start the P2P model using the CLI below:

```bash
./create_p2p_distance_cache.py --workspace <model-workspace>
```

After each run completes, the cache will be written to the model workspace.
If you load the model data space from that workspace, it will automatically use and load the distance cache for model calculations when it exists.

## Data Schemas

The schemas below define key data types used in the modeling library.
The definitions are roughly broken down into three categories: model configuration, input data definitions, and output data definitions.

### Unique Coordinate

```json
{
    "title": "UniqueCoordinate",
    "description": "Uniquely identifiable lat/lon coordinate",
    "type": "object",
    "properties": {
        "coordinate_id": {
            "title": "Coordinate Id",
            "type": "string"
        },
        "coordinate": {
            "title": "Coordinate",
            "type": "array",
            "minItems": 2,
            "maxItems": 2,
            "items": [
                {
                    "type": "number"
                },
                {
                    "type": "number"
                }
            ]
        },
        "properties": {
            "title": "Properties",
            "type": "object"
        }
    },
    "required": [
        "coordinate_id",
        "coordinate"
    ]
}
```

### School Entity

```json
{
    "title": "GigaSchool",
    "description": "Definition of a single school",
    "type": "object",
    "properties": {
        "school_id": {
            "title": "School Id",
            "type": "string"
        },
        "name": {
            "title": "Name",
            "type": "string"
        },
        "country": {
            "title": "Country",
            "type": "string"
        },
        "country_id": {
            "title": "Country Id",
            "type": "integer"
        },
        "lat": {
            "title": "Lat",
            "type": "number"
        },
        "lon": {
            "title": "Lon",
            "type": "number"
        },
        "admin_1_name": {
            "title": "Admin 1 Name",
            "type": "string"
        },
        "admin_2_name": {
            "title": "Admin 2 Name",
            "type": "string"
        },
        "admin_3_name": {
            "title": "Admin 3 Name",
            "type": "string"
        },
        "admin_4_name": {
            "title": "Admin 4 Name",
            "type": "string"
        },
        "education_level": {
            "$ref": "#/definitions/EducationLevel"
        },
        "giga_id_school": {
            "title": "Giga Id School",
            "type": "string"
        },
        "environment": {
            "$ref": "#/definitions/SchoolZone"
        },
        "connected": {
            "title": "Connected",
            "default": false,
            "type": "boolean"
        },
        "has_electricity": {
            "title": "Has Electricity",
            "default": true,
            "type": "boolean"
        },
        "bandwidth_demand": {
            "title": "Bandwidth Demand",
            "default": 20.0,
            "type": "number"
        }
    },
    "required": [
        "school_id",
        "name",
        "country",
        "country_id",
        "lat",
        "lon",
        "admin_1_name",
        "admin_2_name",
        "admin_3_name",
        "admin_4_name",
        "education_level",
        "giga_id_school",
        "environment"
    ],
    "definitions": {
        "EducationLevel": {
            "title": "EducationLevel",
            "description": "Valid level of education",
            "enum": [
                "Primary",
                "Secondary",
                "Other",
                ""
            ],
            "type": "string"
        },
        "SchoolZone": {
            "title": "SchoolZone",
            "description": "Valid school zone environment",
            "enum": [
                "rural",
                "urban",
                ""
            ],
            "type": "string"
        }
    }
}
```

### Cell Tower

```json
{
  "info": {
    "title": "Cellular Tower API"
  },
  "components": {
    "schemas": {
      "CellularTower": {
        "title": "CellularTower",
        "type": "object",
        "properties": {
          "tower_id": {
            "title": "Tower Id",
            "type": "string"
          },
          "operator": {
            "title": "Operator",
            "type": "string"
          },
          "outdoor": {
            "title": "Outdoor",
            "type": "boolean"
          },
          "lat": {
            "title": "Latitude",
            "type": "number",
            "format": "float"
          },
          "lon": {
            "title": "Longitude",
            "type": "number",
            "format": "float"
          },
          "height": {
            "title": "Height",
            "type": "number",
            "format": "float"
          },
          "technologies": {
            "title": "Technologies",
            "type": "array",
            "items": {
              "type": "string",
              "enum": [
                "2G",
                "3G",
                "4G",
                "LTE"
              ]
            },
            "uniqueItems": true
          }
        },
        "required": [
          "tower_id",
          "operator",
          "outdoor",
          "lat",
          "lon",
          "height",
          "technologies"
        ]
      }
    }
  }
}

```


### Fiber Model Configuration

```json
{
    "title": "FiberTechnologyCostConf",
    "type": "object",
    "properties": {
        "capex": {
            "$ref": "#/definitions/FiberCapex"
        },
        "opex": {
            "$ref": "#/definitions/FiberOpex"
        },
        "constraints": {
            "$ref": "#/definitions/FiberConstraints"
        },
        "technology": {
            "title": "Technology",
            "default": "Fiber",
            "type": "string"
        },
        "electricity_config": {
            "$ref": "#/definitions/ElectricityCostConf"
        }
    },
    "required": [
        "capex",
        "opex",
        "constraints"
    ],
    "definitions": {
        "FiberCapex": {
            "title": "FiberCapex",
            "type": "object",
            "properties": {
                "cost_per_km": {
                    "title": "Cost Per Km",
                    "type": "number"
                },
                "fixed_costs": {
                    "title": "Fixed Costs",
                    "default": 0.0,
                    "type": "number"
                },
                "economies_of_scale": {
                    "title": "Economies Of Scale",
                    "default": true,
                    "type": "boolean"
                }
            },
            "required": [
                "cost_per_km"
            ]
        },
        "FiberOpex": {
            "title": "FiberOpex",
            "type": "object",
            "properties": {
                "cost_per_km": {
                    "title": "Cost Per Km",
                    "type": "number"
                },
                "annual_bandwidth_cost_per_mbps": {
                    "title": "Annual Bandwidth Cost Per Mbps",
                    "default": 0.0,
                    "type": "number"
                }
            },
            "required": [
                "cost_per_km"
            ]
        },
        "FiberConstraints": {
            "title": "FiberConstraints",
            "type": "object",
            "properties": {
                "maximum_connection_length": {
                    "title": "Maximum Connection Length",
                    "default": Infinity,
                    "type": "number"
                },
                "maximum_bandwithd": {
                    "title": "Maximum Bandwithd",
                    "default": 2000,
                    "type": "number"
                },
                "required_power": {
                    "title": "Required Power",
                    "default": 500,
                    "type": "number"
                }
            }
        },
        "ElectricityCapexConf": {
            "title": "ElectricityCapexConf",
            "type": "object",
            "properties": {
                "solar_panel_costs": {
                    "title": "Solar Panel Costs",
                    "type": "number"
                },
                "battery_costs": {
                    "title": "Battery Costs",
                    "type": "number"
                }
            },
            "required": [
                "solar_panel_costs",
                "battery_costs"
            ]
        },
        "ElectricityOpexConf": {
            "title": "ElectricityOpexConf",
            "type": "object",
            "properties": {
                "cost_per_kwh": {
                    "title": "Cost Per Kwh",
                    "type": "number"
                }
            },
            "required": [
                "cost_per_kwh"
            ]
        },
        "ElectricityCostConf": {
            "title": "ElectricityCostConf",
            "type": "object",
            "properties": {
                "capex": {
                    "$ref": "#/definitions/ElectricityCapexConf"
                },
                "opex": {
                    "$ref": "#/definitions/ElectricityOpexConf"
                }
            },
            "required": [
                "capex",
                "opex"
            ]
        }
    }
}
```

### School Connection Cost

```json
{
    "title": "SchoolConnectionCosts",
    "type": "object",
    "properties": {
        "school_id": {
            "title": "School Id",
            "type": "string"
        },
        "capex": {
            "title": "Capex",
            "type": "number"
        },
        "opex": {
            "title": "Opex",
            "type": "number"
        },
        "opex_provider": {
            "title": "Opex Provider",
            "type": "number"
        },
        "opex_consumer": {
            "title": "Opex Consumer",
            "type": "number"
        },
        "technology": {
            "$ref": "#/definitions/ConnectivityTechnology"
        },
        "feasible": {
            "title": "Feasible",
            "default": true,
            "type": "boolean"
        },
        "reason": {
            "title": "Reason",
            "type": "string"
        },
        "electricity": {
            "$ref": "#/definitions/PowerConnectionCosts"
        }
    },
    "required": [
        "school_id",
        "capex",
        "opex",
        "opex_provider",
        "opex_consumer",
        "technology"
    ],
    "definitions": {
        "ConnectivityTechnology": {
            "title": "ConnectivityTechnology",
            "description": "Technologies that can be assessed in modeling scenarios",
            "enum": [
                "Fiber",
                "Cellular",
                "Satellite",
                "None"
            ],
            "type": "string"
        },
        "PowerConnectionCosts": {
            "title": "PowerConnectionCosts",
            "type": "object",
            "properties": {
                "electricity_opex": {
                    "title": "Electricity Opex",
                    "default": 0.0,
                    "type": "number"
                },
                "electricity_capex": {
                    "title": "Electricity Capex",
                    "default": 0.0,
                    "type": "number"
                },
                "cost_type": {
                    "title": "Cost Type",
                    "default": "Grid",
                    "enum": [
                        "Grid",
                        "Solar"
                    ],
                    "type": "string"
                }
            }
        }
    }
}
```
