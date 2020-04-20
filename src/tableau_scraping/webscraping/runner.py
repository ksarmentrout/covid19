import time
from typing import Optional

import fire

from webscraping import combine_images, tableau


def reset_driver(open_webdriver):
    """
    Tableau refreshes automatically, at which point all previously loaded images are unloaded and
    the session restarts. One week of data is able to be scraped before this happens, but to be
    safe, the driver is closed and reopened before scraping each additional week.
    """
    open_webdriver.close()
    return tableau.set_up_driver()


def scrape_data(num_weeks: Optional[int] = None):
    """
    Main entrypoint to scraping data and joining the header images and value images together.
    `num_weeks` refers to how many weeks worth of data to scrape. If multiple weeks, the back
    arrow is clicked x times to collect data from the xth week before the most recent info.
    """
    if num_weeks is not None:
        driver = tableau.set_up_driver()
        # Scroll back weeks and scrape each one
        for week_counter in range(num_weeks):

            if week_counter > 0:
                # Close and reopen the driver for every new week to avoid automatic refresh
                driver = reset_driver(driver)

            for _ in range(week_counter):
                # Click the back arrow to go back a week, then re-scrape
                back_arrow_div = driver.find_element_by_xpath(
                    "//div[@class='dijitReset dijitSliderButtonContainer dijitSliderButtonContainerH tableauArrowDec']"
                )
                back_arrow_div.click()
                time.sleep(20)

            # Scrape
            week_dirname = tableau.scrape_week(driver)
            combine_images.combine_headers_with_values(week_dirname)

            print(f'Finished {week_dirname}')
            print(f'Completed {week_counter}/{num_weeks} weeks.')
    else:
        driver = tableau.set_up_driver()
        tableau.scrape_week(driver)

    driver.close()


if __name__ == '__main__':
    fire.Fire(scrape_data)
