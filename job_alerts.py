import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from decouple import config

logging.basicConfig(level=logging.INFO)
import requests
from bs4 import BeautifulSoup
import json
import os

EMAIL_ADDRESS = config('EMAIL_ADDRESS')
EMAIL_PASSWORD = config('EMAIL_PASSWORD')
TO_EMAIL = config('TO_EMAIL')


SEEN_JOBS_FILE = 'seen_jobs.json'

if os.path.exists(SEEN_JOBS_FILE):
    with open(SEEN_JOBS_FILE, 'r') as f:
        seen_jobs = set(json.load(f))
else:
    seen_jobs = set()


urls = [
    'https://dev.bg/company/jobs/python/?_seniority=intern%2Cjunior',
    'https://dev.bg/company/jobs/full-stack-development/?_seniority=intern%2Cjunior'
        ]


headers = {
    'User-Agent': 'Mozilla/5.0 (compatible; JobScraper/1.0)'
}

responses = []

JOB_CARD_SELECTOR = {'tag': 'div','class': 'job-list-item'}
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

        if not title or not link:
            continue

        if link not in seen_jobs:
            jobs_list.append({'title': title, 'link': link})
            seen_jobs.add(link)

    if jobs_list:
        body = ''
        for new_job in jobs_list:
            body += f"New posting for {new_job['title']}, apply here: {new_job['link']}\n\n"
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = TO_EMAIL
        msg['Subject'] = f'New Python Job Postings ({len(jobs_list)})'
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        logging.info(f'Sent email with {len(jobs_list)} new jobs')
    else:
        logging.info('No new jobs to send')

    logging.info(f'New jobs found: {len(jobs_list)}')
    for job in jobs_list:
        logging.info(job['title'])

with open(SEEN_JOBS_FILE, 'w') as f:
    json.dump(list(seen_jobs), f)



