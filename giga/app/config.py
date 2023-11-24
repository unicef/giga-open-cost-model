import os
import fnmatch
import json
import pandas as pd
import copy
import numpy as np
import math

from giga.utils.globals import *
from giga.data.store.stores import COUNTRY_DATA_STORE as data_store
from giga.data.store.stores import SCHOOLS_DATA_STORE as schools_data_store

import country_converter as coco
from datetime import datetime

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
        "school_cache_file": SCHOOLS_CACHE_FILE,
        "school_visibility_cache_file": SCHOOLS_VISIBILITY_CACHE_FILE,
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
                "economies_of_scale": ECONOMIES_OF_SCALE,
                "schools_as_fiber_nodes": True,
            },
            "opex": {
                "cost_per_km": 0.0,
                "annual_bandwidth_cost_per_mbps": 0.0
            },
            "constraints": {
                "maximum_connection_length": 0.0,
                "maximum_bandwithd": 2000.0,
                "required_power": 0.0,
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
            "schools_as_nodes": True,
        }
    }
}


def get_country_code_dicts(directory=COUNTRY_CODE_DEFAULT_PATH,filename=COUNTRY_CODE_DEFAULT_NAME):
    with schools_data_store.open(os.path.join(directory, filename)) as f:
        df = pd.read_csv(f)
    return df.set_index('Code')['Country'].to_dict(),df.set_index('Country')['Code'].to_dict()


def get_registered_countries(directory=SCHOOLS_DEFAULT_PATH) -> None:
    countries = []
    for root, _, filenames in schools_data_store.walk(directory):
        for filename in fnmatch.filter(filenames, "*.csv"):
            countries.append(filename.split("_")[0])
    return countries

def get_registered_country_names(directory=SCHOOLS_DEFAULT_PATH) -> None:
    countries = []
    for root, _, filenames in schools_data_store.walk(directory):
        for filename in fnmatch.filter(filenames, "*.csv"):
            countries.append(coco.convert(filename.split("_")[0], to='name_short'))
    return countries

def is_fiber(s, fiber_keywords = ['fiber', 'fibre', 'fibra', 'ftt', 'fttx']):
    return any(keyword in s.lower() for keyword in fiber_keywords if isinstance(s,str))

def check_avail_techs(country_dir, df_schools):

    # check fiber availability
    fiber = False
    if data_store.file_size(os.path.join(country_dir,SCHOOLS_CACHE_FILE)) >= 3:

        f = data_store.read_file(os.path.join(country_dir,FIBER_FILE))
        
        if len(f) > 0:
            with data_store.open(os.path.join(country_dir,FIBER_CACHE_FILE)) as f:
                jsf = json.load(f)
            if len(jsf["lookup"])>0:
                fiber = True
        else:
            fiber = (df_schools["fiber_node_distance"]!=math.inf).any() if 'fiber_node_distance' in df_schools else False
    
    # check cell & p2p availability
    cell = False
    p2p = False

    f_cell = data_store.read_file(os.path.join(country_dir,CELL_FILE))

    if len(f_cell)>0:
        with data_store.open(os.path.join(country_dir,CELL_CACHE_FILE)) as f:
            jsc = json.load(f)
        if len(jsc["lookup"])>0:
            cell = True
        
        with data_store.open(os.path.join(country_dir,P2P_CACHE_FILE)) as f:
            jsp = json.load(f)
        if len(jsp["lookup"])>0:
            if data_store.file_size(os.path.join(country_dir,SCHOOLS_VISIBILITY_CACHE_FILE)) >= 3:
                p2p = True
    else:
        cell = df_schools["coverage_type"].notnull().any() if 'coverage_type' in df_schools else False

    # check schools as nodes availability
    if not fiber:
        san= False
    else:
        san = df_schools["type_connectivity"].apply(is_fiber).any() if 'type_connectivity' in df_schools else False

    return fiber,cell,p2p,san

    
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

    with data_store.open(os.path.join(country_dir,SCHOOLS_VISIBILITY_CACHE_FILE), 'w') as f:
        json.dump(empty_multiple_cache, f)


