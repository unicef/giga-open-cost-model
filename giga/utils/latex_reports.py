from pylatex import Document, Command
from pylatex.utils import NoEscape
import numpy as np
import math

from giga.viz.notebooks.parameters.groups.data_parameter_manager import country_key_to_name
from giga.report.infra.report import get_report_text as get_infra_report_text
from giga.report.cost.report import get_report_text as get_cost_report_text
from giga.report.merged.report import get_report_text as get_merged_report_text
from giga.utils.globals import ACKS_DEFAULT_PATH, ACKS_FILE
from giga.data.store.stores import COUNTRY_DATA_STORE as data_store
from giga.data.store.adls_store import COUNTRY_DATA_DIR
import os

MILLION = 1000000
KILOMETER_TO_METER = 1000

def get_infra_report_variables(data_space):

    vals = {}
    vals['_selected_schools'] = data_space.selected_space
    vals['country'] = data_space.config.school_data_conf.country_id
    
    schools_table = data_space.schools_to_frame()
    schools_connected = schools_table[schools_table['connected']]
    schools_unconnected = schools_table[schools_table['connected']==False]
    ele_counts = schools_table['has_electricity'].value_counts()

    acks_dir = os.path.join(COUNTRY_DATA_DIR, ACKS_DEFAULT_PATH, vals['country'], ACKS_FILE)

    try:
        with data_store.open(acks_dir) as f:
            vals['acks_text'] = f.read()
    except:
        vals['acks_text'] = ''
    
    vals['country_name'] = country_key_to_name(vals['country'])
    vals['num_schools'] = len(schools_table)
    vals['num_unconn'] = len(schools_unconnected)
    vals['num_conn'] = len(schools_connected)
    vals['num_students'] = schools_table['num_students'].sum()
    vals['num_fnodes'] = len(data_space.fiber_coordinates)
    vals['num_cells'] = len(data_space.cell_tower_coordinates)
    vals['num_has_ele'] = ele_counts[True]
    vals['num_has_no_ele'] = ele_counts[False]
    vals['perc_conn_unknown'] = 100 * sum(schools_table['connectivity_status'] == 'Unknown')/vals['num_schools']
    vals['perc_conn_known'] = 100 - vals['perc_conn_unknown']
    vals['perc_conn_type_unknown'] = 100 * sum(schools_table['type_connectivity'] == 'Unknown')/vals['num_schools']
    vals['perc_conn_type_known'] = 100 - vals['perc_conn_type_unknown']
    vals['perc_ele_unknown'] = 100 * sum(schools_table['electricity'] == 'Unknown')/vals['num_schools']
    vals['perc_ele_known'] = 100 - vals['perc_ele_unknown']
    vals['perc_conn'] = 100 * vals['num_conn']/vals['num_schools']
    vals['perc_unconn'] = 100 - vals['perc_conn']
    vals['perc_has_ele'] = 100 * vals['num_has_ele']/vals['num_schools']
    vals['perc_has_no_ele'] = 100 * vals['num_has_no_ele']/vals['num_schools']

    schools_unconnected_aux = schools_unconnected.replace([math.inf, -math.inf], float('nan'))

    if any(schools_unconnected.nearest_fiber != math.inf):
        vals['perc_fnode_dist'] = 100 * sum(schools_unconnected["nearest_fiber"] <= 10 * KILOMETER_TO_METER) / vals['num_unconn']
        vals['avg_fnode_dist'] = schools_unconnected_aux['nearest_fiber'].mean()/KILOMETER_TO_METER
    else:
        vals['perc_fnode_dist'] = math.inf
        vals['avg_fnode_dist'] = math.inf
    
    if any(schools_unconnected.nearest_cell_tower != math.inf):
        vals['perc_cell_dist'] = 100 * sum(schools_unconnected["nearest_cell_tower"] <= 3 * KILOMETER_TO_METER) / vals['num_unconn']
        vals['avg_cell_dist'] = schools_unconnected_aux['nearest_cell_tower'].mean()/KILOMETER_TO_METER
    else:
        vals['perc_cell_dist'] = math.inf
        vals['avg_cell_dist'] = math.inf
    
    if any(schools_unconnected.nearest_visible_cell_tower != math.inf):
        vals['perc_p2p_dist'] = 100 * sum(schools_unconnected["nearest_visible_cell_tower"] <= 3 * KILOMETER_TO_METER) / vals['num_unconn']
        vals['avg_p2p_dist'] = schools_unconnected_aux['nearest_visible_cell_tower'].mean()/KILOMETER_TO_METER
    else:
        vals['perc_p2p_dist'] = math.inf
        vals['avg_p2p_dist'] = math.inf

    # correct rounding
    vals = round_vals(vals)

    return vals


