import os


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# tracks the default configurations for countries
COUNTRY_DEFAULT_RELATIVE_DIR = "../../conf/countries"
COUNTRY_DEFAULT_WORKSPACE = os.path.join(ROOT_DIR, COUNTRY_DEFAULT_RELATIVE_DIR)

#repository cost path
COSTS_DEFAULT_PATH = "costs/"

GIGA_LOGO_DEFAULT_PATH = "/data/reports/common/"

ACKS_DEFAULT_PATH = "reports/"

#country code path
COUNTRY_CODE_DEFAULT_PATH = "source/misc/"

#country code file name
COUNTRY_CODE_DEFAULT_NAME = "iso3codes.csv"

#master files path
SCHOOLS_DEFAULT_PATH = "gold/school_data/"

#master files name
MASTER_DEFAULT_NAME = "_school_geolocation_coverage_master.csv" 

#backup dir
BACKUP_DIR = "backup"

#file names of extra file
SCHOOLS_FILE = "schools.csv"
CELL_FILE = "cellular.csv"
CELL_CACHE_FILE = "cellular_cache.json"
FIBER_FILE = "fiber.csv"
FIBER_CACHE_FILE = "fiber_cache.json"
P2P_CACHE_FILE = "p2p_cache.json"
SCHOOLS_CACHE_FILE = "school_cache.json"
SCHOOLS_VISIBILITY_CACHE_FILE = "school_visibility_cache.json"

GIGA_LOGO_FILE = "giga_logo.png"
ACKS_FILE = "acknowledgements.txt"

#file names of cost files
CELL_CAPEX_FILE = "cell_capex.csv"
CELL_OPEX_FILE = "cell_opex.csv"
CELL_CSTRS_FILE = "cell_cstrs.csv"
FIBER_CAPEX_FILE = "fiber_capex.csv"
FIBER_OPEX_FILE = "fiber_opex.csv"
FIBER_CSTRS_FILE = "fiber_cstrs.csv"
P2P_CAPEX_FILE = "p2p_capex.csv"
P2P_OPEX_FILE = "p2p_opex.csv"
P2P_CSTRS_FILE = "p2p_cstrs.csv"
SAT_CAPEX_FILE = "cell_capex.csv"
SAT_OPEX_FILE = "cell_opex.csv"
SAT_CSTRS_FILE = "cell_cstrs.csv"
ELECTRICITY_CAPEX_FILE = "electricity_capex.csv"
ELECTRICITY_OPEX_FILE = "electricity_opex.csv"
ELECTRICITY_CSTRS_FILE = "electricity_cstrs.csv"

# General defaults
YEARS_OPEX = 5
BANDWIDTH_DEMAND = 20
ECONOMIES_OF_SCALE = True

#num students
DEFAULT_NUM_STUDENTS = 50
