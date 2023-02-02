from tqdm.notebook import tqdm as tqdm_notebook
from tqdm import tqdm

from giga.utils.notebooks import is_notebook


BAR_FROMAT = '{l_bar}{bar:50}{r_bar}{bar:-50b}'

def progress_bar(data, description=None):
    if is_notebook():
        bar = tqdm_notebook(data)
    else:
        bar = tqdm(data, bar_format=BAR_FROMAT)
    if description: bar.set_description(description)
    return bar


def managed_progress_bar(n_items, description=None):
    if is_notebook():
        bar = tqdm_notebook(total=n_items)
    else:
        bar = tqdm(total=n_items, bar_format=BAR_FROMAT)
    if description: bar.set_description(description)
    return bar
