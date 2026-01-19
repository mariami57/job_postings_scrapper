from venv import logger
import logging
logging.basicConfig(level=logging.INFO)



import requests
from bs4 import BeautifulSoup


urls = [
    'https://dev.bg/company/jobs/python/?_seniority=intern%2Cjunior',
    'https://dev.bg/company/jobs/full-stack-development/?_seniority=intern%2Cjunior'
        ]


headers = {
    'User-Agent': 'Mozilla/5.0 (compatible; JobScraper/1.0)'
}

responses = []

JOB_CARD_SELECTOR = {
    "tag": "div",
    "class": "job-list-item"
}


JOB_CONTAINER = {'tag': 'div', 'class': 'job-card'}
TITLE_TAG = 'h6'
COMPANY_SELECTOR = {'tag': 'div', 'class': 'company-logo-wrap'}
LINK_SELECTOR = {'tag': 'a', 'attr': 'href', 'class': 'overlay-link'}

for url in urls:
    response = requests.get(url, headers=headers, timeout=10)
    responses.append(response)


    soup = BeautifulSoup(response.text, 'html.parser')
    job_cards = soup.find_all(JOB_CARD_SELECTOR['tag'],
                class_=JOB_CARD_SELECTOR['class'])

    if not job_cards:
        logging.warning('No job cards found — page structure may have changed')

    logging.info(f'Found {len(job_cards)} for jobs on {url}')

    jobs_list = []

    for job in job_cards:
        title_elem = job.find(TITLE_TAG)
        company_elem = job.find(LINK_SELECTOR['tag'], class_=COMPANY_SELECTOR['class'])
        link_elem = job.find(LINK_SELECTOR['tag'], class_=LINK_SELECTOR['class'], href=True)

        title = title_elem.text.strip() if title_elem else None
        link = link_elem['href'] if link_elem else None

        jobs_list.append({'title': title, 'link': link})
        if not title or not link:
            continue



