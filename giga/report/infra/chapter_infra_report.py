
import math

def infra_report(vals, section_level = -1):
    global image_suffix

    image_suffix = ('_selected' if vals['_selected_schools'] else '')

    report_text = f"""
    \\{'chapter' if section_level == -1 else 'section'}{'{Infrastructure Report}' if not vals['_selected_schools'] else '{Infrastructure Report for Selected Schools}'}
    """

    if not vals['_selected_schools']:
        report_text += data_assesment_section(vals, section_level+1)
    
    report_text += current_connectivity_status_section(vals, section_level+1)
    report_text += electricity_availability_section(vals, section_level+2)
    report_text += infrastructure_availability_section(vals, section_level+1)

    return report_text


def data_assesment_section(vals, section_level):

    num_fnodes = int(vals['num_fnodes'].replace(',', ''))
    num_cells = int(vals['num_cells'].replace(',', ''))

    fiber_node_text = vals['num_fnodes'] if num_fnodes>0 else 'No data'
    cell_text = vals['num_cells'] if num_cells>0 else 'No data'

    return f"""
    \\{'sub'*section_level}section{{Data Assesment \& Data Quality}}"

    The School Connectivity Cost Model has based its estimates, in part, on the existing, available infrastructure. Before analyzing the current state of the infrastructure 
    as it relates to school connectivity, it is important to also note the quality of data available to Giga. Broadly, the data at Giga's disposal to produce the cost estimates 
    is summarized in following data records:

    \\begin{{itemize}}
        \\item Number of schools: {vals['num_schools']} schools.
        \\item Number of students: {vals['num_students']} students.
        \\item Fiber node data: {fiber_node_text}
        \\item Cell tower data: {cell_text}
    \\end{{itemize}}

    The status of data completeness also needs to be considered, particularly for following attributes most relevant to schools, namely (1) data on the extent of connectivity;
    (2) the type of connectivity and (3) access to electricity. In general, when any of these "Yes" or "No" attributes is unknown, we consider it the same as a "No".
    \\\\

    % Sample Table
    \\begin{{table}}[h]
        \\centering
        \\begin{{tabular}}{{|c|c|c|}}
            \\hline
            & \\textbf{{Known}} & \\textbf{{Unknown}} \\\\
            \hline
            \\textbf{{Connectivity}} & {vals['perc_conn_known']} \% & {vals['perc_conn_unknown']} \% \\\\
            \\textbf{{Connectivity type}} & {vals['perc_conn_type_known']} \% & {vals['perc_conn_type_unknown']} \% \\\\
            \\textbf{{Electricity}} & {vals['perc_ele_known']} \% & {vals['perc_ele_unknown']} \% \\\\
            \\hline
        \\end{{tabular}}
        \\caption{{Status of connectivity and electricity data}}
        \\label{{tab:data_status}}
    \\end{{table}}

    \\newpage
    """

def current_connectivity_status_section(vals, section_level):

    return f"""
    \\{'sub'*section_level}section{{Current School Connectivity Status}}

    \\{'sub'*(section_level+1)}section{{Number of Unconnected Schools}}

    There are {vals['num_schools']} schools in {'in the selected region of ' if vals['_selected_schools'] else ''}{vals['country_name']} of which currently {vals['num_conn']} 
    ({vals['perc_conn']}\%) are connected to the internet. {vals['num_unconn']} schools, which accounts for {vals['perc_unconn']}\%, remain unconnected to the internet. 
    Below is a geographical representation of the connectivity status of schools in {vals['country_name']}:

    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.4]{{{'static_data_map' + image_suffix + '.png'}}}
        \\caption{{School connectivity status}}
        \\label{{fig:snapshot}}
    \\end{{figure}}

    \\{'sub'*(section_level+1)}section{{Technology Distribution Across Connected Schools}}

    The technology breakdown of the {vals['num_conn']} already connected schools is depicted in the following chart:
    \\\\

    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.4]{{{'schools_conn_pie' + image_suffix + '.png'}}}
        \\caption{{Percentage of schools connected by type of technologies}}
        \\label{{fig:snapshot}}
    \\end{{figure}}

    \\newpage
    """

def electricity_availability_section(vals, section_level):

    return f"""
    \\{'sub'*section_level}section{{Electricity Availability}}

    In terms of the availability of electricity, {vals['perc_has_ele']}\% ({vals['num_has_ele']}) of all schools ({vals['num_schools']}) {'in the selected region of ' if vals['_selected_schools'] else ''}{vals['country_name']} have access to electricity. 
    {vals['num_has_no_ele']} schools, which accounts for {vals['perc_has_no_ele']}\% do not have access to electricity. Below is a geographical representation of electricity 
    available at schools in {'the selected region of ' if vals['_selected_schools'] else ''}{vals['country_name']}:

    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.4]{{{'electricity_map' + image_suffix + '.png'}}}
        \\caption{{Electricity availability status}}
        \\label{{fig:electricity}}
    \\end{{figure}}

    \\newpage
    """

