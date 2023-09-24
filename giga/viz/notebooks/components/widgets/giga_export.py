import base64
import tempfile
from selenium import webdriver
from IPython.display import HTML, display
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from ipywidgets import Output, VBox, Button, Widget
import ipywidgets as pw
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

from giga.viz.notebooks.data_maps.result_maps import (
    make_fiber_distance_map_plot,
    make_cellular_distance_map_plot,
    make_cellular_coverage_map,
    make_p2p_distance_map_plot,
)

from giga.viz.notebooks.components.charts.plotters import (
    cumulative_fiber_distance_barplot,
    cumulative_cell_tower_distance_barplot,
    cumulative_visible_cell_tower_distance_barplot,
    make_tech_pie_chart,
)

from giga.utils.latex_reports import generate_infra_report
from giga.data.store.stores import SCHOOLS_DATA_STORE as schools_data_store
from giga.data.space.model_data_space import ModelDataSpace

from giga.utils.progress_bar import progress_bar as pb
from giga.viz.notebooks.components.widgets.giga_buttons import make_button
from giga.viz.notebooks.parameters.groups.data_parameter_manager import country_name_to_key

# Force kaleido to run in a single process, or it crashes Jupyter in Docker
plotly.io.kaleido.scope.chromium_args += ("--single-process",) 

display(HTML("""
<style>

.payload-export-button {
    border: 1px solid rgb(255, 159, 64) !important;
    background-color: rgb(255, 227, 201);
    height: 40px;
    width: 200px;
    border-radius: 6px;
    margin: 6px;
    box-shadow: 1px 1px 3px #ccc;
    padding: 0 10px;
}

.payload-export-button:hover {
    box-shadow: 2px 2px 4px #aaa;
}

.payload-export-button, .payload-export-button * {
    cursor: pointer;
}

</style>

"""))


def export_btn(callback, **kwargs):
    return make_button(
            callback,
            height="40px",
            width="226px",
            border_radius="2px",
            margin="6px",
            box_shadow="1px 1px 3px #ccc",
            button_color="#ffe3c9", 
            border="1px solid #ff9f40",
            **kwargs)

def make_payload_export(title, filename, data, data_format):
    if ";base64" in data_format:
        b64 = base64.b64encode(data)
        data = b64.decode()
    html = f"""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <a download="{filename}" href="data:{data_format},{data}" download>
                <button class="payload-export-button">{title}</button>
            </a>
        </body>
        </html>
    """
    out = Output()
    with out:
        display(HTML(html))
    return out


def make_export_cost_button(df, title="Export Costs", filename="costs.csv"):
    return make_payload_export(title, filename, df.to_csv().encode(), "text/csv;base64")


def make_export_config_button(scenario, title="Export Configuration", filename="config.json"):
    return make_payload_export(title, filename, scenario.config_json.encode(), "text/plain;base64")

PAGE_WIDTH = 8 * inch
PAGE_HEIGHT = 6 * inch

def render_screenshot(tmpfile):
    # Adjust zoom to crop closer to the center of the web contents
    zoom_scale = 1.5
    try:
        browser = webdriver.Chrome()
    except:
        return None
        # TODO add chromium executable to environment
        # raise Exception("Error: Google Chrome must be installed in order to turn graphs into PDFs in the background.")
    browser.set_window_size(PAGE_WIDTH * zoom_scale, PAGE_HEIGHT * zoom_scale)
    browser.get("file://" + tmpfile)
    time.sleep(0.2)
    png_bytes = browser.get_screenshot_as_png()
    browser.quit()
    return png_bytes

def generate_png_bytes(el):
    if isinstance(el, folium.Map):
        # Create a scratch temp file
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, "tmp.html")
        el.save(tmpfile)
        png_bytes = render_screenshot(tmpfile)
        # Delete temporary directory
        shutil.rmtree(tmpdir)
        return png_bytes
    elif isinstance(el, plotly.graph_objs._figure.Figure):
        png_bytes = plotly.io.to_image(el, format='png', 
                                           width=PAGE_WIDTH * 2, height=PAGE_HEIGHT * 2,
                                           scale=3)
        return png_bytes
    elif isinstance(el, plotly.graph_objs.FigureWidget):
        png_bytes = plotly.io.to_image(el.to_dict(), format='png', 
                                           width=PAGE_WIDTH * 2, height=PAGE_HEIGHT * 2,
                                           scale=3)
        return png_bytes
    return None


