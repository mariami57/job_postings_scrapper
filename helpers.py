import logging
import time

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def get_title_selector(rules, domain):
    if 'title_tag' in rules:
        return rules['title_tag'], None

    elif 'title' in rules:
        return rules['title']['tag'], rules['title'].get('class')

    else:
        logging.warning('No title selector defined for {domain}, skipping...')

        return None, None

def fetch_html(url, use_selenium=False):
    if not use_selenium:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        return response.text

    options = Options()
    options.add_argument('--headless')
    options.add_argument('-disable-blink-features=AutomationControlled')

    driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options)

    driver.get(url)
    time.sleep(5)
    html = driver.page_source
    driver.quit()

    return html