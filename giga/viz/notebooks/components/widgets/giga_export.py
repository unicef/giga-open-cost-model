import base64
import tempfile
from selenium import webdriver
from IPython.display import HTML, display
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from ipywidgets import Output, VBox, Button, Widget
from ipywidgets.embed import embed_minimal_html
import io
import base64
import folium
import os
import shutil
import plotly
import time
import pickle
from zipfile import ZipFile
from PIL import Image

from giga.utils.progress_bar import progress_bar as pb


def make_export_cost_button(df, title="Export Costs", filename="costs.csv"):
    csv = df.to_csv()
    b64 = base64.b64encode(csv.encode())
    payload = b64.decode()
    html = """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
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

PAGE_WIDTH = 8 * inch
PAGE_HEIGHT = 6 * inch

def render_screenshot(tmpfile):
    # Adjust zoom to crop closer to the center of the web contents
    zoom_scale = 1.5
    try:
        browser = webdriver.Chrome()
    except:
        raise Exception("Error: Google Chrome must be installed in order to turn graphs into PDFs in the background.")
    browser.set_window_size(PAGE_WIDTH * zoom_scale, PAGE_HEIGHT * zoom_scale)
    browser.get("file://" + tmpfile)
    time.sleep(0.2)
    png_bytes = browser.get_screenshot_as_png()
    browser.quit()
    return png_bytes

def generate_pdf_bytes(el_list):
    # Create a scratch temp file
    tmpdir = tempfile.mkdtemp()
    tmpfile = os.path.join(tmpdir, "tmp.html")
    
    output = io.BytesIO()
    pdf_canvas = canvas.Canvas(output, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    has_content = False
    iter_list = el_list if len(el_list) < 5 else pb(el_list)
    for el in iter_list:
        if isinstance(el, folium.Map):
            el.save(tmpfile)
            png_bytes = render_screenshot(tmpfile)
        elif isinstance(el, plotly.graph_objs._figure.Figure):
            png_bytes = plotly.io.to_image(el, format='png', 
                                           width=PAGE_WIDTH * 2, height=PAGE_HEIGHT * 2,
                                           scale=3)
        else:
            continue
        has_content = True
        png = Image.open(io.BytesIO(png_bytes))
        pdf_canvas.drawInlineImage(png, 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        pdf_canvas.showPage()

    # Delete temporary directory
    shutil.rmtree(tmpdir)

    if not has_content:
        return None
    pdf_canvas.save()
    return output.getvalue()

def make_export_report_button(all_output_maps, title="Generate Report", filename="report.pdf"):
    def on_button_clicked(b):
        out.clear_output()
        with out:
            pdf_bytes = generate_pdf_bytes(all_output_maps.get_all())
            b64 = base64.b64encode(pdf_bytes)
            payload = b64.decode()
            html = """
                <a download="{filename}" href="data:application/pdf;base64,{payload}" download>
                    <button class="custom-button">{title}</button>
                </a>
            """
            html = html.format(payload=payload, title="Download Generated Report", filename=filename)
            display(HTML(html))

    button = Button(description=title)
    button.on_click(on_button_clicked)
    out = Output()
    return VBox([button, out])

def make_export_zip_button(all_output_maps, title="Download Graph .zip", filename="graphs.zip"):
    def on_button_clicked(b):
        out.clear_output()
        with out:
            el_list = all_output_maps.get_all()
            zip_buffer = io.BytesIO()
            with ZipFile(zip_buffer, "w") as zip_file:
                i = 0
                for el in pb(el_list):
                    pdf_bytes = generate_pdf_bytes([el])
                    if pdf_bytes is None:
                        continue
                    zip_file.writestr(f"graph_{i}.pdf", pdf_bytes)
                    i += 1
            zip_buffer.seek(0)
            b64 = base64.b64encode(zip_buffer.read())
            payload = b64.decode()
            html = """
                <a download="{filename}" href="data:application/zip;base64,{payload}" download>
                    <button class="custom-button">{title}</button>
                </a>
            """
            html = html.format(payload=payload, title=title, filename=filename)
            display(HTML(html))

    button = Button(description=title)
    button.on_click(on_button_clicked)
    out = Output()
    return VBox([button, out])

class ModelPackage():
    config = None
    output_space = None

def make_export_model_package(config, output_space, title="Results Package", filename="results_package.pkl"):
    def on_button_clicked(b):
        out.clear_output()
        with out:
            pkg = ModelPackage()
            pkg.config = config
            pkg.output_space = output_space
            output_space_bytes = pickle.dumps(pkg)
            payload = output_space_bytes.hex()
            
            # Create a download link
            html = """
                <a download="{filename}" href="data:text/plain;charset=utf-8,{payload}" download>
                    <button class="custom-button">{title}</button>
                </a>
            """
            html = html.format(payload=payload, title=title, filename=filename)
            display(HTML(html))

    button = Button(description=title)
    button.on_click(on_button_clicked)
    out = Output()
    return VBox([button, out])

def make_export_button_row(config, output_space, table, inputs, all_output_maps = None):
    b1 = make_export_config_button(inputs)
    b2 = make_export_cost_button(table)
    b3 = make_export_model_package(config, output_space)
    if all_output_maps is None:
        return VBox([b1, b2, b3])
    b4 = make_export_report_button(all_output_maps)
    b5 = make_export_zip_button(all_output_maps)
    return VBox([b1, b2, b3, b4, b5])
