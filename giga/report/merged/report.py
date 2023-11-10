from giga.report.merged.title_toc import title_and_toc
from giga.report.cost.foreword import foreword
from giga.report.cost.chapter_introduction import introduction
from giga.report.infra.chapter_infra_report import infra_report
from giga.report.cost.chapter_cost_report import cost_report_for_merged

def get_report_text(infra_vals, infra_selected_vals, cost_vals):

    latex_source = title_and_toc()
    latex_source += foreword()
    latex_source += introduction()
    latex_source += infra_report(vals = infra_vals, section_level=-1)
    latex_source += cost_report_for_merged(vals=cost_vals, vals_infra=infra_selected_vals)

    return latex_source