from giga.utils.globals import ACKS_LOGO_FILE, TITLE_LOGO_FILE
def title_and_toc(vals):

    if 'title_logo' in vals:
        title_logo_text = f'''
            \\includegraphics[scale=0.15]{{{TITLE_LOGO_FILE}}}'''
    else:
        title_logo_text = ''

    if 'acks_logo' in vals:
        acks_logo_text = f'''
            \\includegraphics[scale=0.15]{{{ACKS_LOGO_FILE}}}'''
    else:
        acks_logo_text = ''

    return f"""
    \\begin{{titlepage}}
        \\centering{title_logo_text}
        \\vspace{{1cm}}
        
        {{\huge\\bfseries Giga School Connectivity Cost Report - {vals['country_name']}\par}}
        \\vspace{{1cm}}
        {{\Large Finance Team, Giga\par}}
        \\vspace{{3cm}}
        \\textit{{{vals['acks_text']}}}
        \\vspace{{1cm}}
        {acks_logo_text}
        \\vfill
        {{\large \\today\par}}
    \\end{{titlepage}}

    % Table of Contents
    \\tableofcontents
    \\newpage
    """