def title_and_toc(vals):
    return f"""
    \\begin{{titlepage}}
        \\centering
        \\includegraphics[scale=0.15]{{giga_logo.png}} % Add your logo or comment this line
        \\vspace{{1cm}}
        
        {{\huge\\bfseries {vals['country_name']} - School Connectivity Infrastructure Report\par}}
        \\vspace{{1cm}}
        {{\Large Finance Team, Giga\par}}
        \\vspace{{3cm}}
        \\textit{{{vals['acks_text']}}}
        \\vfill
        {{\large \\today\par}}
    \\end{{titlepage}}

    % Table of Contents
    \\tableofcontents
    \\newpage
    """