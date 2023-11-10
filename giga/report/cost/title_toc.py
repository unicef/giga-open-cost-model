def title_and_toc():
    return r"""
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
    """