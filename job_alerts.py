import logging
import smtplib
from collections import defaultdict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlparse
from decouple import config

from helpers import get_title_selector

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

SCRAPING_RULES = {
    'dev.bg': {
        'job_card': {'tag': 'div','class': 'job-list-item'},
        'job_container': {'tag': 'div', 'class': 'job-card'},
        'title_tag': 'h6',
        'company': {'tag': 'div', 'class': 'company-logo-wrap'},
        'link':  {'tag': 'a', 'attr': 'href', 'class': 'overlay-link'}
    },

    'jobs.bg': {
        'job_card': {'tag': 'div', 'class': 'mdc-layout-grid'},
        'title': {'tag': 'div', 'class': 'card-title'},
        'company': {'tag': 'div', 'class': 'secondary-text'},
        'link': {'tag': 'a', 'attr': 'href', 'class': 'mdc-layout-link'}
    }
}


def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        try:
            with open(SEEN_JOBS_FILE, 'r') as f:
                return set(json.load(f))
        except json.JSONDecodeError:
            logging.warning('seen_jobs.json is empty or corrupted. Starting fresh.')
    return set()

def scrape_jobs(url, seen_jobs):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    if domain not in SCRAPING_RULES:
        logging.warning(f'No scraping rules found for {domain}, skipping...')
        return []

    rules = SCRAPING_RULES[domain]

    title_tag, title_class = get_title_selector(rules, domain)
    if not title_tag:
        return []

    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; JobScraper/1.0)'
    }

    response = requests.get(url, headers=headers, timeout=10)

    soup = BeautifulSoup(response.text, 'html.parser')
    job_cards = soup.find_all(rules['job_card']['tag'],
                              class_=rules['job_card']['class'])

    if not job_cards:
        logging.warning('No job cards found — page structure may have changed')

    logging.info(f'Found {len(job_cards)} for jobs on {url}')

    parsed_url = urlparse(url)
    source = parsed_url.netloc
    jobs_list = []
    for job in job_cards:
        title_elem = job.find(title_tag, class_=title_class)
        company_elem = job.find(rules['company']['tag'], class_=rules['company']['class'])
        link_elem = job.find(rules['link']['tag'], class_=rules['link']['class'], href=True)

        title = title_elem.text.strip() if title_elem else None
        link = link_elem[rules['link']['attr']] if link_elem else None

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
        'https://dev.bg/company/jobs/junior-intern/',
        'https://www.jobs.bg/front_job_search.php?subm=1&categories%5B%5D=56&techs%5B%5D=Python&job_type%5B%5D=4&is_entry_level=1'
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


