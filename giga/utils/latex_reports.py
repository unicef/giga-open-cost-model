from pylatex import Document, Section, Subsection, Tabular, Command
from pylatex import Math, TikZ, Axis, Plot, Figure, Matrix, Alignat, SubFigure
from pylatex import PageStyle, Head, Foot, MiniPage, \
    StandAloneGraphic, MultiColumn, Tabu, LongTabu, LargeText, MediumText, \
    LineBreak, NewPage, Tabularx, TextColor, simple_page_number, Itemize, Enumerate, Hyperref, Package, \
    TikZ, TikZNode, TikZCoordinate, TikZOptions, NewLine, VerticalSpace
from pylatex.utils import italic, bold, NoEscape, escape_latex
import numpy as np
import math

def get_report_variables(schools_complete_table,schools_unconnected,schools_connected,data_space):
    vals = {}
    num_u = len(schools_unconnected)
    num_c = len(schools_connected)
    n = len(schools_complete_table)
    vals['num_schools'] = len(schools_complete_table)
    vals['num_students'] = schools_complete_table['num_students'].fillna(0).sum()
    vals['num_fnodes'] = len(data_space.fiber_coordinates)
    vals['num_cells'] = len(data_space.cell_tower_coordinates)
    vals['per_conn_unknown'] = ((schools_complete_table['connectivity_status'] == 'Unknown').sum()/n)*100
    vals['per_conn_known'] = 100 - vals['per_conn_unknown']
    vals['per_conn_type_unknown'] = ((schools_complete_table['type_connectivity'] == 'Unknown').sum()/n)*100
    vals['per_conn_type_known'] = 100 - vals['per_conn_type_unknown']
    vals['per_ele_unknown'] = ((schools_complete_table['electricity'] == 'Unknown').sum()/n)*100
    vals['per_ele_known'] = 100 - vals['per_ele_unknown']
    vals['num_conn'] = num_c
    vals['num_unconn'] = num_u
    vals['perc_conn'] = int((num_c/n)*100)
    vals['perc_unconn'] = 100 - vals['perc_conn']
    vals['perc_fnode_dist'] = round(sum(schools_unconnected["nearest_fiber"] <= 10000) / num_u * 100)
    vals['perc_cell_dist'] = round(sum(schools_unconnected["nearest_cell_tower"] <= 3000) / num_u * 100)
    vals['perc_p2p_dist'] = round(sum(schools_unconnected["nearest_visible_cell_tower"] <= 3000) / num_u * 100)

    schools_unconnected_aux = schools_unconnected.replace([math.inf, -math.inf], float('nan'))

    vals['avg_fnode_dist'] = round(schools_unconnected_aux['nearest_fiber'].mean())/1000.0
    vals['avg_cell_dist'] = round(schools_unconnected_aux['nearest_cell_tower'].mean())/1000.0
    vals['avg_p2p_dist'] = round(schools_unconnected_aux['nearest_visible_cell_tower'].mean())/1000.0

    return vals


def get_cost_report_variables(config,selected_schools,stats):
    vals = {}
    output_table = stats.output_cost_table
    output_table_full = stats.output_cost_table_full
    tech_name_dict = {'Fiber': 'fiber', 'Cellular': 'cell', 'P2P': 'p2p', 'Satellite': 'sat'}
    MILLION = 1000000
   
    vals['num_schools'] = len(selected_schools)
    vals['num_unconn_schools'] = len(stats.output_space.minimum_cost_result)
    vals['budget_cstr'] = config['scenario_parameters']['cost_minimizer_config']['budget_constraint']
    vals['max_fiber_conn'] = 0
    for tech in config['scenario_parameters']['technologies']:
        if tech['technology']=='Fiber':
            vals['max_fiber_conn'] = tech['constraints']['maximum_connection_length']
            vals['schools_as_fiber_nodes'] = tech['capex']['schools_as_fiber_nodes']

    vals['min_bandwidth'] = config['scenario_parameters']['bandwidth_demand']
    vals['opex_years'] = config['scenario_parameters']['years_opex']
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
    for tech_ in ['Fiber', 'Cellular', 'P2P', 'Satellite']:

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
    vals['fiber_total_kms'] = np.round(sum([c.distance for c in stats.fiber_connections]) / 1000, 2)

    # round variables
    #var_no_round = ['num_schools', 'num_unconn_schools', 'opex_years', 'num_students', 'num_schools_to_connect', 'num_schools_over_budget', 'schools_need_electricity']
    #var_no_round = var_no_round + [tech_+'_schools' for tech_ in tech_name_dict.values()]

    # correct rounding
    for key_, value_ in vals.items():

        if value_ == 0:
            vals[key_] = '0'
        elif not isinstance(value_, int):
            value_round = np.round(value_, 2)
            if value_round.is_integer():
                vals[key_] = int(value_round)
            else:
                vals[key_] = value_round

    return vals