def get_cost_report_variables(dashboard):
    
    vals = {}
    input_config = dashboard.inputs.config
    vals['country'] = dashboard.country
    stats = dashboard.results
    selected_schools = dashboard.selected_schools
    schools_complete_table = stats.complete_school_table
    output_table = stats.output_cost_table
    output_table_full = stats.output_cost_table_full

    acks_dir = os.path.join(COUNTRY_DATA_DIR, ACKS_DEFAULT_PATH, vals['country'], ACKS_FILE)

    try:
        with data_store.open(acks_dir) as f:
            vals['acks_text'] = f.read()
    except:
        vals['acks_text'] = ''

    vals['country_name'] = country_key_to_name(vals['country'])
    vals['num_all_schools'] = len(schools_complete_table)
    vals['num_schools'] = len(selected_schools)
    vals['num_unconn_schools'] = len(stats.output_space.minimum_cost_result)
    vals['budget_cstr'] = input_config['scenario_parameters']['cost_minimizer_config']['budget_constraint']
    vals['max_fiber_conn'] = 0
    vals['input_technologies'] = []
    vals['scenario_id'] = input_config['scenario_parameters']['scenario_id']

    for tech_config in input_config['scenario_parameters']['technologies']:
        vals['input_technologies'].append(tech_config['technology'])
        if tech_config['technology']=='Fiber':
            vals['max_fiber_conn'] = tech_config['constraints']['maximum_connection_length']
            vals['schools_as_fiber_nodes'] = tech_config['capex']['schools_as_fiber_nodes']

    vals['min_bandwidth'] = input_config['scenario_parameters']['bandwidth_demand']
    vals['opex_years'] = input_config['scenario_parameters']['years_opex']
    vals['num_schools_to_connect'] = sum(output_table['feasible'])
    vals['num_schools_over_budget'] = len(output_table_full[output_table_full["reason"] == "BUDGET_EXCEEDED"])
    vals['total_cost'] = sum(output_table["total_cost"].dropna())/MILLION
    vals['total_capex_cost_mil'] = stats.totals_lookup_table_mil['Technology CapEx']+stats.totals_lookup_table_mil['Electricity CapEx']
    vals['total_capex_cost'] = vals['total_capex_cost_mil']*MILLION
    vals['total_opex_cost_mil'] = stats.totals_lookup_table_mil['Annual Recurring Cost']*vals['opex_years']
    vals['total_opex_cost'] = vals['total_opex_cost_mil']*MILLION
    
    vals['num_students'] = np.round(MILLION*vals['total_cost']/stats.average_cost_per_student, 0)
    vals['avg_school_cost'] = stats.average_cost_per_school
    vals['avg_student_cost'] = stats.average_cost_per_student
    
    # electricity related matrix
    vals['ele_capex_total_mil'] = stats.totals_lookup_table_mil['Electricity CapEx']
    vals['ele_capex_total'] = vals['ele_capex_total_mil']*MILLION
    vals['ele_opex_year'] = sum(output_table[output_table['feasible']]['electricity_opex'])
    vals['ele_opex_total'] = vals['ele_opex_year']*vals['opex_years']
    vals['ele_opex_total_mil'] = vals['ele_opex_total']/MILLION
    vals['ele_cost_total'] = vals['ele_capex_total'] + vals['ele_opex_total']
    vals['ele_perc_capex'] =  100*vals['ele_capex_total_mil']/vals['total_cost']
    vals['ele_perc_opex'] = 100*vals['ele_opex_total_mil']/vals['total_cost']
    vals['schools_need_electricity'] = len(output_table[output_table["electricity_capex"] > 0.0])
    vals['ele_capex_per_school'] = vals['ele_capex_total']/vals['schools_need_electricity']
    vals['ele_opex_per_school_year'] = vals['ele_opex_year']/vals['num_schools_to_connect']
    vals['ele_opex_per_school_month'] = vals['ele_opex_per_school_year']/12

    # tech related costs per tech type
    tech_name_dict = {'Fiber': 'fiber', 'Cellular': 'cell', 'P2P': 'p2p', 'Satellite': 'sat'}
    
    for tech_ in tech_name_dict.keys():

        for cost_ in ['capex', 'opex']:
            val_name = tech_name_dict[tech_] + '_' + cost_ + ('_total' if cost_=='capex' else '_year')
            vals[val_name] = sum(output_table[(output_table['technology'] == tech_)&(output_table['feasible'])][cost_])
        
        vals[tech_name_dict[tech_] +'_opex_total'] = vals[tech_name_dict[tech_]+'_opex_year'] * vals['opex_years']
        
        try:
            vals[tech_name_dict[tech_]+'_schools'] = stats.technology_counts[tech_]
            vals[tech_name_dict[tech_]+'_capex_per_school'] = vals[tech_name_dict[tech_]+'_capex_total']/stats.technology_counts[tech_]
            vals[tech_name_dict[tech_]+'_opex_per_school_year'] = vals[tech_name_dict[tech_]+'_opex_year']/stats.technology_counts[tech_]
        except:
            vals[tech_name_dict[tech_]+'_schools'] = 0
            vals[tech_name_dict[tech_]+'_capex_per_school'] = 0
            vals[tech_name_dict[tech_]+'_opex_per_school_year'] = 0
        
        vals[tech_name_dict[tech_] +'_opex_per_school_month'] = vals[tech_name_dict[tech_]+'_opex_per_school_year']/12
        vals[tech_name_dict[tech_] +'_opex_per_school_total'] = vals[tech_name_dict[tech_]+'_opex_per_school_year'] * vals['opex_years']
        vals[tech_name_dict[tech_] +'_cost_total'] = (vals[tech_name_dict[tech_]+'_capex_total'] + vals[tech_name_dict[tech_]+'_opex_total'])
        vals[tech_name_dict[tech_] +'_cost_total_mil'] = vals[tech_name_dict[tech_] +'_cost_total']/MILLION
        vals[tech_name_dict[tech_]+'_perc_schools'] = 100 * vals[tech_name_dict[tech_]+'_schools']/vals['num_schools_to_connect']

    # all tech costs
    vals['tech_capex_total_mil'] = stats.totals_lookup_table_mil['Technology CapEx']
    vals['tech_capex_total'] = vals['tech_capex_total_mil']*MILLION
    vals['tech_opex_year'] = vals['fiber_opex_year'] + vals['cell_opex_year'] + vals['p2p_opex_year'] + vals['sat_opex_year']
    vals['tech_opex_total'] = vals['tech_opex_year']*vals['opex_years']
    vals['tech_opex_total_mil'] = vals['tech_opex_total']/MILLION
    vals['tech_cost_total'] = vals['tech_capex_total'] + vals['tech_opex_total']
    vals['tech_perc_opex'] = 100*vals['tech_opex_total_mil'] /vals['total_cost']
    vals['tech_perc_capex'] = 100*vals['tech_capex_total_mil']/vals['total_cost']

    # tech type shares of total tech cost
    for tech_ in tech_name_dict.values():
        vals[tech_+'_perc_of_tech'] = 100*vals[tech_+'_cost_total']/vals['tech_cost_total']
    
    # year one cost metrics
    vals['total_cost_year_one'] = (vals['total_capex_cost_mil'] + stats.totals_lookup_table_mil['Annual Recurring Cost'])*MILLION
    vals['tech_perc_capex_year_one'] = 100*vals['tech_capex_total']/vals['total_cost_year_one']
    vals['tech_perc_opex_year_one'] = 100*vals['tech_opex_year'] /vals['total_cost_year_one']
    vals['ele_perc_capex_year_one'] = 100*vals['ele_capex_total']/vals['total_cost_year_one']
    vals['ele_perc_opex_year_one'] = 100*vals['ele_opex_year']/vals['total_cost_year_one']
    vals['avg_cost_student_year_one'] = vals['total_cost_year_one']/vals['num_students']
    vals['avg_cost_school_year_one'] = vals['total_cost_year_one']/vals['num_schools_to_connect']

    # fiber length
    vals['fiber_total_kms'] = sum([c.distance for c in stats.fiber_connections]) / KILOMETER_TO_METER

    # correct rounding
    vals = round_vals(vals)

    return vals

