def appendix():

    return r"""
    \clearpage

    \chapter*{Appendix}
    \addcontentsline{toc}{chapter}{Appendix}
    
    \begin{figure}[h]
        \centering
        \includegraphics[scale=0.4]{unit_cost_barplot.png}
        \caption{Unit technology costs}
        \label{fig:unitcost}
    \end{figure}

    \end{document}
    """