def copy_caches_to_backup(country_dir):
    time_stamp = datetime.now().strftime("%Y_%m_%d")
    #schools cache
    with data_store.open(os.path.join(country_dir,SCHOOLS_CACHE_FILE)) as f:
        js = json.load(f)

    with data_store.open(os.path.join(country_dir,BACKUP_DIR,SCHOOLS_CACHE_FILE[:-5]+"_"+time_stamp+".json"), "w") as f:
        json.dump(js, f)

    #fiber cache
    with data_store.open(os.path.join(country_dir,FIBER_CACHE_FILE)) as f:
        js = json.load(f)

    with data_store.open(os.path.join(country_dir,BACKUP_DIR,FIBER_CACHE_FILE[:-5]+"_"+time_stamp+".json"), "w") as f:
        json.dump(js, f)

    #cell cache
    with data_store.open(os.path.join(country_dir,CELL_CACHE_FILE)) as f:
        js = json.load(f)

    with data_store.open(os.path.join(country_dir,BACKUP_DIR,CELL_CACHE_FILE[:-5]+"_"+time_stamp+".json"), "w") as f:
        json.dump(js, f)

    #p2p cache
    with data_store.open(os.path.join(country_dir,P2P_CACHE_FILE)) as f:
        js = json.load(f)

    with data_store.open(os.path.join(country_dir,BACKUP_DIR,P2P_CACHE_FILE[:-5]+"_"+time_stamp+".json"), "w") as f:
        json.dump(js, f)
    
    with data_store.open(os.path.join(country_dir,SCHOOLS_VISIBILITY_CACHE_FILE)) as f:
        json.load(f)
    
    with data_store.open(os.path.join(country_dir,BACKUP_DIR,SCHOOLS_VISIBILITY_CACHE_FILE[:-5]+"_"+time_stamp+".json"), "w") as f:
        json.dump(js, f)

# This could be a call to GigaSchoolTable at some point...    
def fix_schools(df):
    df_new = df.copy()
    df_new.dropna(subset=['giga_id_school'], inplace=True)

    ####num_students####
    your_column = 'num_students'

    # Step 1: Replace empty values with NaN
    if your_column in df_new:
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

    ####fiber_node_distance####
    your_column = 'fiber_node_distance'

    if your_column in df_new:
        # Step 1: Replace empty values with NaN
        df_new[your_column].replace(r'^\s*$', pd.NA, regex=True, inplace=True)
        df_new[your_column] = pd.to_numeric(df_new[your_column], errors='coerce')   

        #fill na with inf
        df_new[your_column].fillna(math.inf, inplace=True)

        # Step 4: Convert the column to float
        df_new[your_column] = df_new[your_column].astype(float)

    return df_new

def get_country_center_zoom(df, max_zoom_level = 11.75):
    earth_radius = 6371.0

    # get country center
    lats = df['lat'].to_numpy()
    lats = lats[~np.isnan(lats)]
    lons = df['lon'].to_numpy()
    lons = lons[~np.isnan(lons)]
    _center = {'lon': lons.mean(), 'lat': lats.mean()}
    
    #getcountry zoom level
    _xrange, _yrange = np.ptp(lons) ,np.ptp(lats)
    max_bound = np.deg2rad(max(_xrange, _yrange)) * earth_radius
    _zoom = max_zoom_level - np.log(max_bound)
    
    return _center, _zoom

