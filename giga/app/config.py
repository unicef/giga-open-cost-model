import os
import fnmatch
import json
from typing import List
import pandas as pd
import copy

#from giga.utils.globals import COUNTRY_DEFAULT_WORKSPACE
#from giga.data.store.stores import COUNTRY_DATA_STORE as data_store
#from giga.utils.globals import SCHOOLS_DEFAULT_PATH
from giga.utils.globals import *
from giga.data.store.stores import COUNTRY_DATA_STORE as data_store
from giga.data.store.stores import SCHOOLS_DATA_STORE as schools_data_store

# Get the countries to skip from an variable
skip_in_deployment_str = os.getenv("SKIP_COUNTRIES_IN_DEPLOYMENT", "sample")
# Parse the string into a list
SKIP_IN_DEPLOYMENT = skip_in_deployment_str.split(",") if skip_in_deployment_str else []

#maybe move to a different file?
empty_default_dict = {
    "data": {
        "country": "",
        "country_code": 0,
        "workspace": "workspace",
        "school_file": "schools.csv",
        "fiber_file": "",
        "cellular_file": "",
        "fiber_distance_cache_file":"",
        "cellular_distance_cache_file": "",
        "p2p_distance_cache_file": "",
        "country_center": {
            "lat": 0,
            "lon": 0
        }
    },
    "model_defaults": {
        "scenario": {
            "years_opex": YEARS_OPEX,
            "bandwidth_demand": BANDWIDTH_DEMAND
        },
        "fiber": {
            "capex": {
                "cost_per_km": 0.0,
                "fixed_costs": 0.0,
                "economies_of_scale": ECONOMIES_OF_SCALE
            },
            "opex": {
                "cost_per_km": 0.0,
                "annual_bandwidth_cost_per_mbps": 0.0
            },
            "constraints": {
                "maximum_connection_length": 0.0,
                "maximum_bandwithd": 2000.0,
                "required_power": 0.0
            },
            "technology": "Fiber"
        },
        "satellite": {
            "capex": {
                "fixed_costs": 0.0
            },
            "opex": {
                "fixed_costs": 0.0,
                "annual_bandwidth_cost_per_mbps": 0.0
            },
            "constraints": {
                "maximum_bandwithd": 150.0,
                "required_power": 0.0
            },
            "technology": "Satellite"
        },
        "cellular": {
            "capex": {
                "fixed_costs": 0.0
            },
            "opex": {
                "fixed_costs": 0.0,
                "annual_bandwidth_cost_per_mbps": 0.0
            },
            "constraints": {
                "maximum_range": 0.0,
                "maximum_bandwithd": 100.0,
                "required_power": 0.0
            },
            "technology": "Cellular"
        },
        "p2p": {
            "capex": {
                "fixed_costs": 0.0,
                "tower_fixed_costs": 0.0
            },
            "opex": {
                "fixed_costs": 0.0,
                "annual_bandwidth_cost_per_mbps": 0.0
            },
            "constraints": {
                "maximum_range": 0.0,
                "maximum_bandwithd": 1000.0,
                "required_power": 0.0
            },
            "technology": "P2P"
        },
        "electricity": {
            "capex": {
                "solar_cost_per_watt": 0.0
            },
            "opex": {
                "cost_per_kwh": 0.0
            },
            "constraints": {
                "required_power_per_school":0.0
            }
        }
    }
}


def get_country_code_dicts(directory=COUNTRY_CODE_DEFAULT_PATH,filename=COUNTRY_CODE_DEFAULT_NAME):
    with schools_data_store.open(os.path.join(directory, filename)) as f:
        df = pd.read_csv(f)
    return df.set_index('Code')['Country'].to_dict(),df.set_index('Country')['Code'].to_dict()

CODE_COUNTRY_DICT, COUNTRY_CODE_DICT = get_country_code_dicts()

def get_registered_countries_old(directory=COUNTRY_DEFAULT_WORKSPACE) -> None:
    countries = []
    for root, _, filenames in data_store.walk(directory):
        for filename in fnmatch.filter(filenames, "*.json"):
            countries.append(filename.split(".")[0])
    return countries

def get_registered_countries(directory=SCHOOLS_DEFAULT_PATH) -> None:
    countries = []
    for root, _, filenames in schools_data_store.walk(directory):
        for filename in fnmatch.filter(filenames, "*.csv"):
            countries.append(filename.split("_")[0])
    return countries


