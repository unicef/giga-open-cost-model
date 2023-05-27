from IPython.display import display

from ipywidgets import HTML, VBox, Box

display(
    HTML(
        value="""<style>
    .giga-section {
        background-color: #f5f5f5; /* Giga Light Gray */
        margin: 5px 15px 15px 5px;
        padding: 15px;
        border: 2px solid #87c0ad;
        box-shadow: 1px 1px 3px #ccc;
        overflow: hidden;
        position: relative;
    }
    .giga-section.dark {
        background-color: #222222 !important; /* Giga Black */
        color: #f5f5f5 !important; /* Giga Light Gray */
        font-weight: bold;
    }
    .giga-section.dark .giga-section-contents * {
        color: #f5f5f5 !important; /* Giga Light Gray */
        font-weight: bold;
    }
    .giga-section.dark select {
        background-color: #474747; /* Giga Dark Gray */
    }
    .giga-section select {
        border-radius: 5px;
    }
    .giga-section .giga-section-title,
    .giga-section .giga-section-title * {
        font-weight: bold;
        font-size: 15pt;
        background-color: #cde3e1; /* Giga Light Pine */
        color: #474747; /* Giga Dark Gray */
    }
    .giga-section .giga-section-title {
        padding: 25px;
        display: block;
        margin: -25px -25px 0 -25px;
    }
    .giga-section .giga-section-contents {
        padding: 15px 8px 5px 8px;
    }
    .giga-section.center .giga-section-contents,
    .giga-section.run .giga-section-contents {
        margin: 0 auto;
    }
    .giga-section .giga-section {
        background-color: #cde3e1; /* Giga Light Pine */
        margin-bottom: 25px;
        border-color: #07706d; /* Giga Pine */
        border-radius: 15px;
    }
    .giga-section .giga-section .giga-section-title,
    .giga-section .giga-section .giga-section-title * {
        font-size: 14pt !important;
        background-color: #07706d; /* Giga Pine */
        color: #f5f5f5; /* Giga Light Gray */
    }
    .giga-section>.widget-html {
        margin: 0;
    }
    
    .giga-section.nopad .giga-section-contents .plotly.plot-container {
        margin: -70px;
    }

    /* .header / .footer: adds appropriate border rounding */
    .giga-section.header {
        border-radius: 25px 25px 0 0;
    }
    .giga-section.footer {
        border-radius: 0 0 25px 25px;
    }
    .giga-section.header .giga-section-title,
    .giga-section.header .giga-section-title *,
    .giga-section.run .giga-section-title,
    .giga-section.run .giga-section-title * {
        font-size: 20pt;
    }

    /* .run: blue and rounded */
    .giga-section.run {
        border-radius: 25px;
        margin-top: 50px;
        border-color: #b6c4cd;
    }
    .giga-section.run .giga-section-title,
    .giga-section.run .giga-section-title * {
        background-color: #d6e4fd; /* Giga Light Blue */
    }
    .giga-section.run .giga-section {
        background-color: #d6e4fd; /* Giga Light Blue */
        border-color: #1647a4;
    }
    .giga-section.run .giga-section .giga-section-title,
    .giga-section.run .giga-section .giga-section-title * {
        background-color: #1647a4; /* Giga Dark Blue */
    }

    /* Tables */
    .giga-section table {
        border: 1px solid #b6c4cd;
        border-radius: 5px;
        
    }
    .giga-section td, .giga-section th {
        padding: 3px;
    }
    .giga-section thead tr {
        text-align: left !important;
        background-color: #d0d0d0;
    }
    .giga-section tbody th {
        text-align: right !important;
    }
    .giga-section tbody tr:nth-child(even) {
        background-color: #d6e4fd; /* Giga Light Blue */
    }
    .giga-section tbody tr:nth-child(odd) {
        background-color: #f5f5f5; /* Giga Light Gray */
    }

    /*Model output*/
    .giga-section .jp-OutputArea-child pre {
        max-width, 1000px;
        overflow-y: scroll;
        display: block;
        margin: 10px;
        padding: 15px;
    }
    .giga-section .jp-RenderedText[data-mime-type='application/vnd.jupyter.stderr'] {
        background-color: #d6e4fd;
        border: 1px solid #b6c4cd;
        border-radius: 5px;
    }

    /*Mapbox panels*/
    .giga-section .plot-container {
        max-width: 900px;
    }
    .giga-section .mapboxgl-map {
        width: 100% !important;
        height: 100% !important;
        top: 0 !important;
        left: 0 !important;
        margin: -10px;
    }
    .giga-section .togg {
        width: 100% !important;
        height: 100% !important;
        top: 0 !important;
        left: 0 !important;
        margin: -10px;
    }

    /* .expander: clicking header toggles contents */
    .giga-section.expander:not(.active) {
        padding-bottom: 0;
    }
    .giga-section.expander .giga-section-title:not(.giga-section .giga-section *) {
        cursor: pointer;
    }
    .giga-section.expander .giga-section-title:not(.giga-section .giga-section *):before {
        content: '▶';
        font-size: 14pt;
        color: #999;
        float: left;
        transition: transform 0.3s;
        margin-right: 5px;
    }
    .giga-section.expander.active .giga-section-title:not(.giga-section .giga-section *):before {
        transform: rotate(90deg);
    }
    .giga-section.expander .giga-section-contents:not(.giga-section .giga-section *) {
        max-height: 0;
        overflow-y: hidden;
        transition: max-height 0.5s ease-in-out;
    }
    .giga-section.expander.active .giga-section-contents:not(.giga-section .giga-section *) {
        max-height: 1500px;
    }
    .giga-section.expander:not(.active) .giga-section-contents:not(.giga-section .giga-section *) {
        padding: 0;
    }
</style>"""
    )
)


def section(title: str, contents: HTML, extra_class: str = "") -> HTML:
    # For expanding sections, this JS toggles a class that applies expanded/collapsed styles.
    toggle_js = "this.closest('.giga-section').classList.toggle('active');"
    return (
        VBox(
            [
                HTML(f"""<div class="giga-section-title" onclick="{toggle_js}">{title}</div>"""),
                Box([contents]).add_class("giga-section-contents"),
            ]
        )
        .add_class("giga-section")
        .add_class(extra_class)
    )