def get_country_default(country, workspace = 'workspace', schools_dir = SCHOOLS_DEFAULT_PATH, costs_target_dir = COSTS_DEFAULT_PATH):

    default = copy.deepcopy(empty_default_dict)
    
    default['data']['country'] = country
    default['data']['workspace'] = workspace
    #school master file
    master_file = os.path.join(schools_dir, country + MASTER_DEFAULT_NAME)
    with schools_data_store.open(master_file) as f:
        df = pd.read_csv(f, dtype={"lat": "float32", "lon": "float32"})

    df_fixed = fix_schools(df)
    
    costs_dir = os.path.join(workspace,costs_target_dir)
    country_dir = os.path.join(workspace,country)
    #if schools file does not exist copy it and create empty files
    if not data_store.file_exists(os.path.join(country_dir,SCHOOLS_FILE)):
        data_store.write_file(os.path.join(country_dir,SCHOOLS_FILE),df_fixed.to_csv(index=False))
        create_empty_tech_files(country_dir)
        create_empty_caches(country_dir)
        #in this case, only sat is available and maybe cell
        default["model_defaults"]["available_tech"]["fiber"] = df_fixed["fiber_node_distance"].notnull().any() if 'fiber_node_distance' in df_fixed else False
        default["model_defaults"]["available_tech"]["cellular"] = df_fixed["coverage_type"].notnull().any() if 'coverage_type' in df_fixed else False
        default["model_defaults"]["available_tech"]["p2p"] = False
        default["model_defaults"]["available_tech"]["schools_as_nodes"] = False
        default["model_defaults"]["fiber"]["capex"]["schools_as_fiber_nodes"] = df_fixed["type_connectivity"].apply(is_fiber).any() if 'type_connectivity' in df_fixed else False
    else:
        with data_store.open(os.path.join(country_dir,SCHOOLS_FILE)) as f:
            df2 = pd.read_csv(f, dtype={"lat": "float32", "lon": "float32"})
        if not df_fixed.equals(df2):
            #if the schools are the same then the caches are ok otherwise ko
            if not df_fixed[['giga_id_school','lat','lon']].equals(df2[['giga_id_school','lat','lon']]):
                # we save the old schools file in backup, might be useful to recalculate caches
                time_stamp = datetime.now().strftime("%Y_%m_%d")
                backup_schools_file = SCHOOLS_FILE[:-3]+"_"+time_stamp+".csv"
                data_store.write_file(os.path.join(country_dir,BACKUP_DIR,backup_schools_file),df2.to_csv(index=False))
                copy_caches_to_backup(country_dir)
                create_empty_caches(country_dir)
            
            #in any case we save the new schools file
            data_store.write_file(os.path.join(country_dir,SCHOOLS_FILE),df_fixed.to_csv(index=False))

        #check tech availability
        fiber,cell,p2p,san = check_avail_techs(country_dir,df_fixed)
        default["model_defaults"]["available_tech"]["fiber"] = fiber
        default["model_defaults"]["available_tech"]["cellular"] = cell
        default["model_defaults"]["available_tech"]["p2p"] = p2p
        default["model_defaults"]["available_tech"]["schools_as_nodes"] = san
        default["model_defaults"]["fiber"]["capex"]["schools_as_fiber_nodes"] = san

    #set default country center coordinates
    country_center, country_zoom = get_country_center_zoom(df_fixed, max_zoom_level=11.75)
    default["data"]["country_center"]["lat"] = country_center['lat']
    default["data"]["country_center"]["lon"] = country_center['lon']
    default["data"]["country_zoom"] = country_zoom

    #add costs
    ### cell
    if data_store.file_exists(os.path.join(costs_dir, CELL_CAPEX_FILE)): 
        with data_store.open(os.path.join(costs_dir, CELL_CAPEX_FILE)) as f:
            dfc = pd.read_csv(f, dtype={"Setup cost": "float32"})
        if country in dfc['Country'].values:
            desired_row = dfc[dfc['Country'] == country].iloc[0]
            default["model_defaults"]['cellular']["capex"]["fixed_costs"] = desired_row["Setup cost"]

    if data_store.file_exists(os.path.join(costs_dir, CELL_OPEX_FILE)): 
        with data_store.open(os.path.join(costs_dir, CELL_OPEX_FILE)) as f:
            dfc = pd.read_csv(f, dtype={"Maintenance yearly": "float32", "Cost per Mbps/year": "float32"})
        if country in dfc['Country'].values:
            desired_row = dfc[dfc['Country'] == country].iloc[0]
            default["model_defaults"]['cellular']["opex"]["fixed_costs"] = desired_row["Maintenance yearly"]
            default["model_defaults"]['cellular']["opex"]["annual_bandwidth_cost_per_mbps"] = desired_row["Cost per Mbps/year"]

    if data_store.file_exists(os.path.join(costs_dir, CELL_CSTRS_FILE)): 
        with data_store.open(os.path.join(costs_dir, CELL_CSTRS_FILE)) as f:
            dfc = pd.read_csv(f, dtype={"Max length": "float32", "Annual power required (KWh)": "float32"})
        if country in dfc['Country'].values:
            desired_row = dfc[dfc['Country'] == country].iloc[0]
            default["model_defaults"]['cellular']["constraints"]["maximum_range"] = desired_row["Max length"]
            default["model_defaults"]['cellular']["constraints"]["required_power"] = desired_row["Annual power required (KWh)"]

    ### p2p
    if data_store.file_exists(os.path.join(costs_dir, P2P_CAPEX_FILE)): 
        with data_store.open(os.path.join(costs_dir, P2P_CAPEX_FILE)) as f:
            dfc = pd.read_csv(f, dtype={"Setup cost - school": "float32", "Setup cost - tower": "float32"})
        if country in dfc['Country'].values:
            desired_row = dfc[dfc['Country'] == country].iloc[0]
            default["model_defaults"]['p2p']["capex"]["fixed_costs"] = desired_row["Setup cost - school"]
            default["model_defaults"]['p2p']["capex"]["tower_fixed_costs"] = desired_row["Setup cost - tower"]

    if data_store.file_exists(os.path.join(costs_dir, P2P_OPEX_FILE)): 
        with data_store.open(os.path.join(costs_dir, P2P_OPEX_FILE)) as f:
            dfc = pd.read_csv(f, dtype={"Maintenance yearly": "float32", "Cost per Mbps/year": "float32"})
        if country in dfc['Country'].values:
            desired_row = dfc[dfc['Country'] == country].iloc[0]
            default["model_defaults"]['p2p']["opex"]["fixed_costs"] = desired_row["Maintenance yearly"]
            default["model_defaults"]['p2p']["opex"]["annual_bandwidth_cost_per_mbps"] = desired_row["Cost per Mbps/year"]

    if data_store.file_exists(os.path.join(costs_dir, P2P_CSTRS_FILE)): 
        with data_store.open(os.path.join(costs_dir, P2P_CSTRS_FILE)) as f:
            dfc = pd.read_csv(f, dtype={"Max length": "float32", "Annual power required (KWh)": "float32"})
        if country in dfc['Country'].values:
            desired_row = dfc[dfc['Country'] == country].iloc[0]
            default["model_defaults"]['p2p']["constraints"]["maximum_range"] = desired_row["Max length"]
            default["model_defaults"]['p2p']["constraints"]["required_power"] = desired_row["Annual power required (KWh)"]

    ### fiber
    if data_store.file_exists(os.path.join(costs_dir, FIBER_CAPEX_FILE)): 
        with data_store.open(os.path.join(costs_dir, FIBER_CAPEX_FILE)) as f:
            dfc = pd.read_csv(f, dtype={"Setup cost": "float32", "Cost per km": "float32"})
        if country in dfc['Country'].values:
            desired_row = dfc[dfc['Country'] == country].iloc[0]
            default["model_defaults"]['fiber']["capex"]["fixed_costs"] = desired_row["Setup cost"]
            default["model_defaults"]['fiber']["capex"]["cost_per_km"] = desired_row["Cost per km"]

    if data_store.file_exists(os.path.join(costs_dir, FIBER_OPEX_FILE)): 
        with data_store.open(os.path.join(costs_dir, FIBER_OPEX_FILE)) as f:
            dfc = pd.read_csv(f, dtype={"Cost per Mbps/year": "float32", "Maintenance per km": "float32"})
        if country in dfc['Country'].values:
            desired_row = dfc[dfc['Country'] == country].iloc[0]
            #defaults['fiber']["opex"]["fixed_costs"] = desired_row["Maintenance yearly"] --> Not in original code - we should add it
            default["model_defaults"]['fiber']["opex"]["annual_bandwidth_cost_per_mbps"] = desired_row["Cost per Mbps/year"]
            default["model_defaults"]['fiber']["opex"]["cost_per_km"] = desired_row["Maintenance per km"]

    if data_store.file_exists(os.path.join(costs_dir, FIBER_CSTRS_FILE)): 
        with data_store.open(os.path.join(costs_dir, FIBER_CSTRS_FILE)) as f:
            dfc = pd.read_csv(f, dtype={"Max length": "float32", "Annual power required (KWh)": "float32"})
        if country in dfc['Country'].values:
            desired_row = dfc[dfc['Country'] == country].iloc[0]
            default["model_defaults"]['fiber']["constraints"]["maximum_connection_length"] = desired_row["Max length"]
            default["model_defaults"]['fiber']["constraints"]["required_power"] = desired_row["Annual power required (KWh)"]

    ### satellite
    if data_store.file_exists(os.path.join(costs_dir, SAT_CAPEX_FILE)): 
        with data_store.open(os.path.join(costs_dir, SAT_CAPEX_FILE)) as f:
            dfc = pd.read_csv(f, dtype={"Setup cost": "float32"})
        if country in dfc['Country'].values:
            desired_row = dfc[dfc['Country'] == country].iloc[0]
            default["model_defaults"]['satellite']["capex"]["fixed_costs"] = desired_row["Setup cost"]

    if data_store.file_exists(os.path.join(costs_dir, SAT_OPEX_FILE)): 
        with data_store.open(os.path.join(costs_dir, SAT_OPEX_FILE)) as f:
            dfc = pd.read_csv(f, dtype={"Maintenance yearly": "float32", "Cost per Mbps/year": "float32"})
        if country in dfc['Country'].values:
            desired_row = dfc[dfc['Country'] == country].iloc[0]
            default["model_defaults"]['satellite']["opex"]["fixed_costs"] = desired_row["Maintenance yearly"]
            default["model_defaults"]['satellite']["opex"]["annual_bandwidth_cost_per_mbps"] = desired_row["Cost per Mbps/year"]

    if data_store.file_exists(os.path.join(costs_dir, SAT_CSTRS_FILE)): 
        with data_store.open(os.path.join(costs_dir, SAT_CSTRS_FILE)) as f:
            dfc = pd.read_csv(f, dtype={"Annual power required (KWh)": "float32"})
        if country in dfc['Country'].values:
            desired_row = dfc[dfc['Country'] == country].iloc[0]
            default["model_defaults"]['satellite']["constraints"]["required_power"] = desired_row["Annual power required (KWh)"]
                
    ### electricity
    if data_store.file_exists(os.path.join(costs_dir, ELECTRICITY_CAPEX_FILE)): 
        with data_store.open(os.path.join(costs_dir, ELECTRICITY_CAPEX_FILE)) as f:
            dfc = pd.read_csv(f, dtype={"Solar cost (USD/Watt)": "float32"})
        if country in dfc['Country'].values:
            desired_row = dfc[dfc['Country'] == country].iloc[0]
            default["model_defaults"]['electricity']["capex"]["solar_cost_per_watt"] = desired_row["Solar cost (USD/Watt)"]

    if data_store.file_exists(os.path.join(costs_dir, ELECTRICITY_OPEX_FILE)): 
        with data_store.open(os.path.join(costs_dir, ELECTRICITY_OPEX_FILE)) as f:
            dfc = pd.read_csv(f, dtype={"Cost per kWh": "float32"})
        if country in dfc['Country'].values:
            desired_row = dfc[dfc['Country'] == country].iloc[0]
            default["model_defaults"]['electricity']["opex"]["cost_per_kwh"] = desired_row["Cost per kWh"]

    if data_store.file_exists(os.path.join(costs_dir, ELECTRICITY_CSTRS_FILE)): 
        with data_store.open(os.path.join(costs_dir, ELECTRICITY_CSTRS_FILE)) as f:
            dfc = pd.read_csv(f, dtype={"Power required per school (Watts)": "float32"})
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

