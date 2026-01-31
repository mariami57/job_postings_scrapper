import json
import logging
import os
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from decouple import config

from job_alerts import EMAIL_ADDRESS

EMAIL_ADDRESS = config('EMAIL_ADDRESS')
PASSWORD = config('PASSWORD')
TO_EMAIL = config('TO_EMAIL')

SEEN_JOBS = 'seen_jobs.json'

TITLE_SELECTOR = 'h6'
JOB_CARD_SELECTOR = {'tag': 'div', 'class': 'job-card'}
JOB_CONTAINER = {'tag': 'div', 'class': 'job-container'}
LINK_SELECTOR = {'tag': 'a', 'attr':'href', 'class': 'overlay-link'}

def load_seen_jobs():
    if os.path.exists(SEEN_JOBS):
        try:
            with open(SEEN_JOBS, 'r') as f:
                return set(json.load(f))
        except json.JSONDecodeError:
            logging.warning('seen_jobs.json not found')
    return set()

def scrape_jobs(url, seen_jobs):
    header = {
        'User-Agent': 'Mozilla/5.0 (compatible; JobScraper/1.0)'
    }

    response = requests.get(url, headers=header, timeout=10)

    soup = BeautifulSoup(response.text, 'html-parser')
    job_cards = soup.findall(JOB_CARD_SELECTOR['tag'], class_=JOB_CARD_SELECTOR['class'])

    if not job_cards:
        logging.warning('No jobs found')
    logging.info('found new jobs')

    parsed_url = urlparse(url)
    source = parsed_url.netloc

    jobs_list = []

    for job in job_cards:
        title_elem = job.find(TITLE_SELECTOR)
        link_elem = job.find(LINK_SELECTOR['tag'], _class=LINK_SELECTOR['class'], href=True)


        title = title_elem.text.strip() if title_elem else None
        link = link_elem['href'] if link_elem else None

        if not title or not link:
            continue
        if not link in seen_jobs:
            jobs_list.append({'title': title, 'link': link, 'source': source})
    return jobs_list