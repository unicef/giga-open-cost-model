from giga.report.cost.title_toc import title_and_toc
from giga.report.cost.foreword import foreword
from giga.report.cost.chapter_introduction import introduction
from giga.report.cost.chapter_cost_report import cost_report
from giga.report.cost.appendix import appendix

def get_report_text(vals):
    
    latex_source = title_and_toc(vals)
    latex_source += foreword()
    latex_source += introduction()
    latex_source += cost_report(vals= vals)
    latex_source += appendix()
    return latex_source