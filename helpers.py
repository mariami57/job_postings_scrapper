import logging
import time

import requests
from requests import ReadTimeout
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager


def get_title_selector(rules, domain):
    if 'title_tag' in rules:
        return rules['title_tag'], None

    elif 'title' in rules:
        return rules['title']['tag'], rules['title'].get('class')

    else:
        logging.warning('No title selector defined for {domain}, skipping...')

        return None, None

def fetch_html(url, use_selenium=False, max_retries=3, timeout=30):
    if not use_selenium:
        headers = {'User-Agent': 'Mozilla/5.0'}

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
                return response.text
            except (ReadTimeout, ConnectionError) as e:
                logging.warning(f'Attempt {attempt} failed for {url}: {e}')
                if attempt < max_retries:
                    time.sleep(5)
                else:
                    logging.error(f'All attempts failed for {url}')
                    return ''

    options = Options()
    options.add_argument('--headless')
    options.binary_location = '/usr/bin/firefox'

    driver = webdriver.Firefox(
    service=Service(GeckoDriverManager().install()),
    options=options)

    driver.get(url)
    time.sleep(5)
    html = driver.page_source
    driver.quit()

    return html