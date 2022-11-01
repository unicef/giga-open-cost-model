from tqdm.notebook import tqdm as tqdm_notebook
from tqdm import tqdm

from giga.utils.notebooks import is_notebook

def progress_bar(data):
	if is_notebook():
		return tqdm_notebook(data)
	else:
		return tqdm(data)