def round_vals(vals):
    vals = vals.copy()

    for key_, value_ in vals.items():
        if value_ == 0 and not isinstance(value_, bool):
            vals[key_] = '0'
        elif isinstance(value_, float):
            value_round = np.round(value_, 2)
            if value_round.is_integer():
                vals[key_] = int(value_round)
            else:
                vals[key_] = value_round
    
    return vals


def format_vals(vals):
    vals = vals.copy()

    for key_, value_ in vals.items():
        if 'perc_' in key_ and value_ == 0:
            vals[key_] = 'less\, than\, 0.01'

        if not (isinstance(value_, str) or isinstance(value_, list) or isinstance(value_, dict) or isinstance(value_, bool)) and value_!= math.inf:
            vals[key_] = f'{value_:,}'
    
    return vals

def generate_cost_report(dashboard):

    #report "variables"
    vals_num = get_cost_report_variables(dashboard = dashboard)
    vals = format_vals(vals_num)

    # Create a LaTeX document object
    geometry_options = {"tmargin":"3cm","lmargin":"3cm","margin":"3cm"}
    doc = Document(geometry_options= geometry_options,documentclass='report',document_options=['12pt', 'a4paper'])

    doc.preamble.append(Command(NoEscape(r'usepackage[utf8]{inputenc}')))
    doc.preamble.append(Command(NoEscape(r'usepackage[T1]{fontenc}')))
    doc.preamble.append(Command(NoEscape(r'usepackage{graphicx}')))
    doc.preamble.append(Command(NoEscape(r'usepackage{multirow}')))
    doc.preamble.append(Command(NoEscape(r'usepackage{subcaption}')))

    doc = append_cost_report_vals(doc, vals)

    latex_source = get_cost_report_text(vals = vals)

    # Add the LaTeX source to the document
    doc.append(NoEscape(latex_source))

    return doc