def get_registered_country_names_old(
    default_parameter_dir=COUNTRY_DEFAULT_WORKSPACE, skip=SKIP_IN_DEPLOYMENT
):
    countries = get_registered_countries(default_parameter_dir)
    return [c.replace("_", " ").title() for c in countries if c not in skip]

def get_registered_country_names(directory=SCHOOLS_DEFAULT_PATH) -> None:
    countries = []
    for root, _, filenames in schools_data_store.walk(directory):
        for filename in fnmatch.filter(filenames, "*.csv"):
            countries.append(CODE_COUNTRY_DICT[filename.split("_")[0]])
    return countries


def get_country_defaults_old(
    workspace="workspace", default_parameter_dir=COUNTRY_DEFAULT_WORKSPACE
):
    countries = get_registered_countries(default_parameter_dir)
    defaults = {}
    for country in countries:
        with data_store.open(os.path.join(default_parameter_dir, f"{country}.json")) as f:
            default = json.load(f)
        default["data"]["workspace"] = workspace
        defaults[country] = default
    return defaults

def get_country_defaults(workspace="workspace", schools_dir=SCHOOLS_DEFAULT_PATH, costs_dir= COSTS_DEFAULT_PATH):
    defaults = {}
    for root, _, filenames in schools_data_store.walk(schools_dir):
        for filename in fnmatch.filter(filenames, "*.csv"):
            default = copy.deepcopy(empty_default_dict)
            country = filename.split("_")[0]
            default['data']['country'] = country
            default['data']['workspace'] = workspace
            #school master file
            master_file = os.path.join(schools_dir, country + MASTER_DEFAULT_NAME)
            with schools_data_store.open(master_file) as f:
                df = pd.read_csv(f)
            df.dropna(subset=['giga_id_school'], inplace=True)
            #if not data_store.dir_exists(os.path.join(workspace,country)):
            #    data_store.mkdir(os.path.join(workspace,country))
            country_dir = os.path.join(workspace,country)
            status = 'OK'
            if not data_store.file_exists(os.path.join(country_dir,SCHOOLS_FILE)):
                data_store.write_file(os.path.join(country_dir,SCHOOLS_FILE),df.to_csv(index=False))
            else:
                with data_store.open(os.path.join(country_dir,SCHOOLS_FILE)) as f:
                    df2 = pd.read_csv(f)
                if not df.equals(df2):
                    #if the schools are the same then the caches are ok otherwise ko
                    if not df[['giga_id_school','lat','lon']].equals(df2[['giga_id_school','lat','lon']]):
                        status = 'KO'
                    data_store.write_file(os.path.join(country_dir,SCHOOLS_FILE_OLD),df2.to_csv(index=False))
                    data_store.write_file(os.path.join(country_dir,SCHOOLS_FILE),df.to_csv(index=False))


            #center coordinates
            lats = list(df['lat'])
            lons = list(df['lon'])
            c_lat = sum(lats)/len(lats)
            c_lon = sum(lons)/len(lons)
            default["data"]["country_center"]["lat"] = c_lat
            default["data"]["country_center"]["lon"] = c_lon

            # add extra files if they exist
            if status=='OK':
                if data_store.file_exists(os.path.join(country_dir,CELL_FILE)):
                    default["data"]["cellular_file"] = CELL_FILE
                if data_store.file_exists(os.path.join(country_dir,CELL_CACHE_FILE)):
                    default["data"]["cellular_distance_cache_file"] = CELL_CACHE_FILE
                if data_store.file_exists(os.path.join(country_dir,FIBER_FILE)):
                    default["data"]["fiber_file"] = FIBER_FILE
                if data_store.file_exists(os.path.join(country_dir,FIBER_CACHE_FILE)):
                    default["data"]["fiber_distance_cache_file"] = FIBER_CACHE_FILE
                if data_store.file_exists(os.path.join(country_dir,P2P_CACHE_FILE)):
                    default["data"]["p2p_distance_cache_file"] = P2P_CACHE_FILE    
            # add costs
            ### cell
            if schools_data_store.file_exists(os.path.join(costs_dir, CELL_CAPEX_FILE)): 
                with schools_data_store.open(os.path.join(costs_dir, CELL_CAPEX_FILE)) as f:
                    dfc = pd.read_csv(f)
                if country in dfc['Country'].values:
                    desired_row = dfc[dfc['Country'] == country].iloc[0]
                    default["model_defaults"]['cellular']["capex"]["fixed_costs"] = desired_row["Setup cost"]

            if schools_data_store.file_exists(os.path.join(costs_dir, CELL_OPEX_FILE)): 
                with schools_data_store.open(os.path.join(costs_dir, CELL_OPEX_FILE)) as f:
                    dfc = pd.read_csv(f)
                if country in dfc['Country'].values:
                    desired_row = dfc[dfc['Country'] == country].iloc[0]
                    default["model_defaults"]['cellular']["opex"]["fixed_costs"] = desired_row["Maintenance yearly"]
                    default["model_defaults"]['cellular']["opex"]["annual_bandwidth_cost_per_mbps"] = desired_row["Cost per Mbps/year"]

            if schools_data_store.file_exists(os.path.join(costs_dir, CELL_CSTRS_FILE)): 
                with schools_data_store.open(os.path.join(costs_dir, CELL_CSTRS_FILE)) as f:
                    dfc = pd.read_csv(f)
                if country in dfc['Country'].values:
                    desired_row = dfc[dfc['Country'] == country].iloc[0]
                    default["model_defaults"]['cellular']["constraints"]["maximum_range"] = desired_row["Max length"]
                    default["model_defaults"]['cellular']["constraints"]["required_power"] = desired_row["Annual power required (KWh)"]

            ### p2p
            if schools_data_store.file_exists(os.path.join(costs_dir, P2P_CAPEX_FILE)): 
                with schools_data_store.open(os.path.join(costs_dir, P2P_CAPEX_FILE)) as f:
                    dfc = pd.read_csv(f)
                if country in dfc['Country'].values:
                    desired_row = dfc[dfc['Country'] == country].iloc[0]
                    default["model_defaults"]['p2p']["capex"]["fixed_costs"] = desired_row["Setup cost - school"]
                    default["model_defaults"]['p2p']["capex"]["tower_fixed_costs"] = desired_row["Setup cost - tower"]

            if schools_data_store.file_exists(os.path.join(costs_dir, P2P_OPEX_FILE)): 
                with schools_data_store.open(os.path.join(costs_dir, P2P_OPEX_FILE)) as f:
                    dfc = pd.read_csv(f)
                if country in dfc['Country'].values:
                    desired_row = dfc[dfc['Country'] == country].iloc[0]
                    default["model_defaults"]['p2p']["opex"]["fixed_costs"] = desired_row["Maintenance yearly"]
                    default["model_defaults"]['p2p']["opex"]["annual_bandwidth_cost_per_mbps"] = desired_row["Cost per Mbps/year"]

            if schools_data_store.file_exists(os.path.join(costs_dir, P2P_CSTRS_FILE)): 
                with schools_data_store.open(os.path.join(costs_dir, P2P_CSTRS_FILE)) as f:
                    dfc = pd.read_csv(f)
                if country in dfc['Country'].values:
                    desired_row = dfc[dfc['Country'] == country].iloc[0]
                    default["model_defaults"]['p2p']["constraints"]["maximum_range"] = desired_row["Max length"]
                    default["model_defaults"]['p2p']["constraints"]["required_power"] = desired_row["Annual power required (KWh)"]

            ### fiber
            if schools_data_store.file_exists(os.path.join(costs_dir, FIBER_CAPEX_FILE)): 
                with schools_data_store.open(os.path.join(costs_dir, FIBER_CAPEX_FILE)) as f:
                    dfc = pd.read_csv(f)
                if country in dfc['Country'].values:
                    desired_row = dfc[dfc['Country'] == country].iloc[0]
                    default["model_defaults"]['fiber']["capex"]["fixed_costs"] = desired_row["Setup cost"]
                    default["model_defaults"]['fiber']["capex"]["cost_per_km"] = desired_row["Cost per km"]

            if schools_data_store.file_exists(os.path.join(costs_dir, FIBER_OPEX_FILE)): 
                with schools_data_store.open(os.path.join(costs_dir, FIBER_OPEX_FILE)) as f:
                    dfc = pd.read_csv(f)
                if country in dfc['Country'].values:
                    desired_row = dfc[dfc['Country'] == country].iloc[0]
                    #defaults['fiber']["opex"]["fixed_costs"] = desired_row["Maintenance yearly"] --> Not in original code - we should add it
                    default["model_defaults"]['fiber']["opex"]["annual_bandwidth_cost_per_mbps"] = desired_row["Cost per Mbps/year"]
                    default["model_defaults"]['fiber']["opex"]["cost_per_km"] = desired_row["Maintenance per km"]

            if schools_data_store.file_exists(os.path.join(costs_dir, FIBER_CSTRS_FILE)): 
                with schools_data_store.open(os.path.join(costs_dir, FIBER_CSTRS_FILE)) as f:
                    dfc = pd.read_csv(f)
                if country in dfc['Country'].values:
                    desired_row = dfc[dfc['Country'] == country].iloc[0]
                    default["model_defaults"]['fiber']["constraints"]["maximum_connection_length"] = desired_row["Max length"]
                    default["model_defaults"]['fiber']["constraints"]["required_power"] = desired_row["Annual power required (KWh)"]

            ### satellite
            if schools_data_store.file_exists(os.path.join(costs_dir, SAT_CAPEX_FILE)): 
                with schools_data_store.open(os.path.join(costs_dir, SAT_CAPEX_FILE)) as f:
                    dfc = pd.read_csv(f)
                if country in dfc['Country'].values:
                    desired_row = dfc[dfc['Country'] == country].iloc[0]
                    default["model_defaults"]['satellite']["capex"]["fixed_costs"] = desired_row["Setup cost"]

            if schools_data_store.file_exists(os.path.join(costs_dir, SAT_OPEX_FILE)): 
                with schools_data_store.open(os.path.join(costs_dir, SAT_OPEX_FILE)) as f:
                    dfc = pd.read_csv(f)
                if country in dfc['Country'].values:
                    desired_row = dfc[dfc['Country'] == country].iloc[0]
                    default["model_defaults"]['satellite']["opex"]["fixed_costs"] = desired_row["Maintenance yearly"]
                    default["model_defaults"]['satellite']["opex"]["annual_bandwidth_cost_per_mbps"] = desired_row["Cost per Mbps/year"]

            if schools_data_store.file_exists(os.path.join(costs_dir, SAT_CSTRS_FILE)): 
                with schools_data_store.open(os.path.join(costs_dir, SAT_CSTRS_FILE)) as f:
                    dfc = pd.read_csv(f)
                if country in dfc['Country'].values:
                    desired_row = dfc[dfc['Country'] == country].iloc[0]
                    default["model_defaults"]['satellite']["constraints"]["required_power"] = desired_row["Annual power required (KWh)"]
                
            ### electricity
            if schools_data_store.file_exists(os.path.join(costs_dir, ELECTRICITY_CAPEX_FILE)): 
                with schools_data_store.open(os.path.join(costs_dir, ELECTRICITY_CAPEX_FILE)) as f:
                    dfc = pd.read_csv(f)
                if country in dfc['Country'].values:
                    desired_row = dfc[dfc['Country'] == country].iloc[0]
                    default["model_defaults"]['electricity']["capex"]["solar_cost_per_watt"] = desired_row["Solar cost (USD/Watt)"]

            if schools_data_store.file_exists(os.path.join(costs_dir, ELECTRICITY_OPEX_FILE)): 
                with schools_data_store.open(os.path.join(costs_dir, ELECTRICITY_OPEX_FILE)) as f:
                    dfc = pd.read_csv(f)
                if country in dfc['Country'].values:
                    desired_row = dfc[dfc['Country'] == country].iloc[0]
                    default["model_defaults"]['electricity']["opex"]["cost_per_kwh"] = desired_row["Cost per kWh"]

            if schools_data_store.file_exists(os.path.join(costs_dir, ELECTRICITY_CSTRS_FILE)): 
                with schools_data_store.open(os.path.join(costs_dir, ELECTRICITY_CSTRS_FILE)) as f:
                    dfc = pd.read_csv(f)
                if country in dfc['Country'].values:
                    desired_row = dfc[dfc['Country'] == country].iloc[0]
                    default["model_defaults"]['electricity']["constraints"]["required_power_per_school"] = desired_row["Power required per school (Watts)"]

            defaults[country] = default

    return defaults


def get_country_code_lookup(default_parameter_dir=COUNTRY_DEFAULT_WORKSPACE):
    defaults = get_country_defaults(default_parameter_dir=default_parameter_dir)
    return {
        c: default["data"]["country_code"]
        for c, default in defaults.items()
        if default["data"]["country_code"]
    }

