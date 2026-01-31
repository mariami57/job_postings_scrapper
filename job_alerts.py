import logging
import smtplib
from collections import defaultdict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlparse
from decouple import config
logging.basicConfig(level=logging.INFO)
import requests
from bs4 import BeautifulSoup
import json
import os
from jinja2 import Environment, FileSystemLoader

EMAIL_ADDRESS = config('EMAIL_ADDRESS')
EMAIL_PASSWORD = config('EMAIL_PASSWORD')
TO_EMAIL = config('TO_EMAIL')


SEEN_JOBS_FILE = 'seen_jobs.json'

JOB_CARD_SELECTOR = {'tag': 'div','class': 'job-list-item'}
JOB_CONTAINER = {'tag': 'div', 'class': 'job-card'}
TITLE_TAG = 'h6'
COMPANY_SELECTOR = {'tag': 'div', 'class': 'company-logo-wrap'}
LINK_SELECTOR = {'tag': 'a', 'attr': 'href', 'class': 'overlay-link'}

def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        try:
            with open(SEEN_JOBS_FILE, 'r') as f:
                return set(json.load(f))
        except json.JSONDecodeError:
            logging.warning('seen_jobs.json is empty or corrupted. Starting fresh.')
    return set()

def scrape_jobs(url, seen_jobs):
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; JobScraper/1.0)'
    }

    response = requests.get(url, headers=headers, timeout=10)

    soup = BeautifulSoup(response.text, 'html.parser')
    job_cards = soup.find_all(JOB_CARD_SELECTOR['tag'],
                              class_=JOB_CARD_SELECTOR['class'])

    if not job_cards:
        logging.warning('No job cards found — page structure may have changed')

    logging.info(f'Found {len(job_cards)} for jobs on {url}')

    parsed_url = urlparse(url)
    source = parsed_url.netloc
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
            jobs_list.append({'title': title, 'link': link, 'source': source})
            seen_jobs.add(link)

    return jobs_list

def collect_all_jobs(urls, seen_jobs):
    all_new_jobs = []
    for url in urls:
        new_jobs = scrape_jobs(url, seen_jobs)
        all_new_jobs.extend(new_jobs)
    return all_new_jobs


def send_email(new_jobs):
    if not new_jobs:
        logging.info('No new jobs to send')
        return

    jobs_by_site = defaultdict(list)
    for job in new_jobs:
        jobs_by_site[job['source']].append(job)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(BASE_DIR))
    template = env.get_template('email_template.html')
    html_body = template.render(jobs_by_site=jobs_by_site)

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg['Subject'] = f'New Python Job Postings ({len(new_jobs)})'
    msg.attach(MIMEText(html_body, 'html'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    logging.info(f'Sent email with {len(new_jobs)} new jobs')

def main():

    urls = [
        'https://dev.bg/company/jobs/python/?_seniority=intern%2Cjunior',
        'https://dev.bg/company/jobs/full-stack-development/?_seniority=intern%2Cjunior',
        'https://dev.bg/company/jobs/junior-intern/'
            ]

    seen_jobs = load_seen_jobs()
    new_jobs = collect_all_jobs(urls, seen_jobs)
    save_seen_jobs(seen_jobs)
    send_email(new_jobs)


def save_seen_jobs(seen_jobs):
    with open(SEEN_JOBS_FILE, 'w') as f:
        json.dump(list(seen_jobs), f)

if __name__ == '__main__':
    main()


