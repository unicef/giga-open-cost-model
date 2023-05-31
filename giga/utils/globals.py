import os


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# tracks the default configurations for countries
COUNTRY_DEFAULT_RELATIVE_DIR = "../../conf/countries"
COUNTRY_DEFAULT_WORKSPACE = os.path.join(ROOT_DIR, COUNTRY_DEFAULT_RELATIVE_DIR)