def generate_infra_report(data_space):

    #report "variables"
    vals_num = get_infra_report_variables(data_space)
    vals = format_vals(vals_num)

    # Create a LaTeX document object
    geometry_options = {"tmargin":"3cm","lmargin":"3cm","margin":"3cm"}
    doc = Document(geometry_options= geometry_options,documentclass='report',document_options=['12pt', 'a4paper'])
    doc.preamble.append(Command(NoEscape(r'usepackage[utf8]{inputenc}')))
    doc.preamble.append(Command(NoEscape(r'usepackage[T1]{fontenc}')))
    doc.preamble.append(Command(NoEscape(r'usepackage{graphicx}')))

    latex_source = get_infra_report_text(vals = vals)

    # Add the LaTeX source to the document
    doc.append(NoEscape(latex_source))

    return doc

def generate_merged_report(dashboard):

    data_space = dashboard.results.data_space
    selected_schools = dashboard.selected_schools
    data_space_selected = data_space.filter_schools(selected_schools)

    infra_vals_num = get_infra_report_variables(data_space=data_space)
    infra_selected_vals_num = get_infra_report_variables(data_space=data_space_selected)
    cost_vals_num = get_cost_report_variables(dashboard)

    infra_vals = format_vals(infra_vals_num)
    infra_selected_vals = format_vals(infra_selected_vals_num)
    cost_vals = format_vals(cost_vals_num)

    # Create a LaTeX document object
    geometry_options = {"tmargin":"3cm","lmargin":"3cm","margin":"3cm"}
    doc = Document(geometry_options= geometry_options,documentclass='report',document_options=['12pt', 'a4paper'])

    doc.preamble.append(Command(NoEscape(r'usepackage[utf8]{inputenc}')))
    doc.preamble.append(Command(NoEscape(r'usepackage[T1]{fontenc}')))
    doc.preamble.append(Command(NoEscape(r'usepackage{graphicx}')))
    doc.preamble.append(Command(NoEscape(r'usepackage{multirow}')))
    doc.preamble.append(Command(NoEscape(r'usepackage{subcaption}')))

    doc = append_cost_report_vals(doc, cost_vals)
    
    latex_source = get_merged_report_text(infra_vals=infra_vals, infra_selected_vals=infra_selected_vals, cost_vals=cost_vals)

    # Add the LaTeX source to the document
    doc.append(NoEscape(latex_source))

    return doc