def generate_costmodel_report(config,selected_schools,stats,country,schools_complete_table,schools_unconnected,schools_connected,data_space):
    # Create a LaTeX document object
    geometry_options = {"tmargin":"3cm","lmargin":"3cm","margin":"3cm"}
    doc = Document(geometry_options= geometry_options,documentclass='report',document_options=['12pt', 'a4paper'])

    doc.preamble.append(Command(NoEscape(r'usepackage[utf8]{inputenc}')))
    doc.preamble.append(Command(NoEscape(r'usepackage[T1]{fontenc}')))
    doc.preamble.append(Command(NoEscape(r'usepackage{graphicx}')))
    doc.preamble.append(Command(NoEscape(r'usepackage{multirow}')))
    doc.preamble.append(Command(NoEscape(r'usepackage{subcaption}')))

    #report "variables"
    vals_num = get_cost_report_variables(config,selected_schools,stats)

    def format_vals(vals):
        vals = vals.copy()

        for key_, value_ in vals.items():
            if 'perc_' in key_ and value_ == 0:
                vals[key_] = 'less\, than\, 0.01'

            if (not isinstance(value_, str)) and value_>1000 and value_!= math.inf:
                vals[key_] = f'{value_:,}'
        
        return vals
    
    vals = format_vals(vals_num)

    str1 = r"newcommand{{\country}}{{{}}}".format(country)
    doc.preamble.append(Command(NoEscape(str1)))
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

    scenario_id = config['scenario_parameters']['scenario_id']
    budget_cstr = vals['budget_cstr']

    latex_source = r"""

    % Title Page
    \begin{titlepage}
        \centering
        \includegraphics[scale=0.15]{giga_logo.png} % Add your logo or comment this line
        \vspace{1cm}
    
        {\huge\bfseries \country{} - School Connectivity Project Planning Report\par}
        \vspace{1cm}
        {\Large Finance Team, Giga\par}
        \vfill
        {\large \today\par}
    \end{titlepage}

    % Table of Contents
    \tableofcontents
    \newpage

    \chapter*{Foreword}
    \addcontentsline{toc}{chapter}{Foreword}
    This report is intended for government officials who have used Giga’s Cost Model Tool for estimating the costs of a connectivity project (i.e., connecting a certain number of schools) or conducted a project with Giga using this tool.   The report serves to provide an overview of the tool, its estimates and limitations, and the potential costs of connecting all schools in the country.  

    The purpose of this report is to summarize cost estimates for a school connectivity project and to describe the supporting methodology that Giga’s Cost Model uses to arrive at such estimates, including the model’s limitations and generalizations.  This report is intended to provide basic project information to key stakeholders to support preliminary project scoping and financial planning.  Note that actual project costs are a market function and can only be secured through outreach (e.g., RFI, RFP, etc.) to market participants.

    \chapter{Cost Model Report}

    % Section 1
    \section{Introduction}
    The Government of \country{} recognizes the importance of digitalization and connectivity to enabling access to quality education as an essential component for achieving its national development goals. As part of its efforts to promote education and technology, the government has partnered with the Giga initiative to connect all schools to the internet. 

    Giga is a global initiative launched in 2019 by UNICEF and the International Telecommunication Union (ITU) that aims to connect every school to the internet by 2030. The initiative is currently active in more than 50 countries worldwide and is supported by a coalition of public and private partners, including governments, technology companies, and civil society organizations. 

    In \country{}, Giga is working with the government to connect schools across the country to the internet. The initiative's goal is to provide reliable and affordable internet access to all schools, teachers, and students in Rwanda enabling them to access educational resources and participate in the digital economy fully. Giga will support Rwanda in leveraging existing infrastructure, exploring possible technologies, and supporting the mobilization of financial resources to implement connectivity projects. 

    \newpage

    % Section 2
    \section{Scenario and options}

    In this section we describe the scenario and most relevant options selected in order to yield the cost estimates that will follow in the next sections.

    \subsection{Scenario Description}
    """

    if "minimum_cost" in scenario_id:
        latex_source += r"The scenario chosen is that of \textbf{Lowest Cost}, i.e., minimize the total cost of connecting all schools to the internet."+"\n"
    elif "priorities" in scenario_id:
        latex_source += r"The scenario chosen is that of \textbf{Priorities}, i.e., we connect schools with a certain technology priority: fiber, cellular, microwave and satellite."+"\n"

    latex_source += r"\subsection{Budget constraint}"+"\n"

    if budget_cstr==math.inf:
        latex_source+= r"The scenario below was run without any budget constraints."+"\n"
    else:
        latex_source += r"The scenario below was run with a budget of \budgetcstr{} (USD)."+"\n"

    latex_source += r"\subsection{Technologies used}"+"\n"+"For this cost model estimation we allowed the use of the following technologies:"
    for tech in config['scenario_parameters']['technologies']:
        latex_source += " "+tech['technology']+","

    latex_source = latex_source[:-1]+".\n"

    latex_source += r"""
    \subsection{Main options}

    The main options selected are as follows:
    \begin{itemize}""" + '\n'

    latex_source+=f"    \item We {'allow' if vals_num['schools_as_fiber_nodes'] else 'disallow'} schools connected with fiber to behave as fiber nodes.\n"
    latex_source+=f"    \item We {'allow' if vals_num['schools_as_fiber_nodes'] else 'disallow'} providing solar electricity to schools with no electricity."
    latex_source+=r"""
        \item We allow a maximum fiber connection length of \maxfiber{} Kms.
        \item We consider a minimum bandwidth per school of \minbandwidth{} Mbps.
        \item We consider opex costs of \opexyears{} years in the total cost calculations.
    \end{itemize}

    \subsection{School selection}
    """

    if len(schools_complete_table)==len(selected_schools):
        latex_source += r"We consider all \totalnumunconn{} unconnected schools in \country{}."+"\n"
    else:
        latex_source += r"We only consider a subset of \totalnumunconn{} unconnected schools within \country{}."+"\n"

    extra_sentence = r""" (where another  \numoverbudget{} schools could have
    been connected with additional budget). """

    latex_source += r"""

    \section{Cost estimation results overview}

    In this section, estimated costs of connecting schools will be shown based on the data inputs provided to the School Costing Tool. This includes an analysis of the initial CapEx investments required and an estimate of the operational costs of school connectivity.

    The cost estimation tool was executed in an area with \totalnumschools{}, \totalnumunconn{} of which are currently not connected. With the given scenario and options chosen we can connect \numtoconn{} schools""" + f"{extra_sentence if vals_num['num_schools_over_budget'] !='0' else '. '}"

    latex_source += r"""The total cost of connecting these schools is \totalcost{}M USD, \totalcapexcost{}M USD consisting of CapEx cost and \totalopexcost{}M USD consisting of OpEx over a period of \opexyears{} years. See the figure below:

    \begin{figure}[h]
    \centering
    \includegraphics[scale=0.3]{graph_0.png} % replace with your image path
    \caption{Project costs}
    \label{fig:snapshot}
    \end{figure} 

    \subsection{CapEx and OpEx}

    The following table summarizes the CapEx costs:

    % Sample Table
    \begin{table}[h]
    \centering
    \begin{tabular}{|c|c|c|c|}
        \hline
        \textbf{CapEx} & \textbf{Schools} & \textbf{Cost per school} USD & \textbf{Total cost} USD \\
        \hline
         \textbf{Fiber}  & \fiberschools{} & \fibercapexps{} & \fibercapextot{} \\
          \textbf{Cellular}  & \cellschools{} & \cellcapexps{} & \cellcapextot{} \\
           \textbf{Microwave}  & \ptopschools{} & \ptopcapexps{} & \ptopcapextot{}  \\
            \textbf{Satellite}  & \satschools{} & \satcapexps{} & \satcapextot{}  \\
             \textbf{Electricity}  & \eleschools{} & \elecapexps{} & \elecapextot{}  \\
        \hline
    \end{tabular}
    \caption{CapEx Cost Model Overview}
    \label{tab:capex_overview}
    \end{table}

    The following table summarizes OpEx costs:

    \begin{table}[h]
    \centering
    \begin{tabular}{|c|c|c|c|}
        \hline
        \textbf{OpEx Cost} & \textbf{School/month USD} & \textbf{School/year USD} & \textbf{Total/year USD}  \\
        \hline
         \textbf{Fiber}  & \fiberopexpsm{} & \fiberopexpsy{} & \fiberopexyear{} \\
          \textbf{Cellular}  & \cellopexpsm{} & \cellopexpsy{} & \cellopexyear{} \\
           \textbf{Microwave}  & \ptopopexpsm{} & \ptopopexpsy{} & \ptopopexyear{} \\
            \textbf{Satellite}  & \satopexpsm{} & \satopexpsy{} & \satopexyear{} \\
             \textbf{Electricity}  & \eleopexpsm{} & \eleopexpsy{} & \eleopexyear{} \\
        \hline
    \end{tabular}
    \caption{OpEx Cost Model Overview}
    \label{tab:opex_overview}
    \end{table}

    \subsubsection{CapEx/OpEx progression}
    Now, let's dive deeper into the specifics of the costs.

    To connect all the unconnected \totalnumunconn{} schools in \country{} it is estimated to cost a total of \totalcost{}M USD. Over a period of \opexyears{} years, 
    electricity CapEx costs are expected to account for \eleperccapex{}$\%$ (\elecapextot{} USD) followed by capital expenditure (technology related) costs at \techcapextot{} USD (\techperccapex{}\%) 
    and operating expenditure costs for electricity at \eleopextot{} USD (\elepercopex{}\%) and for technology at \techopextot{} USD (\techpercopex{}\%) 

    In the first year, the CapEx cost for electricity accounts for an even larger share of total costs at \eleperccapexyearone{}\% (\elecapextot{} USD) 
    followed by technology Capex at \techperccapexyearone{}\% (\techcapextot{} USD), plus electricity OpEx at \elepercopexyearone{}\% (\eleopexyear{} USD) 
    and technology OpEx at \techpercopexyearone{}\% (\techopexyear{} USD). This is because, CapEx costs constitute a one-off, initial investment and are 
    expected to decrease as a percentage of total costs over time. Electricity capex costs are also assumed to be fixed and expected to decrease as a 
    percentage of total costs over time. Conversely, OpEx costs are expected to increase as a percentage of total costs over time.  
    \newline

    \begin{table}[h]
    \centering
    \begin{tabular}{|c|c|c|c|c|}
    \hline
    \multicolumn{1}{|c|}{\textbf{Cost type}} & \multicolumn{2}{c|}{\textbf{1 year}} & \multicolumn{2}{c|}{\textbf{\opexyears{} years}} \\
    \cline{2-5}
     & \textbf{USD} & \textbf{\%} & \textbf{USD} & \textbf{\%} \\
    \hline
    \textbf{Tech CapEx} & \techcapextot{} & \techperccapexyearone{} & \techcapextot{} & \techperccapex{} \\
    \hline
    \textbf{Electricity CapEx} & \elecapextot{} & \eleperccapexyearone{} & \elecapextot{} & \eleperccapex{} \\
    \hline
    \textbf{Tech OpEx} & \techopexyear{} & \techpercopexyearone{} & \techopextot{} & \techpercopex{} \\
    \hline
    \textbf{Electricity OpEx} & \eleopexyear{} & \elepercopexyearone{} & \eleopextot{} & \elepercopex{} \\
    \hline
    \end{tabular}
    \caption{CapEx/OpEx percentage progression}
    \label{tab:capex_opex_progression}
    \end{table}

    \subsubsection{Technology cost breakdown}
    Each technology has different associated CapEx and OpEx unit costs (see appendix). Based on the technology distribution to connect the unconnected schools, it is estimated that the total fiber cost will be of \fibercosttot{} USD, accounting for \fiberpercoftech{}\% of the total technology cost (\techcosttot{} USD). Cellular is expected to account for \cellpercoftech{}\%, Microwave \ptoppercoftech{}\% and Satellite \satpercoftech{}\%. 
    In contrast, electricity (both CapEx and OpEx) consists of a total cost of \elecosttot{} USD.

    The following bar chart shows the cost break down of the different technologies (plus electricity):
    \begin{figure}[h]
    \centering
    \includegraphics[scale=0.3]{graph_1.png} % replace with your image path
    \caption{Technology cost breakdown}
    \label{fig:snapshot}
    \end{figure} 


    \subsection{School/Student costs}

    The average cost to connect an unconnected school in the first year is estimated to be \avgcostschoolyearone{} USD. Over a period of five years the cost is estimated to be \avgschoolcost{} USD. 

    The cost per student in the first year is expected to be \avgcoststudentyearone{} USD. Over a period of five years the cost to connect a student is estimated to be \avgstudentcost{} USD.

    The following figures show the schools colored by school cost and student cost, respectively:

    \begin{figure}[ht]
    \centering

    \begin{subfigure}{0.45\textwidth}
        \centering
        \includegraphics[width=\linewidth]{graph_2.png}
        \caption{School cost}
        \label{fig:figure1}
    \end{subfigure}
    \hfill
    \begin{subfigure}{0.45\textwidth}
        \centering
        \includegraphics[width=\linewidth]{graph_3.png}
        \caption{Student cost}
        \label{fig:figure2}
    \end{subfigure}

    \caption{School/Student costs map}
    \label{fig:both_figures}
    \end{figure}

    \subsection{Technology breakdown}

    Based on the chosen scenario and options, the algorithm of the Costing Tool, yields the following technology breakdown: \fiberpercschools{}\% are connected with fiber, \cellpercschools{}\% are connected with cellular, \ptoppercschools{}\% are connected with microwave and \satpercschools{}\% are connected with satellite. The following pie chart shows the technology breakdown both in terms of percentages and total school numbers:

    \begin{figure}[h]
    \centering
    \includegraphics[scale=0.4]{graph_4.png} % replace with your image path
    \caption{School technology breakdown}
    \label{fig:snapshot}
    \end{figure} 

    It is worth seeing the school technology distribution in the following map:

    \begin{figure}[h]
    \centering
    \includegraphics[scale=0.4]{graph_5.png} % replace with your image path
    \caption{School technology breakdown map}
    \label{fig:snapshot}
    \end{figure} 

    \subsubsection{Fiber "economies of scale"}

    Finally, it is important to show the predicted fiber connections between schools or between a school and a fiber node as it the core of the capex cost of fiber connectivity. These fiber connections should constitute the lowest number 
    of kilometres possible so that the fiber CapEx cost remains as low as possible. In the following map we show all \fiberkms{} kilometer(s) of fiber runs for the chosen scenario:

    \begin{figure}[h]
    \centering
    \includegraphics[scale=0.3]{graph_6.png} % replace with your image path
    \caption{Fiber routes}
    \label{fig:snapshot}
    \end{figure} 

    \end{document}

    """


    # Add the LaTeX source to the document
    doc.append(NoEscape(latex_source))

    return doc

