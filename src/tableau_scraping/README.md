# Tableau Scraping

This subdirectory contains scripts for scraping mobility data from [this embedded Tableau public frame]('https://public.tableau.com/profile/fabio.baraghini#!/vizhome/CuebiqMobilityIndexAnalysis/MobilityIndexMarketArea').

While the tags, classes, etc. used in these scripts are specific to retrieving the data in that particular Tableau display, the general approach to scraping data from embedded Tableau pages can be helpful and applied to other instances. The use of the selenium driver as well as switching to be within the context of the Tableau iframe are crucial for correctly accessing the information. 

Unfortunately, the data Tableau displays is rendered as images. In this instance, the images comprising the main data table load dynamically when they need to become visible, so part of the script involves scrolling through the entire table to make sure all of the images load.

From there, the images need to be downloaded and parsed using some OCR software. 


### Running

I used a `conda` environment to run these scripts. All dependencies are located in `environment.yml`.


### Module Summary:

*tableau.py* - primary module for scraping from tableau. Creates a driver, handles scrolling so that all required images load, and downloads them (in this instance, the county names (called the "headers") and the values are stored as separate images and needed to be parsed separately)

*combine_images.py* - stitches the header and value images together horizontally

*extract_text.py* - extracts the text from the images using `pytesseract`. Also contains helper functions for sorting the downloaded images

*runner.py* - main entrypoint, handling scraping and joining images across multiple weeks of data