def generate_infra_zip_bytes(country,data_space,m):
    # Create a scratch temp file
    tmpdir = tempfile.mkdtemp()
    tmpfile = os.path.join(tmpdir, "tmp.html") #for snapshot
    country_id = country_name_to_key(country)

    #complete school data
    schools_complete_table = data_space.schools_to_frame()
    schools_unconnected = schools_complete_table[schools_complete_table['connected']==False]
    schools_connected = schools_complete_table[schools_complete_table['connected']==True]
    
    #create all images
    images = [m]
    images.append(make_tech_pie_chart(schools_connected))
    images.append(make_fiber_distance_map_plot(schools_unconnected,country_id))
    images.append(cumulative_fiber_distance_barplot(schools_unconnected))
    images.append(make_cellular_distance_map_plot(schools_unconnected,country_id))
    images.append(cumulative_cell_tower_distance_barplot(schools_unconnected))
    images.append(make_cellular_coverage_map(schools_unconnected,country_id))
    images.append(make_p2p_distance_map_plot(schools_unconnected,country_id))
    images.append(cumulative_visible_cell_tower_distance_barplot(schools_unconnected))

    #save images
    i = 0
    for el in pb(images):
        image_path = os.path.join(tmpdir, f"graph_{i}.png")
        if isinstance(el, folium.Map):
            el.save(tmpfile)
            png_bytes = render_screenshot(tmpfile)
            with open(image_path, 'wb') as f:
                f.write(png_bytes)
        elif isinstance(el, plotly.graph_objs._figure.Figure):
            plotly.io.write_image(el, image_path, format='png')
        elif isinstance(el, plotly.graph_objs.FigureWidget):
            plotly.io.write_image(el.to_dict(), image_path, format='png')
        i+=1

    #create latex file
    doc = generate_infra_report(country,schools_complete_table,schools_unconnected,schools_connected,data_space)

    #copy giga_logo in tmpdir
    local_logo_path = os.path.join(tmpdir,'giga_logo.png')

    blob_client = schools_data_store.blob_service_client.get_blob_client(container="giga", blob='source/infra/reports/aux_files/giga_logo.png')
    with open(local_logo_path, "wb") as download_file:
        download_file.write(blob_client.download_blob().readall())

    #compile latex into pdf
    doc.generate_pdf(os.path.join(tmpdir, "infra_report"), clean_tex=False, clean = True)

    #create zip file
    zip_buffer = io.BytesIO()
    with ZipFile(zip_buffer, "w") as zip_file:
        for filename in os.listdir(tmpdir):
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in ['.png','.tex','.pdf','.log']:
                file_path = os.path.join(tmpdir, filename)
                arcname = os.path.basename(file_path)
                zip_file.write(file_path, arcname)        
    zip_buffer.seek(0)

    #remove tmp files
    shutil.rmtree(tmpdir)

    #return zip bytes
    return zip_buffer.read()

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
        elif isinstance(el, plotly.graph_objs.FigureWidget):
            png_bytes = plotly.io.to_image(el.to_dict(), format='png', 
                                           width=PAGE_WIDTH * 2, height=PAGE_HEIGHT * 2,
                                           scale=3)
        else:
            continue
        if png_bytes is None:
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
            display(make_payload_export("Download Report", filename, pdf_bytes, "text/pdf;base64"))

    button = export_btn(on_button_clicked, description=title)
    button.on_click(on_button_clicked)
    out = Output()
    return VBox([button, out])

def make_export_infra_report_button(inputs, title="Generate Infrastructure Report", filename="infra_report.zip"):
    def on_button_clicked(b):
        out.clear_output()
        with out:
            zip_bytes = generate_infra_zip_bytes(country,data_space,inputs.data_map_m)
            display(make_payload_export("Download Report", filename, zip_bytes, "text/pdf;base64"))

    country= inputs.data_parameter_manager.get_country_name()
    data_space = ModelDataSpace(inputs.data_parameters())
    button = export_btn(on_button_clicked, description=title)
    button.on_click(on_button_clicked)
    out = Output()
    return VBox([button, out])

def make_export_zip_button(m, all_output_maps, title="Download Graph .zip", filename="graphs.zip"):
    def on_button_clicked(b):
        out.clear_output()
        with out:
            el_list = [m] + all_output_maps.get_all()
            zip_buffer = io.BytesIO()
            with ZipFile(zip_buffer, "w") as zip_file:
                i = 0
                for el in pb(el_list):
                    pdf_bytes = generate_png_bytes(el)
                    if pdf_bytes is None:
                        continue
                    zip_file.writestr(f"graph_{i}.png", pdf_bytes)
                    i += 1
            zip_buffer.seek(0)
            display(make_payload_export("Download .zip", filename, zip_buffer.read(), "text/pdf;base64"))

    button = export_btn(on_button_clicked, description=title)
    button.on_click(on_button_clicked)
    out = Output()
    return VBox([button, out])

class ModelPackage():
    def __init__(self, config, selected_schools, output_space):
        self.config = config
        self.selected_schools = selected_schools
        self.output_space = output_space

def make_export_model_package(config, selected_schools, output_space, title="Results Package", filename="results_package.pkl"):
    def on_button_clicked(b):
        out.clear_output()
        with out:
            pkg = ModelPackage(config, selected_schools, output_space)
            output_space_bytes = pickle.dumps(pkg)
            display(make_payload_export("Download package", filename, output_space_bytes.hex(),
                                        "text/plain;charset=utf-8"))

    button = export_btn(on_button_clicked, description=title)
    button.on_click(on_button_clicked)
    out = Output()
    return VBox([button, out])

def make_export_button_row(config, selected_schools, output_space, table, inputs, all_output_maps = None):
    hr = pw.HTML('<hr/>')
    b1 = make_export_config_button(inputs)
    b2 = make_export_cost_button(table)
    b3 = make_export_model_package(config, selected_schools, output_space)
    if all_output_maps is None:
        return VBox([b1, b2, hr, b3])
    b4 = make_export_report_button(all_output_maps)
    b5 = make_export_zip_button(inputs.data_map_m,all_output_maps)
    return VBox([b1, b2, hr, b3, hr, b4, hr, b5])