def append_cost_report_vals(doc, vals):
    
    doc.preamble.append(Command(NoEscape(r"newcommand{{\country}}{{{}}}".format(vals['country_name']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\totalnumschools}}{{${}$}}'.format(vals['num_schools']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\totalnumunconn}}{{${}$}}'.format(vals['num_unconn_schools']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\budgetcstr}}{{${}$}}'.format(vals['budget_cstr']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\maxfiber}}{{${}$}}'.format(vals['max_fiber_conn']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\schoolsasnodes}}{{${}$}}'.format(vals['schools_as_fiber_nodes']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\minbandwidth}}{{${}$}}'.format(vals['min_bandwidth']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\opexyears}}{{${}$}}'.format(vals['opex_years']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\numtoconn}}{{${}$}}'.format(vals['num_schools_to_connect']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\numoverbudget}}{{${}$}}'.format(vals['num_schools_over_budget']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\totalcost}}{{${}$}}'.format(vals['total_cost']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\totalcapexcost}}{{${}$}}'.format(vals['total_capex_cost_mil']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\totalopexcost}}{{${}$}}'.format(vals['total_opex_cost_mil']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\fiberschools}}{{${}$}}'.format(vals['fiber_schools']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\cellschools}}{{${}$}}'.format(vals['cell_schools']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\ptopschools}}{{${}$}}'.format(vals['p2p_schools']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\satschools}}{{${}$}}'.format(vals['sat_schools']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\eleschools}}{{${}$}}'.format(vals['schools_need_electricity']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\fibercapexps}}{{${}$}}'.format(vals['fiber_capex_per_school']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\cellcapexps}}{{${}$}}'.format(vals['cell_capex_per_school']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\ptopcapexps}}{{${}$}}'.format(vals['p2p_capex_per_school']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\satcapexps}}{{${}$}}'.format(vals['sat_capex_per_school']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\elecapexps}}{{${}$}}'.format(vals['ele_capex_per_school']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\fibercapextot}}{{${}$}}'.format(vals['fiber_capex_total']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\cellcapextot}}{{${}$}}'.format(vals['cell_capex_total']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\ptopcapextot}}{{${}$}}'.format(vals['p2p_capex_total']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\satcapextot}}{{${}$}}'.format(vals['sat_capex_total']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\elecapextot}}{{${}$}}'.format(vals['ele_capex_total']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\fiberopexpsm}}{{${}$}}'.format(vals['fiber_opex_per_school_month']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\cellopexpsm}}{{${}$}}'.format(vals['cell_opex_per_school_month']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\ptopopexpsm}}{{${}$}}'.format(vals['p2p_opex_per_school_month']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\satopexpsm}}{{${}$}}'.format(vals['sat_opex_per_school_month']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\eleopexpsm}}{{${}$}}'.format(vals['ele_opex_per_school_month']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\fiberopexpsy}}{{${}$}}'.format(vals['fiber_opex_per_school_year']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\cellopexpsy}}{{${}$}}'.format(vals['cell_opex_per_school_year']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\ptopopexpsy}}{{${}$}}'.format(vals['p2p_opex_per_school_year']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\satopexpsy}}{{${}$}}'.format(vals['sat_opex_per_school_year']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\eleopexpsy}}{{${}$}}'.format(vals['ele_opex_per_school_year']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\fiberopexyear}}{{${}$}}'.format(vals['fiber_opex_year']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\cellopexyear}}{{${}$}}'.format(vals['cell_opex_year']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\ptopopexyear}}{{${}$}}'.format(vals['p2p_opex_year']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\satopexyear}}{{${}$}}'.format(vals['sat_opex_year']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\fiberopextot}}{{${}$}}'.format(vals['fiber_opex_total']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\cellopextot}}{{${}$}}'.format(vals['cell_opex_total']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\ptopopextot}}{{${}$}}'.format(vals['p2p_opex_total']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\satopextot}}{{${}$}}'.format(vals['sat_opex_total']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\eleopextot}}{{${}$}}'.format(vals['ele_opex_total']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\techperccapex}}{{${}$}}'.format(vals['tech_perc_capex']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\eleperccapex}}{{${}$}}'.format(vals['ele_perc_capex']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\techcapextot}}{{${}$}}'.format(vals['tech_capex_total']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\elepercopex}}{{${}$}}'.format(vals['ele_perc_opex']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\techopextot}}{{${}$}}'.format(vals['tech_opex_total']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\techpercopex}}{{${}$}}'.format(vals['tech_perc_opex']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\techperccapexyearone}}{{${}$}}'.format(vals['tech_perc_capex_year_one']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\techpercopexyearone}}{{${}$}}'.format(vals['tech_perc_opex_year_one']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\eleperccapexyearone}}{{${}$}}'.format(vals['ele_perc_capex_year_one']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\elepercopexyearone}}{{${}$}}'.format(vals['ele_perc_opex_year_one']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\techopexyear}}{{${}$}}'.format(vals['tech_opex_year']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\eleopexyear}}{{${}$}}'.format(vals['ele_opex_year']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\fiberpercoftech}}{{${}$}}'.format(vals['fiber_perc_of_tech']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\cellpercoftech}}{{${}$}}'.format(vals['cell_perc_of_tech']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\ptoppercoftech}}{{${}$}}'.format(vals['p2p_perc_of_tech']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\satpercoftech}}{{${}$}}'.format(vals['sat_perc_of_tech']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\techcosttot}}{{${}$}}'.format(vals['tech_cost_total']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\elecosttot}}{{${}$}}'.format(vals['ele_cost_total']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\fibercosttot}}{{${}$}}'.format(vals['fiber_cost_total']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\avgcoststudentyearone}}{{${}$}}'.format(vals['avg_cost_student_year_one']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\avgcostschoolyearone}}{{${}$}}'.format(vals['avg_cost_school_year_one']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\avgschoolcost}}{{${}$}}'.format(vals['avg_school_cost']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\avgstudentcost}}{{${}$}}'.format(vals['avg_student_cost']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\fiberpercschools}}{{${}$}}'.format(vals['fiber_perc_schools']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\cellpercschools}}{{${}$}}'.format(vals['cell_perc_schools']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\ptoppercschools}}{{${}$}}'.format(vals['p2p_perc_schools']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\satpercschools}}{{${}$}}'.format(vals['sat_perc_schools']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\fiberkms}}{{${}$}}'.format(vals['fiber_total_kms']))))

    return doc
