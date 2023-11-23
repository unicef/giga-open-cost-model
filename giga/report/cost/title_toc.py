def title_and_toc(vals):

    if 'acks_logo' in vals:
        acks_logo_text = '''
            \\vspace{{1cm}}
            \\includegraphics[scale=0.15]{{title_acks_logo.png}}'''
    else:
        acks_logo_text = ''

    return f"""
    \\begin{{titlepage}}
        \\centering
        \\includegraphics[scale=0.15]{{giga_logo.png}} % Add your logo or comment this line
        \\vspace{{1cm}}
        
        {{\huge\\bfseries {vals['country_name']} - School Connectivity Project Planning Report\par}}
        \\vspace{{1cm}}
        {{\Large Finance Team, Giga\par}}
        \\vspace{{3cm}}
        \\textit{{{vals['acks_text']}}}{acks_logo_text}
        \\vfill
        {{\large \\today\par}}
    \\end{{titlepage}}

    % Table of Contents
    \\tableofcontents
    \\newpage
    """