
def infra_report(vals, section_level = -1):

    report_text = f"""
    \\{'chapter' if section_level == -1 else 'section'}{'{Infrastructure Report}' if not vals['_selected_schools'] else '{Infrastructure Report for Selected Schools}'}
    """

    if not vals['_selected_schools']:
        report_text += data_assesment_section(vals, section_level+1)
    
    report_text += current_connectivity_status_section(vals, section_level+1)
    report_text += infrastructure_availability_section(vals, section_level+1)

    return report_text


def data_assesment_section(vals, section_level):

    return f"""
    \\{'sub'*section_level}section{{Data Assesment}}"

    Before analyzing the current state of the infrastructure as it relates to school connectivity, it is important to study the quality of the data available to Giga. Broadly, the data at Giga's disposal to produce this report can be summarized as follows:

    \\begin{{itemize}}
        \\item A total of {vals['num_schools']} schools.
        \\item For a total of {vals['num_students']} students.
        \\item {vals['num_fnodes']} fiber nodes.
        \\item {vals['num_cells']} cell towers.
    \\end{{itemize}}

    We also need to make sure of what is the level of completeness of the data at hand, particularly with the most relevant attributes of the schools, that are connectivity (access and type) and access to electricity. In general, when any of these "Yes" or "No" attributes is unknown, we consider it the same as a "No".
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

    image_suffix = ('_selected' if vals['_selected_schools'] else '')

    return f"""
    \\{'sub'*section_level}section{{Current Connectivity Status}}

    There are {vals['num_schools']} schools in {'in the selected region of ' if vals['_selected_schools'] else ''}{vals['country_name']} of which currently {vals['num_conn']} ({vals['perc_conn']}\%) are connected to the internet. {vals['num_unconn']} schools, which accounts for {vals['perc_unconn']}\%, remain unconnected to the internet. See below a snapshot of the connectivity status of the schools in {vals['country_name']}:

    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.4]{{{'static_data_map' + image_suffix + '.png'}}}
        \\caption{{School connectivity status}}
        \\label{{fig:snapshot}}
    \\end{{figure}}

    Moreover, the technology breakdown of the {vals['num_conn']} already connected schools is depicted in the following chart:
    \\\\

    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.4]{{{'schools_conn_pie' + image_suffix + '.png'}}}
        \\caption{{Percentage of schools connected by type of technologies}}
        \\label{{fig:snapshot}}
    \\end{{figure}}

    \\newpage
    """

def infrastructure_availability_section(vals, section_level):

    section_text =  f"""
    \\{'sub'*section_level}section{{Infrastructure Availability}}

    In this section, we'll examine the existing condition of infrastructure in {vals['country_name']}, focusing on its proximity to schools and the distances involved.
    """

    if int(vals['num_fnodes']) > 0:
        section_text += fiber_section(vals, section_level=section_level+1)
    
    section_text += cellular_section(vals, section_level=section_level+1)
    section_text += microwave_section(vals, section_level=section_level+1)

    return section_text


def fiber_section(vals, section_level):
    image_suffix = ('_selected' if vals['_selected_schools'] else '')

    return f"""
    \\{'sub'*section_level}section{{Fiber}}

    As we have already mentioned, there are {vals['num_fnodes']} fiber nodes in {vals['country_name']}. The average distance from school to fiber node is {vals['avg_fnode_dist']} kms. The map below shows all unconnected schools colored according to their distance to the closest fiber node:

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
    """

def cellular_section(vals, section_level):
    image_suffix = ('_selected' if vals['_selected_schools'] else '')

    return f"""
    \\{'sub'*section_level}section{{Cellular}}

    As we have already mentioned, there are {vals['num_cells']} cell towers in {vals['country_name']}. The average distance from school to a cell tower is {vals['avg_cell_dist']} kms. The map below shows all unconnected schools colored according to their distance to the closest cell tower:

    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.4]{{{'cell_dist_map' + image_suffix + '.png'}}}
        \\caption{{Proximity to cell towers}}
        \\label{{fig:cell_dists}}
    \\end{{figure}}

    The following graph shows the cumulative distribution of school to cell tower distances. Note that {vals['perc_cell_dist']} \% of schools are within $3$ kms of a cell tower:
    \\\\
    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.4]{{{'cum_cell_dist' + image_suffix + '.png'}}}
        \\caption{{Cell tower cumulative distribution}}
        \\label{{fig:cell_cumul_distr}}
    \\end{{figure}}
    \\newpage
    It is also worth exploring the distribution of cellular coverage at the schools by type of cellular technology:

    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.5]{{{'cell_coverage_map' + image_suffix + '.png'}}}
        \\caption{{Cellular coverage}}
        \\label{{fig:cell_coverage}}
    \\end{{figure}}

    The following graph shows the cumulative distribution of mobile coverage at school locations:

    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.3]{{{'cum_distribution_coverage' + image_suffix + '.png'}}}
        \\caption{{Cellular coverage}}
        \\label{{fig:coverage_cumul_distr}}
    \\end{{figure}}

    """

def microwave_section(vals, section_level):
    image_suffix = ('_selected' if vals['_selected_schools'] else '')

    return f"""
    \\{'sub'*section_level}section{{Microwave}}

    In order to establish a Microwave Peer-to-peer (P2P) connection, there needs to be line of sight between the school and a cell tower. The average distance from school to a visible cell tower is {vals['avg_p2p_dist']} kms. The map below shows all unconnected schools colored according to their distance to the closest visible cell tower:

    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.4]{{{'p2p_dist_map' + image_suffix + '.png'}}}
        \\caption{{Proximity to visible cell towers}}
        \\label{{fig:p2p_dists}}
    \\end{{figure}}

    The following graph shows the cumulative distribution of school to visible cell tower distances. Note that {vals['perc_p2p_dist']} \% of schools are within $3$ kms of a cell tower:
    \\\\
    \\begin{{figure}}[h]
        \\centering
        \\includegraphics[scale=0.35]{{{'cum_visible_cell_dist' + image_suffix + '.png'}}}
        \\caption{{Visible cell tower cumulative distribution}}
        \\label{{fig:ptop_cumul_distr}}
    \\end{{figure}}
    """