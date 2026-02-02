import logging
import smtplib
from collections import defaultdict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlparse
from decouple import config

from helpers import get_title_selector, fetch_html

logging.basicConfig(level=logging.INFO)
from bs4 import BeautifulSoup
import json
import os
from jinja2 import Environment, FileSystemLoader

IS_CI = os.getenv('GITHUB_ACTIONS') == 'true'
DRY_RUN = config('DRY_RUN', default=False, cast=bool)

EMAIL_ADDRESS = config('EMAIL_ADDRESS')
EMAIL_PASSWORD = config('EMAIL_PASSWORD')
TO_EMAIL = config('TO_EMAIL')


SEEN_JOBS_FILE = 'seen_jobs.json'

SCRAPING_RULES = {
    'dev.bg': {
        'use_selenium': False,
        'job_card': {'tag': 'div','class': 'job-list-item'},
        'job_container': {'tag': 'div', 'class': 'job-card'},
        'title_tag': 'h6',
        'company': {'tag': 'div', 'class': 'company-logo-wrap'},
        'link':  {'tag': 'a', 'attr': 'href', 'class': 'overlay-link'}
    },

    'www.jobs.bg': {
        'use_selenium': True,
        'job_card': {'tag': 'div', 'class': 'mdc-card '},
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

    if rules.get('use_selenium') and IS_CI:
        logging.info(f'Skipping {domain} (Selenium disabled in CI)')
        return []

    title_tag, title_class = get_title_selector(rules, domain)
    if not title_tag:
        return []


    html = fetch_html(url, use_selenium=rules.get('use_selenium', False))
    soup = BeautifulSoup(html, 'html.parser')
    job_cards = soup.find_all(rules['job_card']['tag'],
                              class_=rules['job_card']['class'])


    logging.info(f'Found {len(job_cards)} for jobs on {url}')

    jobs_list = []
    for job in job_cards:
        title_elem = job.find(title_tag, class_=title_class)
        link_elem = job.find(rules['link']['tag'], class_=rules['link']['class'], href=True)

        title = title_elem.text.strip() if title_elem else None
        link = link_elem[rules['link']['attr']] if link_elem else None

        if not title or not link:
            continue

        if link not in seen_jobs:
            jobs_list.append({'title': title, 'link': link, 'source': domain})
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

    if DRY_RUN:
        logging.info('Dry run enabled - email will not be sent')
        for job in new_jobs:
            logging.info(f"[DRY RUN] {job['source']} | {job['title']} | {job['link']}")
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

    if not DRY_RUN:
        save_seen_jobs(seen_jobs)
    else:
        logging.info('DRY RUN — seen_jobs.json not updated')

    send_email(new_jobs)


def save_seen_jobs(seen_jobs):
    with open(SEEN_JOBS_FILE, 'w') as f:
        json.dump(list(seen_jobs), f)

if __name__ == '__main__':
    main()


