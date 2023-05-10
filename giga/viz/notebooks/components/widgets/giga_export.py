import base64
from IPython.display import HTML, display
from ipywidgets import Output, HBox
import io
from PyPDF2 import PdfWriter


def make_export_cost_button(df, title="Export Costs", filename="costs.csv"):
    csv = df.to_csv()
    b64 = base64.b64encode(csv.encode())
    payload = b64.decode()
    html = """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                .custom-button {{
                    background-color: #ffe3c9;
                    border: none;
                    color: #474747;
                    padding: 8px 16px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 12px;
                    margin: 4px 2px;
                    cursor: pointer;
                    border-radius: 6px;
                    width: 180px;
                }}
            </style>
        </head>
        <body>
            <a download="{filename}" href="data:text/csv;base64,{payload}" download>
                <button class="custom-button">{title}</button>
            </a>
        </body>
        </html>
    """
    html = html.format(payload=payload, title=title, filename=filename)
    out = Output()
    with out:
        display(HTML(html))
    return out


def make_export_config_button(
    scenario, title="Export Configuration", filename="config.json"
):
    payload = scenario.config_json
    b64 = base64.b64encode(payload.encode())
    payload = b64.decode()
    html = """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                .custom-button {{
                    background-color: #ffe3c9;
                    border: none;
                    color: #474747;
                    padding: 8px 16px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 12px;
                    margin: 4px 2px;
                    cursor: pointer;
                    border-radius: 6px;
                    width: 180px;
                }}
            </style>
        </head>
        <body>
            <a download="{filename}" href="data:text/csv;base64,{payload}" download>
                <button class="custom-button">{title}</button>
            </a>
        </body>
        </html>
    """
    html = html.format(payload=payload, title=title, filename=filename)
    out = Output()
    with out:
        display(HTML(html))
    return out


def make_export_report_button(df, title="Export Report", filename="report.pdf"):
    output = io.BytesIO()
    pdf_writer = PdfWriter()
    pdf_writer.add_blank_page(width=72, height=72)
    with output:
        pdf_writer.write(output)
        pdf_bytes = output.getvalue()
    b64 = base64.b64encode(pdf_bytes)
    payload = b64.decode()

    html = """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                .custom-button {{
                    background-color: #ffe3c9;
                    border: none;
                    color: #474747;
                    padding: 8px 16px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 12px;
                    margin: 4px 2px;
                    cursor: pointer;
                    border-radius: 6px;
                    width: 180px;
                }}
            </style>
        </head>
        <body>
            <a download="{filename}" href="data:application/pdf;base64,{payload}" download>
                <button class="custom-button">{title}</button>
            </a>
        </body>
        </html>
    """
    html = html.format(payload=payload, title=title, filename=filename)
    out = Output()
    with out:
        display(HTML(html))
    return out


def make_export_button_row(table, inputs):
    b1 = make_export_config_button(inputs)
    b2 = make_export_cost_button(table)
    b3 = make_export_report_button(table)
    return HBox([b1, b2, b3])
