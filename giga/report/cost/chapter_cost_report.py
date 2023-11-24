from math import inf
from giga.report.infra.chapter_infra_report import infra_report

def cost_report(vals):
    chapter_text = f"""
    \\chapter{{Cost Model Report}}
    """

    chapter_text += section_scenario(vals)
    chapter_text += section_cost_estimation(vals)

    return chapter_text

def cost_report_for_merged(vals, vals_infra):

    chapter_text = f"""
    \\chapter{{Cost Model Report}}
    """

    chapter_text += section_scenario(vals)
    if vals['num_all_unconn_schools'] != vals_infra['num_unconn']:
        chapter_text += infra_report(vals = vals_infra, section_level=0)
    chapter_text += section_cost_estimation(vals)

    return chapter_text


def section_scenario(vals):
    section_text = r"""
    \section{Scenario and options}

    In this section we describe the scenario and most relevant options selected in order to yield the cost estimates that will follow in the next sections.

    \subsection{Scenario Description}
    """

    if "priority_cost" == vals['scenario_id']:
        section_text += r"""
        The scenario chosen is that of \textbf{Priorities}, i.e., we connect schools with a certain technology priority: fiber, cellular, microwave and satellite.
        """
    elif "minimum_cost" in vals['scenario_id']:
        section_text += r"""
        The scenario chosen is that of \textbf{Lowest Cost}, i.e., minimize the total cost of connecting all schools to the internet.
        """
    
    section_text += f"""The scenario ran {('without any budget constraints.' if vals['budget_cstr'] == inf else f'with a budget of {vals["budget_cstr"]} USD.')}
    """

    section_text += f"""
    \\subsection{{Technologies used}}
    
    For this cost model estimation, we allowed the use of the following technologies: {', '.join(vals['input_technologies'])}.

    \\subsection{{Main options}}

    The main options selected are as follows:
    \\begin{{itemize}}
        \\item We {'allow' if vals['schools_as_fiber_nodes'] else 'disallow'} schools connected with fiber to behave as fiber nodes.
        \\item We {'allow' if vals['schools_as_fiber_nodes'] else 'disallow'} providing solar electricity to schools with no electricity.
        \\item We allow a maximum fiber connection length of {vals['max_fiber_conn']} Kms.
        \\item We consider a minimum bandwidth per school of {vals['min_bandwidth']} Mbps.
        \\item We consider opex costs of {vals['opex_years']} years in the total cost calculations.
    \\end{{itemize}}

    \\subsection{{School selection}}
    """

    if vals['num_all_schools']==vals['num_schools']:
        section_text += r"""
        We consider all \totalnumunconn{} unconnected schools in \country{}.
        """
    else:
        section_text += r"""
        We only consider a subset of \totalnumunconn{} unconnected schools within \country{}.
        """

    return section_text


def section_cost_estimation(vals):

    additional_text = ' (where another  \\numoverbudget{{}} schools could have been connected with additional budget).' if vals['num_schools_over_budget'] !='0' else '. '
    
    section_text = f"""
    \\section{{Estimated School Connectivity Costs}}

    In this section, estimated costs of connecting schools will be shown based on the data inputs provided to the School Costing Tool. This includes an analysis of the initial CapEx investments required and an estimate of the operational costs of school connectivity.

    The cost estimation tool was executed in an area with \\totalnumschools{{}}, \\totalnumunconn{{}} of which are currently not connected. With the given scenario and options chosen we can connect \\numtoconn{{}} schools{additional_text}
    """

    section_text += r"""
    \subsection{Total Project Costs Estimate}
    The total cost of connecting these schools is \totalcost{}M USD, \totalcapexcost{}M USD consisting of CapEx cost and \totalopexcost{}M USD consisting of OpEx over a period of \opexyears{} years. See the figure below:

    \begin{figure}[h]
        \centering
        \includegraphics[scale=0.3]{project_cost_barplot.png}
        \caption{Project costs}
        \label{fig:snapshot}
    \end{figure}
    \newpage
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

    \newpage
    \subsubsection{Cost Estimates by Technology}
    Each technology has different associated CapEx and OpEx unit costs (see appendix). Based on the technology distribution to connect the unconnected schools, it is estimated that the total fiber cost will be of \fibercosttot{} USD, accounting for \fiberpercoftech{}\% of the total technology cost (\techcosttot{} USD). Cellular is expected to account for \cellpercoftech{}\%, Microwave \ptoppercoftech{}\% and Satellite \satpercoftech{}\%. 
    In contrast, electricity (both CapEx and OpEx) consists of a total cost of \elecosttot{} USD.

    The following bar chart shows the cost break down of the different technologies (plus electricity):
    \begin{figure}[h]
    \centering
    \includegraphics[scale=0.3]{average_cost_barplot.png} % replace with your image path
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
        \includegraphics[width=\linewidth]{per_school_cost_map.png}
        \caption{School cost}
        \label{fig:figure1}
    \end{subfigure}
    \hfill
    \begin{subfigure}{0.45\textwidth}
        \centering
        \includegraphics[width=\linewidth]{per_student_cost_map.png}
        \caption{Student cost}
        \label{fig:figure2}
    \end{subfigure}

    \caption{School/Student costs map}
    \label{fig:both_figures}
    \end{figure}

    Based on the chosen scenario and options, the algorithm of the Costing Tool, yields the following technology breakdown: \fiberpercschools{}\% are connected with fiber, \cellpercschools{}\% are connected with cellular, \ptoppercschools{}\% are connected with microwave and \satpercschools{}\% are connected with satellite. The following pie chart shows the technology breakdown both in terms of percentages and total school numbers:

    \begin{figure}[h]
    \centering
    \includegraphics[scale=0.4]{technology_pie.png} % replace with your image path
    \caption{School technology breakdown}
    \label{fig:snapshot}
    \end{figure} 

    It is worth seeing the school technology distribution in the following map:

    \begin{figure}[h]
    \centering
    \includegraphics[scale=0.4]{technology_map.png} % replace with your image path
    \caption{School technology breakdown map}
    \label{fig:snapshot}
    \end{figure} 

    \newpage
    
    \subsubsection{Fiber \& P2P "economies of scale"}

    Finally, it is important to show the predicted fiber \& P2P connections between schools or between a school and a fiber node or visible cell tower as it the core of the capex cost of fiber \& P2P connectivity. For fiber, connections should constitute the lowest number 
    of kilometres possible so that the fiber CapEx cost remains as low as possible. In the following map we show all \fiberkms{} kilometer(s) of fiber runs and P2P connections for the chosen scenario:

    \begin{figure}[h]
    \centering
    \includegraphics[scale=0.3]{infra_lines_map.png} % replace with your image path
    \caption{Fiber and P2P routes}
    \label{fig:snapshot}
    \end{figure}
    """

    return section_text
    