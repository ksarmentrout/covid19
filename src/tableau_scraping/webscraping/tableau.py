import os
import re
import time
from typing import Optional

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = 'https://public.tableau.com/profile/fabio.baraghini#!/vizhome/CuebiqMobilityIndexAnalysis/MobilityIndexMarketArea'


def set_up_driver():
    driver = webdriver.Chrome()
    driver.get(URL)
    _ = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "iframe"))
    )

    # Wait to load
    time.sleep(7)

    # Switch to the embedded tableau iframe
    iframe = driver.find_element_by_tag_name('iframe')
    driver.switch_to.frame(iframe)

    return driver


def scrape_week(
        driver: Optional[webdriver.Chrome] = None,
        close_driver: bool = False,
) -> str:
    if driver is None:
        driver = set_up_driver()

    week_div = driver.find_element_by_xpath("//div[@class='sliderText']")
    week_text = week_div.text
    formatted_week = week_text.lower().replace(' ', '_').replace('-', '')

    scroll = driver.find_element_by_xpath(
        "//div[@class='tab-tvScrollY tvimages'][./div[@class='tvimagesContainer' and @style]]"
    )
    # column = driver.find_elements_by_xpath("//canvas[@class='tabCanvas tab-widget']")[1]

    # Reset the scroll bar to the top just in case
    driver.execute_script('arguments[0].scrollTop = (0,0)', scroll)

    # Scroll down in increments
    for i in range(1, 95):
        driver.execute_script('arguments[0].scrollTop = (0,%s)' % str(i * 400), scroll)
        time.sleep(1.0)

    data_containers = []
    # Looking for the tvimagesContainer objects with the highest number of images as children
    # There should only be two with large values, corresponding to the two data column types.
    for x in driver.find_elements_by_class_name('tab-clip'):
        for y in x.find_elements_by_class_name('tvimagesContainer'):
            if len(y.find_elements_by_tag_name('img')) > 20:
                data_containers.append(y)

    assert len(data_containers) == 2

    # Figure out which container has locations and which has data
    container_1_src = data_containers[0].find_element_by_tag_name('img').get_attribute('src')

    def get_sources(container):
        return [img.get_attribute('src') for img in container.find_elements_by_tag_name('img')]

    if 'yheader.0.0' in container_1_src:
        headers = get_sources(data_containers[0])
        values = get_sources(data_containers[1])
    else:
        headers = get_sources(data_containers[1])
        values = get_sources(data_containers[0])

    # Make directories if they do not exist
    if not os.path.isdir(formatted_week):
        os.mkdir(formatted_week)
    header_dir = os.path.join(formatted_week, 'headers')
    value_dir = os.path.join(formatted_week, 'values')
    for dirname in [header_dir, value_dir]:
        if not os.path.isdir(dirname):
            os.mkdir(dirname)

    # Gather the img children from each data container and download all of 'em
    for idx, src_url in enumerate(headers):
        header_pattern = '(yheader\.\d+\.\d+.png)'
        save_filename = re.search(header_pattern, src_url).groups()[0]
        savename = os.path.join(header_dir, save_filename)

        img_data = requests.get(src_url).content
        with open(savename, 'wb') as file:
            file.write(img_data)

        print(f'Saved {idx + 1} / {len(headers)} headers')

    for idx, val_url in enumerate(values):
        value_pattern = '(viz\.\d+\.\d+.png)'
        save_filename = re.search(value_pattern, val_url).groups()[0]
        savename = os.path.join(value_dir, save_filename)

        img_data = requests.get(val_url).content
        with open(savename, 'wb') as file:
            file.write(img_data)

        print(f'Saved {idx + 1} / {len(headers)} values')

    if close_driver:
        driver.close()

    # Return the dirname where the week data was saved
    return formatted_week


if __name__ == '__main__':
    scrape_week(close_driver=True)
