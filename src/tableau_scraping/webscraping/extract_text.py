import os
from typing import List

from cv2 import imread as cv2_imread
import fire
import numpy as np
import pandas as pd
import PIL
from PIL import Image
from pytesseract import image_to_string


def get_sec_num(filename: str) -> int:
    """
    Extracts the section number from the filename and returns it as an int
    """
    if filename.startswith('yheader'):
        cut_filename = filename.replace('yheader.0.', '').replace('.png', '')
    elif filename.startswith('viz'):
        cut_filename = filename.replace('viz.0.', '').replace('.png', '')
    elif filename.startswith('joined_img'):
        cut_filename = filename.replace('joined_img_', '').replace('.png', '')
    else:
        raise RuntimeError(f'{filename} does not look like a header or value file.')

    return int(cut_filename)


def get_sorted_filenames(dirname: str) -> List[str]:
    """
    Looks at all of the section numbers of the filenames in a directory and returns
    a sorted list of the filenames.
    """
    dir_filenames = os.listdir(dirname)
    sec_numbers = [get_sec_num(fn) for fn in dir_filenames]
    sorted_tuples = sorted(list(zip(dir_filenames, sec_numbers)), key=lambda x: x[1])
    sorted_filenames = [os.path.join(dirname, x[0]) for x in sorted_tuples]
    return sorted_filenames


def main(week_dir):
    joined_dir = os.path.join(week_dir, 'joined')
    joined_filenames = get_sorted_filenames(joined_dir)
    joined_imgs = [PIL.Image.open(i) for i in joined_filenames]

    # If all the images are combined vertically, it's too large of an image to process.
    # We can't process each one separately though because they cut off at arbitrary points
    # through rows, making some of them illegible.
    # To remedy this, we'll combine sections at a time using a sliding window and then stitch
    # back together based on overlaps, throwing out those lines that could not be read or
    # were misinterpreted due to being incomplete.

    # Plan: create small groups of stitched images, throw away the top and bottom 3ish lines (except for the first and
    # last images), interpret the text, and make the text into a dataframe. Then combine all the dataframes and throw
    # away duplicate lines.

    all_dfs = []

    # Set the group size
    group_size = 8
    first = True
    last = False

    total_files = len(joined_filenames)
    counter = 0
    while counter < total_files:
        print(counter)
        img_group = joined_imgs[counter:counter+group_size]

        if len(img_group) < group_size or counter >= total_files:
            last = True

        # vertically stack images
        imgs_comb = np.vstack([np.asarray(i) for i in img_group])
        imgs_comb = PIL.Image.fromarray(imgs_comb)
        imgs_comb.save('combined_vertical.png')  # this is going to get overwritten each time

        open_img = cv2_imread('combined_vertical.png')
        img_text = image_to_string(open_img)
        parsed = [x.strip() for x in img_text.split('\n') if x.strip()]

        # The problem with `image_to_string()` is that it returns all of the text in one long list, with no distinction
        # between the columns visible in the image. Here are two different attempts to parse those columns.

        # Version 1 (more naive): Divide column length by 3 and check that all columns are the same length
        # data_len = len(parsed) // 3
        # counties = parsed[:data_len]
        # indices = parsed[data_len:(2*data_len)]
        # wows = parsed[-data_len:]

        # Version 2 (less naive): Parse columns based on expected features.
        # WoW% values should all end in "%", counties should be only alpha characters with ".",
        # and index values should all be floats
        wows = [x for x in parsed if x[-1] == '%']
        parsed = [x for x in parsed if x not in wows]
        counties = [x for x in parsed if x[0].isalpha()]
        parsed = [x for x in parsed if x not in counties]
        indices = [x for x in parsed if x[-1].isdigit()]

        try:
            assert len(counties) == len(indices) == len(wows), \
                f'Uneven number of results in groups'
        except:
            # Using this try/except block for debugging purposes
            print('first assert failed')
            raise

        try:
            assert len(parsed) % 3 == 0, f'Uneven number of results for group starting with number {counter}'
        except:
            # Using this try/except block for debugging purposes
            print('second assert failed')
            raise

        group_df = pd.DataFrame(
            {
                'county': counties,
                'index': indices,
                'WoW%': wows,
            }
        )

        # Cut off rows from top and bottom that will be overlapped
        df_len = len(group_df)
        if first:
            group_df = group_df.iloc[:df_len - 3]
        elif last:
            group_df = group_df.iloc[3:]
        else:
            group_df = group_df.iloc[3:df_len - 3]

        all_dfs.append(group_df)

        first = False
        counter += group_size

    # combine all dfs
    df = pd.concat(all_dfs)

    # Drop duplicate rows
    df = df.drop_duplicates()

    # Save output
    df.to_csv(os.path.join(week_dir, 'combined_data.csv'), index=False)


if __name__ == '__main__':
    fire.Fire(main)
