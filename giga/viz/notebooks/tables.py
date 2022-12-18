from ipywidgets import interactive, IntRangeSlider, Layout
from IPython.display import display


def apply_highlight(s, coldict):
    if s.name in coldict.keys():
        return ["background-color: {}".format(coldict[s.name])] * len(s)
    return [""] * len(s)


def interactive_cost_inspector_stats(
    df, columns_to_highlight=["capex", "opex", "total_cost"]
):
    coldict = {c: "#f2d591" for c in columns_to_highlight}

    def render(capex, opex, total_cost):
        filt = df[df["capex"].between(capex[0], capex[1])]
        filt = filt[filt["opex"].between(opex[0], opex[1])]
        filt = filt[filt["total_cost"].between(total_cost[0], total_cost[1])]
        if len(filt) > 0:
            display(filt.style.apply(apply_highlight, coldict=coldict))
        else:
            display(filt)

    capex_slider = IntRangeSlider(
        value=[0, 200_000],
        min=0,
        max=200_000,
        step=2_000,
        description="Capex:",
        layout=Layout(width="500px"),
    )
    opex_slider = IntRangeSlider(
        value=[0, 10_000],
        min=0,
        max=10_000,
        step=1_000,
        description="Opex:",
        layout=Layout(width="500px"),
    )

    total_cost_slider = IntRangeSlider(
        value=[0, 200_000],
        min=0,
        max=200_000,
        step=2_000,
        description="Total Cost:",
        layout=Layout(width="500px"),
    )

    interactive_plot = interactive(
        render, capex=capex_slider, opex=opex_slider, total_cost=total_cost_slider
    )

    for c in interactive_plot.children:
        c.style = {"description_width": "initial"}
    return interactive_plot
