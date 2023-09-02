from pylatex import Document, Section, Subsection, Tabular, Command
from pylatex import Math, TikZ, Axis, Plot, Figure, Matrix, Alignat, SubFigure
from pylatex import PageStyle, Head, Foot, MiniPage, \
    StandAloneGraphic, MultiColumn, Tabu, LongTabu, LargeText, MediumText, \
    LineBreak, NewPage, Tabularx, TextColor, simple_page_number, Itemize, Enumerate, Hyperref, Package, \
    TikZ, TikZNode, TikZCoordinate, TikZOptions, NewLine, VerticalSpace
from pylatex.utils import italic, bold, NoEscape, escape_latex
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