def generate_infra_report(country,schools_complete_table,schools_unconnected,schools_connected,data_space):
    # Create a LaTeX document object
    geometry_options = {"tmargin":"3cm","lmargin":"3cm","margin":"3cm"}
    doc = Document(geometry_options= geometry_options,documentclass='report',document_options=['12pt', 'a4paper'])

    doc.preamble.append(Command(NoEscape(r'usepackage[utf8]{inputenc}')))
    doc.preamble.append(Command(NoEscape(r'usepackage[T1]{fontenc}')))
    doc.preamble.append(Command(NoEscape(r'usepackage{graphicx}')))
    
    #report "variables"
    vals = get_report_variables(schools_complete_table,schools_unconnected,schools_connected,data_space)
    str1 = r"newcommand{{\country}}{{{}}}".format(country)
    doc.preamble.append(Command(NoEscape(str1)))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\totalnumschools}}{{${}$}}'.format(vals['num_schools']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\totalnumstudents}}{{${}$}}'.format(vals['num_students']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\totalnumfnodes}}{{${}$}}'.format(vals['num_fnodes']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\totalnumcells}}{{${}$}}'.format(vals['num_cells']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\percconnknown}}{{${}$}}'.format(vals['per_conn_known']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\percconnunknown}}{{${}$}}'.format(vals['per_conn_unknown']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\percconntypeknown}}{{${}$}}'.format(vals['per_conn_type_known']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\percconntypeunknown}}{{${}$}}'.format(vals['per_conn_type_unknown']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\perceleknown}}{{${}$}}'.format(vals['per_ele_known']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\perceleunknown}}{{${}$}}'.format(vals['per_ele_unknown']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\totalnumconn}}{{${}$}}'.format(vals['num_conn']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\totalnumunconn}}{{${}$}}'.format(vals['num_unconn']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\percconn}}{{${}$}}'.format(vals['perc_conn']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\percunconn}}{{${}$}}'.format(vals['perc_unconn']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\avgfnodedist}}{{${}$}}'.format(vals['avg_fnode_dist']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\percschoolsfnode}}{{${}$}}'.format(vals['perc_fnode_dist']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\avgcelldist}}{{${}$}}'.format(vals['avg_cell_dist']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\percschoolscell}}{{${}$}}'.format(vals['perc_cell_dist']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\avgptopdist}}{{${}$}}'.format(vals['avg_p2p_dist']))))
    doc.preamble.append(Command(NoEscape(r'newcommand{{\percschoolsptop}}{{${}$}}'.format(vals['perc_p2p_dist']))))
    #####

    latex_source = r"""
\begin{titlepage}
    \centering
    \includegraphics[scale=0.15]{giga_logo.png} % Add your logo or comment this line
    \vspace{1cm}
    
    {\huge\bfseries \country{} - School Connectivity Project Planning Report\par}
    \vspace{1cm}
    {\Large Finance Team, Giga\par}
    \vfill
    {\large \today\par}
\end{titlepage}

% Table of Contents
\tableofcontents
\newpage

\chapter*{Foreword}
\addcontentsline{toc}{chapter}{Foreword}
This report is intended for government officials who have used Giga’s Cost Model Tool for estimating the costs of a connectivity project (i.e., connecting a certain number of schools) or conducted a project with Giga using this tool.   The report serves to provide an overview of the tool, its estimates and limitations, and the potential costs of connecting all schools in the country.  

The purpose of this report is to summarize cost estimates for a school connectivity project and to describe the supporting methodology that Giga’s Cost Model uses to arrive at such estimates, including the model’s limitations and generalizations.  This report is intended to provide basic project information to key stakeholders to support preliminary project scoping and financial planning.  Note that actual project costs are a market function and can only be secured through outreach (e.g., RFI, RFP, etc.) to market participants.

\chapter{Infrastructure Report}

% Section 1
\section{Introduction}
The Government of \country{} recognizes the importance of digitalization and connectivity to enabling access to quality education as an essential component for achieving its national development goals. As part of its efforts to promote education and technology, the government has partnered with the Giga initiative to connect all schools to the internet. 

Giga is a global initiative launched in 2019 by UNICEF and the International Telecommunication Union (ITU) that aims to connect every school to the internet by 2030. The initiative is currently active in more than 50 countries worldwide and is supported by a coalition of public and private partners, including governments, technology companies, and civil society organizations. 

In \country{}, Giga is working with the government to connect schools across the country to the internet. The initiative's goal is to provide reliable and affordable internet access to all schools, teachers, and students in Rwanda enabling them to access educational resources and participate in the digital economy fully. Giga will support Rwanda in leveraging existing infrastructure, exploring possible technologies, and supporting the mobilization of financial resources to implement connectivity projects. 

\newpage

% Section 2
\section{Data Assessment}

Before analyzing the current state of the infrastructure as it relates to school connectivity, it is important to study the quality of the data available to Giga. Broadly, the data at Giga's disposal to produce this report can be summarized as follows:

\begin{itemize}
\item A total of \totalnumschools{} schools.
\item For a total of \totalnumstudents{} students.
\item \totalnumfnodes{} fiber nodes.
\item \totalnumcells{} cell towers.
\end{itemize}

We also need to make sure of what is the level of completeness of the data at hand, particularly with the most relevant attributes of the schools, that are connectivity (access and type) and access to electricity. In general, when any of these "Yes" or "No" attributes is unknown, we consider it the same as a "No".
\\

% Sample Table
\begin{table}[h]
    \centering
    \begin{tabular}{|c|c|c|}
        \hline
         & \textbf{Known} & \textbf{Unknown} \\
        \hline
        \textbf{Connectivity} & \percconnknown{} \% & \percconnunknown{} \% \\
        \textbf{Connectivity type} & \percconntypeknown{} \% & \percconntypeunknown{} \% \\
        \textbf{Electricity} & \perceleknown{} \% & \perceleunknown{} \% \\
        \hline
    \end{tabular}
    \caption{Status of connectivity and electricity data}
    \label{tab:data_status}
\end{table}

\newpage
% Section 3
\section{Current Connectivity Status}
There are \totalnumschools{} schools in \country{} of which currently \totalnumconn{} or \percconn{}\% are connected to the internet. Almost \percunconn{}\% or a total of \totalnumunconn{} schools remain unconnected to the internet. Se below a snapshot of the connectivity status of the schools in \country{}:


\begin{figure}[h]
    \centering
    \includegraphics[scale=0.4]{graph_0.png} % replace with your image path
    \caption{School connectivity status}
    \label{fig:snapshot}
\end{figure} 

Moreover, the technology breakdown of the \totalnumconn{} already connected schools is depicted in the following chart:
\\

\begin{figure}[h]
    \centering
    \includegraphics[scale=0.4]{graph_1.png} % replace with your image path
    \caption{Percentage of schools connected by type of technology}
    \label{fig:snapshot}
\end{figure}

\newpage

% section 4
\section{Infrastructure Availability}

In this section we will review the current state of the infrastructure in \country{}: where the relevant infrastructure is located with respect to the schools and their distances.

\subsection{Fiber}

As we have already mentioned, there are \totalnumfnodes{} fiber nodes in \country{}. The average distance from school to fiber node is \avgfnodedist{} kms. The map below shows all unconnected schools colored according to their distance to the closest fiber node:

\begin{figure}[h]
    \centering
    \includegraphics[scale=0.35]{graph_2.png} % replace with your image path
    \caption{Proximity to fiber nodes}
    \label{fig:fnode_dists}
\end{figure}

The following graph shows the cumulative distribution of school to fiber node distances. Note that \percschoolsfnode{} \% of schools are within $10$ kms of a fiber node:

\begin{figure}[h]
    \centering
    \includegraphics[scale=0.3]{graph_3.png} % replace with your image path
    \caption{Fiber node cumulative distribution}
    \label{fig:fnode_cumul_distr}
\end{figure}

\subsection{Cellular}

As we have already mentioned, there are \totalnumcells{} cell towers in \country{}. The average distance from school to a cell tower is \avgcelldist{} kms. The map below shows all unconnected schools colored according to their distance to the closest cell tower:

\begin{figure}[h]
    \centering
    \includegraphics[scale=0.4]{graph_4.png} % replace with your image path
    \caption{Proximity to cell towers}
    \label{fig:cell_dists}
\end{figure}

The following graph shows the cumulative distribution of school to cell tower distances. Note that \percschoolscell{} \% of schools are within $3$ kms of a cell tower:
\\
\begin{figure}[h]
    \centering
    \includegraphics[scale=0.4]{graph_5.png} % replace with your image path
    \caption{Cell tower cumulative distribution}
    \label{fig:cell_cumul_distr}
\end{figure}
\newpage
It is also worth exploring the distribution of cellular coverage at the schools by type of cellular technology:

\begin{figure}[h]
    \centering
    \includegraphics[scale=0.5]{graph_6.png} % replace with your image path
    \caption{Cellular coverage}
    \label{fig:cell_coverage}
\end{figure}

\newpage
\subsection{Microwave}
In order to establish a Microwave Peer-to-peer (P2P) connection, there needs to be line of sight between the school and a cell tower. The average distance from school to a visible cell tower is \avgptopdist{} kms. The map below shows all unconnected schools colored according to their distance to the closest visible cell tower:

\begin{figure}[h]
    \centering
    \includegraphics[scale=0.4]{graph_7.png} % replace with your image path
    \caption{Proximity to visible cell towers}
    \label{fig:p2p_dists}
\end{figure}

The following graph shows the cumulative distribution of school to visible cell tower distances. Note that \percschoolsptop{} \% of schools are within $3$ kms of a cell tower:
\\
\begin{figure}[h]
    \centering
    \includegraphics[scale=0.35]{graph_8.png} % replace with your image path
    \caption{Visible cell tower cumulative distribution}
    \label{fig:ptop_cumul_distr}
\end{figure}

"""

    # Add the LaTeX source to the document
    doc.append(NoEscape(latex_source))

    return doc
