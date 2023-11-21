import pandas as pd
import numpy as np
import math
import os

from giga.app.config import get_registered_countries
from giga.data.store.stores import COUNTRY_DATA_STORE as data_store
from giga.utils.globals import *

def get_countries_overview_table():
    country_stats = dict()

    for country_ in get_registered_countries():
        country_dir = os.path.join('workspace', country_)
        country_stats[country_] = dict()
        country_stats[country_]['fiber_file_exists'] = data_store.file_size(os.path.join(country_dir, FIBER_FILE))> 0
        country_stats[country_]['cell_file_exists'] = data_store.file_size(os.path.join(country_dir, CELL_FILE))>0

        with data_store.open(os.path.join(country_dir,SCHOOLS_FILE)) as f:
            df_school = pd.read_csv(f, low_memory=False)
            n_rows = len(df_school)

        country_stats[country_].update(
            dict(
                n_schools = n_rows,
                n_unconn_schools = sum(df_school.connectivity != 'Yes'),
                nonnull_perc_connectivity = np.round(100 * df_school['connectivity'].notnull().sum()/n_rows, 2),
                nonnull_perc_ele = np.round(100 * df_school['electricity'].notnull().sum()/n_rows, 2),
                nonnull_perc_dist2fiber = np.round(100 * sum(df_school['fiber_node_distance'] != math.inf)/n_rows, 2),
                nonnull_perc_coverage = np.round(100 * df_school['coverage_availability'].notnull().sum()/n_rows, 2),
            )
        )

        country_stats[country_].update(
            dict(
                fiber_available = country_stats[country_]['fiber_file_exists'] or country_stats[country_]['nonnull_perc_dist2fiber'] > 0,
                cell_available = country_stats[country_]['cell_file_exists'] or country_stats[country_]['nonnull_perc_coverage'] > 0,
                p2p_available = country_stats[country_]['cell_file_exists'],
                satellite_available = True
            )
        )
        
    return pd.DataFrame(country_stats).T

def save_countries_overview_table(table: pd.DataFrame, path: str):
    suffix_ = path.split('.')[-1]
    if suffix_ == 'xlsx':
        table.to_excel(path, sheet_name = 'Countries Overview', index = True, index_label = 'Country', engine = 'openpyxl')
    elif suffix_ == 'csv':
        table.to_csv(path, index= True, index_label = 'Country')
    else:
        raise ValueError('File format is not supported. Supported file formats: "xlsx" and "csv".')