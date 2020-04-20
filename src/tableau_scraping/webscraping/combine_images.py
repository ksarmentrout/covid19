import os
import shutil

import numpy as np
import PIL
from PIL import Image

from src.tableau_scraping.webscraping import extract_text


def combine_headers_with_values(
        week_base_dirname: str = '',
        delete_headers_and_values: bool = True,
):
    """
    There are columns of county names (called "headers" by the UI) and columns of data.
    This method combines the county name columns with their data rows horizontally.
    """
    header_dirname = os.path.join(week_base_dirname, 'headers')
    values_dirname = os.path.join(week_base_dirname, 'values')

    header_filenames = extract_text.get_sorted_filenames(header_dirname)
    value_filenames = extract_text.get_sorted_filenames(values_dirname)

    joined_dir = os.path.join(week_base_dirname, 'joined')
    if not os.path.isdir(joined_dir):
        os.mkdir(joined_dir)

    for idx, header_file in enumerate(header_filenames):
        header_data = PIL.Image.open(header_file)
        value_data = PIL.Image.open(value_filenames[idx])

        combined = np.hstack([np.asarray(header_data), np.asarray(value_data)])
        combined_img = PIL.Image.fromarray(combined)
        combined_img.save(os.path.join(joined_dir, f'joined_img_{idx}.png'))

    if delete_headers_and_values:
        shutil.rmtree(header_dirname)
        shutil.rmtree(values_dirname)


if __name__ == '__main__':
    combine_headers_with_values()