def infrastructure_availability_section(vals, section_level):

    section_text =  f"""
    \\{'sub'*section_level}section{{Infrastructure Availability}}

    In this section, we'll examine the existing condition of infrastructure in {vals['country_name']}, highlighting  infrastructure located in proximity to schools and detailing school distances to relevant infrastructure points.
    """

    num_fnodes = int(vals['num_fnodes'].replace(',', '')) #or distance to fiber node information.

    if num_fnodes > 0 or vals['avg_fnode_dist'] != math.inf:
        section_text += fiber_section(vals, section_level=section_level+1)
    
    num_cells = int(vals['num_cells'].replace(',', ''))

    if num_cells > 0 or vals['avg_cell_dist'] != math.inf:
        section_text += cellular_section(vals, section_level=section_level+1)
    
    if vals['avg_p2p_dist'] != math.inf:
        section_text += microwave_section(vals, section_level=section_level+1)

    return section_text


def fiber_section(vals, section_level):

    num_fnodes = int(vals['num_fnodes'].replace(',', ''))

    first_sentence = f"There are {vals['num_fnodes']} fiber nodes in {vals['country_name']}. " if num_fnodes > 0 else ""

    return f"""
    \\{'sub'*section_level}section{{Fiber}}

    {first_sentence}The average distance from school to fiber node is {vals['avg_fnode_dist']} kms. The map below shows all unconnected schools colored according to their distance to the closest fiber node:

    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.35]{{{'fiber_dist_map' + image_suffix + '.png'}}}
        \\caption{{Proximity to fiber nodes}}
        \\label{{fig:fnode_dists}}
    \\end{{figure}}

    The following graph shows the cumulative distribution of school to fiber node distances. Note that {vals['perc_fnode_dist']} \% of schools are within $10$ kms of a fiber node:

    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.3]{{{'cum_fiber_dist' + image_suffix + '.png'}}}
        \\caption{{Fiber node cumulative distribution}}
        \\label{{fig:fnode_cumul_distr}}
    \\end{{figure}}

    \\newpage
    """

def cellular_section(vals, section_level):

    num_cells = int(vals['num_cells'].replace(',', ''))
    
    first_sentence = f"There are {vals['num_cells']} cell towers in {vals['country_name']}. " if num_cells > 0 else ""

    return f"""
    \\{'sub'*section_level}section{{Cellular}}

    \\{'sub'*(section_level+1)}section{{Number of Unconnected Schools within 3 kms of a Cell Tower}}

    {first_sentence}The average distance from school to a cell tower is {vals['avg_cell_dist']} kms. The map below shows all unconnected schools colored according to their distance to the closest cell tower:

    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.4]{{{'cell_dist_map' + image_suffix + '.png'}}}
        \\caption{{Proximity to cell towers}}
        \\label{{fig:cell_dists}}
    \\end{{figure}}

    The following graph shows the cumulative distribution of schools accross distances to cell towers. {vals['perc_cell_dist']} \% of schools are within $3$ kms of a cell tower:
    \\\\
    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.4]{{{'cum_cell_dist' + image_suffix + '.png'}}}
        \\caption{{Cell tower cumulative distribution}}
        \\label{{fig:cell_cumul_distr}}
    \\end{{figure}}
    
    \\newpage
    
    \\{'sub'*(section_level+1)}section{{Number of Unconnected Schools by Coverage Area (3G, 4G and 5G)}}
    
    In terms of distribution of cellular technology coverage accross schools, {vals['perc_3g']}\% are covered by 3G and {vals['perc_4g']}\% by 4G.
    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.4]{{{'cell_coverage_map' + image_suffix + '.png'}}}
        \\caption{{Cellular coverage}}
        \\label{{fig:cell_coverage}}
    \\end{{figure}}

    The following graph shows the cumulative distribution of schools covered by cellular technology type:

    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.3]{{{'cum_distribution_coverage' + image_suffix + '.png'}}}
        \\caption{{Cellular coverage}}
        \\label{{fig:coverage_cumul_distr}}
    \\end{{figure}}

    \\newpage
    """

def microwave_section(vals, section_level):

    return f"""
    \\{'sub'*section_level}section{{Microwave}}

    \\{'sub'*(section_level+1)}section{{Number of Unconnected Schools within visibility range (P2P/microwave)}}

    To establish a Microwave Peer-to-peer (P2P) connection, there needs to be a line of sight between the school and a cell tower. The average distance from school to 
    a visible cell tower is {vals['avg_p2p_dist']} kms. The map below shows all unconnected schools colored according to their distance to the closest visible cell tower:

    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.4]{{{'p2p_dist_map' + image_suffix + '.png'}}}
        \\caption{{Proximity to visible cell towers}}
        \\label{{fig:p2p_dists}}
    \\end{{figure}}

    The following graph shows the cumulative distribution of schools to visible cell tower distances. {vals['perc_p2p_dist']}\% of schools are within $3$ kms of a cell tower:
    \\\\
    \\begin{{figure}}[h]
        \\centering 
        \\includegraphics[scale=0.35]{{{'cum_visible_cell_dist' + image_suffix + '.png'}}}
        \\caption{{Visible cell tower cumulative distribution}}
        \\label{{fig:ptop_cumul_distr}}
    \\end{{figure}}
    """