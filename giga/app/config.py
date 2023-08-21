import os
import fnmatch
import json
from typing import List
import pandas as pd
import copy
import numpy as np

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
empty_single_cache = {"lookup": {}, "cache_type": "one-to-one"}
empty_multiple_cache = {"lookup": {},"n_neighbors":0,"cache_type":"one-to-many"}

empty_default_dict = {
    "data": {
        "country": "",
        "country_code": 0,
        "workspace": "workspace",
        "school_file": SCHOOLS_FILE,
        "fiber_file":FIBER_FILE,
        "cellular_file": CELL_FILE,
        "fiber_distance_cache_file":FIBER_CACHE_FILE,
        "cellular_distance_cache_file": CELL_CACHE_FILE,
        "p2p_distance_cache_file": P2P_CACHE_FILE,
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
        },
        "available_tech": {
            "fiber": True,
            "cellular": True,
            "p2p": True,
            "satellite": True,
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

def check_avail_techs(country_dir,df_schools):
    fiber = True
    cell = True
    p2p = True

    f = data_store.read_file(os.path.join(country_dir,FIBER_FILE))
    if len(f)==0:
        fiber = False
    else:

        with data_store.open(os.path.join(country_dir,FIBER_CACHE_FILE)) as f:
            jsf = json.load(f)

        with data_store.open(os.path.join(country_dir,SCHOOLS_CACHE_FILE)) as f:
            jss = json.load(f)

        if len(jsf["lookup"])==0 or len(jss["lookup"])==0:
            fiber = False

    f = data_store.read_file(os.path.join(country_dir,CELL_FILE))
    if len(f)==0:
        cell = df_schools["coverage_type"].notnull().any()
        p2p = False
    else:
        with data_store.open(os.path.join(country_dir,CELL_CACHE_FILE)) as f:
            jsc = json.load(f)
        if len(jsc["lookup"])==0:
            cell = False

        with data_store.open(os.path.join(country_dir,P2P_CACHE_FILE)) as f:
            jsp = json.load(f)
        if len(jsp["lookup"])==0:
            p2p = False

    return fiber,cell,p2p

    
def create_empty_tech_files(country_dir):
    data_store.write_file(os.path.join(country_dir,CELL_FILE),"")
    data_store.write_file(os.path.join(country_dir,FIBER_FILE),"")

def create_empty_caches(country_dir):
     with data_store.open(os.path.join(country_dir,SCHOOLS_CACHE_FILE), "w") as f:
        json.dump(empty_multiple_cache, f)

     with data_store.open(os.path.join(country_dir,FIBER_CACHE_FILE), "w") as f:
        json.dump(empty_single_cache, f)

     with data_store.open(os.path.join(country_dir,CELL_CACHE_FILE), "w") as f:
        json.dump(empty_single_cache, f)

     with data_store.open(os.path.join(country_dir,P2P_CACHE_FILE), "w") as f:
        json.dump(empty_single_cache, f)


def copy_caches_to_backup(country_dir):
    #schools cache
    with data_store.open(os.path.join(country_dir,SCHOOLS_CACHE_FILE)) as f:
        js = json.load(f)

    with data_store.open(os.path.join(country_dir,BACKUP_DIR,SCHOOLS_CACHE_FILE), "w") as f:
        json.dump(js, f)

    #fiber cache
    with data_store.open(os.path.join(country_dir,FIBER_CACHE_FILE)) as f:
        js = json.load(f)

    with data_store.open(os.path.join(country_dir,BACKUP_DIR,FIBER_CACHE_FILE), "w") as f:
        json.dump(js, f)

    #cell cache
    with data_store.open(os.path.join(country_dir,CELL_CACHE_FILE)) as f:
        js = json.load(f)

    with data_store.open(os.path.join(country_dir,BACKUP_DIR,CELL_CACHE_FILE), "w") as f:
        json.dump(js, f)

    #p2p cache
    with data_store.open(os.path.join(country_dir,P2P_CACHE_FILE)) as f:
        js = json.load(f)

    with data_store.open(os.path.join(country_dir,BACKUP_DIR,P2P_CACHE_FILE), "w") as f:
        json.dump(js, f)

# This could be a call to GigaSchoolTable at some point...    
def fix_schools(df):
    df_new = df.copy()
    df_new.dropna(subset=['giga_id_school'], inplace=True) #AIA has some nan giga_ids...

    ####num_students####
    your_column = 'num_students'

    # Step 1: Replace empty values with NaN
    #df_new[your_column].replace('', pd.NA, inplace=True)
    df_new[your_column].replace(r'^\s*$', pd.NA, regex=True, inplace=True)
    df_new[your_column] = pd.to_numeric(df_new[your_column], errors='coerce')   

    if df[your_column].notna().any():
        # Step 2: Calculate the average of the non-empty values
        average = int(df_new[your_column].dropna().mean())

        # Step 3: Replace NaN values with average (if not all values are empty) or with DEFAULT_VALUE
        df_new[your_column].fillna(average, inplace=True)
    else:
        df_new[your_column].fillna(DEFAULT_NUM_STUDENTS, inplace=True)

    # Step 4: Convert the column to integers
    df_new[your_column] = df_new[your_column].astype(int)
    #####################

    return df_new

def get_country_default(country,workspace, schools_dir, costs_dir):
    default = copy.deepcopy(empty_default_dict)
    
    default['data']['country'] = country
    default['data']['workspace'] = workspace
    #school master file
    master_file = os.path.join(schools_dir, country + MASTER_DEFAULT_NAME)
    with schools_data_store.open(master_file) as f:
        df = pd.read_csv(f, dtype={"lat": "float32", "lon": "float32"})

    df_fixed = fix_schools(df)
    

    country_dir = os.path.join(workspace,country)
    #if schools file does not exist copy it and create empty files
    if not data_store.file_exists(os.path.join(country_dir,SCHOOLS_FILE)):
        data_store.write_file(os.path.join(country_dir,SCHOOLS_FILE),df_fixed.to_csv(index=False))
        create_empty_tech_files(country_dir)
        create_empty_caches(country_dir)
        #in this case, only sat is available and maybe cell
        default["model_defaults"]["available_tech"]["fiber"] = False
        default["model_defaults"]["available_tech"]["cellular"] = df_fixed["coverage_type"].notnull().any()
        default["model_defaults"]["available_tech"]["p2p"] = False
    else:
        with data_store.open(os.path.join(country_dir,SCHOOLS_FILE)) as f:
            df2 = pd.read_csv(f, dtype={"lat": "float32", "lon": "float32"})
        if not df_fixed.equals(df2):
            #if the schools are the same then the caches are ok otherwise ko
            if not df_fixed[['giga_id_school','lat','lon']].equals(df2[['giga_id_school','lat','lon']]):
                # we save the old schools file in backup, might be useful to recalculate caches
                data_store.write_file(os.path.join(country_dir,BACKUP_DIR,SCHOOLS_FILE),df2.to_csv(index=False))
                copy_caches_to_backup(country_dir)
                create_empty_caches(country_dir)
            
            #in any case we save the new schools file
            data_store.write_file(os.path.join(country_dir,SCHOOLS_FILE),df_fixed.to_csv(index=False))

        #check tech availability
        fiber,cell,p2p = check_avail_techs(country_dir,df_fixed)
        default["model_defaults"]["available_tech"]["fiber"] = fiber
        default["model_defaults"]["available_tech"]["cellular"] = cell
        default["model_defaults"]["available_tech"]["p2p"] = p2p

    #get center coordinates
    df_filtered = df_fixed.dropna(subset=['lat', 'lon']) #there might be nans in some lat,lon
    lats = list(df_filtered['lat'])
    lons = list(df_filtered['lon'])
    c_lat = sum(lats)/len(lats)
    c_lon = sum(lons)/len(lons)
    default["data"]["country_center"]["lat"] = c_lat
    default["data"]["country_center"]["lon"] = c_lon

    #add costs
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

    return default


def get_country_defaults(workspace="workspace", schools_dir=SCHOOLS_DEFAULT_PATH, costs_dir= COSTS_DEFAULT_PATH):
    defaults = {}
    for root, _, filenames in schools_data_store.walk(schools_dir):
        for filename in fnmatch.filter(filenames, "*.csv"):
            country = filename.split("_")[0]
            default = get_country_default(country,workspace,schools_dir,costs_dir)
            defaults[country] = default

    return defaults


def get_country_code_lookup(default_parameter_dir=COUNTRY_DEFAULT_WORKSPACE):
    defaults = get_country_defaults(default_parameter_dir=default_parameter_dir)
    return {
        c: default["data"]["country_code"]
        for c, default in defaults.items()
        if default["data"]["country_code"]
    }

