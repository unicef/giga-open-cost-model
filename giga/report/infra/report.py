from giga.report.infra.title_toc import title_and_toc
from giga.report.infra.disclaimer import disclaimer
from giga.report.infra.chapter_introduction import introduction
from giga.report.infra.chapter_infra_report import infra_report

def get_report_text(vals):
    
    latex_source = title_and_toc(vals)
    latex_source += disclaimer()
    latex_source += introduction(vals)
    latex_source += infra_report(vals)
    
    return latex_source