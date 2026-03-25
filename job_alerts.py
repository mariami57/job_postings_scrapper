import logging
import smtplib
from collections import defaultdict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlparse
from decouple import config
from helpers import fetch_html
logging.basicConfig(level=logging.INFO)
from bs4 import BeautifulSoup
import json
import os
from jinja2 import Environment, FileSystemLoader

IS_CI = os.getenv('GITHUB_ACTIONS') == 'true'
DRY_RUN = False if IS_CI else config('DRY_RUN', default=False, cast=bool)

EMAIL_ADDRESS = config('EMAIL_ADDRESS')
EMAIL_PASSWORD = config('EMAIL_PASSWORD')
TO_EMAIL = config('TO_EMAIL')

SEEN_JOBS_FILE = 'seen_jobs.json'

SCRAPING_RULES = {
    'dev.bg': {
        'job_card': {'tag': 'div','class': 'job-list-item'},
        'title': {'tag': 'h6', 'class': 'job-title'},
        'company': {'tag': 'div', 'class': 'company-logo-wrap'},
        'link':  {'tag': 'a', 'attr': 'href', 'class': 'overlay-link'}
    },

    'www.jobs.bg': {
        'use_selenium': True,
        'job_card': {'tag': 'div', 'class': 'mdc-card'},
        'title': {'tag': 'div', 'class': 'card-title'},
        'company': {'tag': 'div', 'class': 'secondary-text'},
        'link': {'tag': 'a', 'attr': 'href', 'class': 'mdc-layout-link'}
    }
}

def normalize_link(link):
    parsed = urlparse(link)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        try:
            with open(SEEN_JOBS_FILE, 'r') as f:
                return set(json.load(f))
        except (json.JSONDecodeError, TypeError):
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


    html = fetch_html(url, use_selenium=rules.get('use_selenium', False))
    if IS_CI:
        logging.info(f"DEBUG: HTML snippet for {domain}: {html[:500]}")

    soup = BeautifulSoup(html, 'html.parser')
    job_cards = soup.find_all(rules['job_card']['tag'],
                              class_=rules['job_card']['class'])


    logging.info(f'Found {len(job_cards)} for jobs on {url}')

    jobs_list = []
    seen_in_this_run = set()

    for job in job_cards:
        title_elem = job.find(rules['title']['tag'], class_=rules['title']['class'])
        link_elem = job.find(rules['link']['tag'], class_=rules['link']['class'], href=True)

        title = title_elem.text.strip() if title_elem else None
        link = link_elem[rules['link']['attr']] if link_elem else None

        if not title or not link:
            continue

        normalized_link = normalize_link(link)

        if normalized_link in seen_jobs or normalized_link in seen_in_this_run:
            continue

        jobs_list.append({'title': title, 'link': link, 'source': domain})
        seen_jobs.add(link)

        logging.info(f"New job collected: {title} | {link}")


    logging.info(
        f"Collected {len(jobs_list)} NEW jobs (after filtering seen_jobs)"
    )

    return jobs_list

def collect_all_jobs(urls, seen_jobs):
    all_new_jobs = []
    for url in urls:
        new_jobs = scrape_jobs(url, seen_jobs)
        all_new_jobs.extend(new_jobs)

    unique_jobs = {job['link']: job for job in all_new_jobs}

    return list(unique_jobs.values())


def send_email(new_jobs):

    if not new_jobs:
        logging.info("No new jobs to send, skipping email")
        return


    logging.info(f"Preparing to send email with {len(new_jobs)} jobs to {TO_EMAIL}")

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
    msg['Subject'] = f'New Job Postings ({len(new_jobs)})'
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            logging.info(f"Connecting to SMTP as {EMAIL_ADDRESS}")
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        logging.info(f"Email successfully sent to {TO_EMAIL}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")


def main():
    urls = [
        'https://dev.bg/company/jobs/python/?_seniority=intern%2Cjunior',
        'https://dev.bg/company/jobs/full-stack-development/?_seniority=intern%2Cjunior',
        'https://dev.bg/company/jobs/junior-intern/',
        "https://www.jobs.bg/front_job_search.php?subm=1&categories%5B%5D=56&techs%5B%5D=Python&job_type%5B%5D=4&is_entry_level=1"
    ]

    seen_jobs = load_seen_jobs()
    new_jobs = collect_all_jobs(urls, seen_jobs)

    logging.info(f"Collected {len(new_jobs)} new jobs from scraping")

    send_email(new_jobs)
    save_seen_jobs(seen_jobs)

def save_seen_jobs(seen_jobs):
    try:
        with open(SEEN_JOBS_FILE, 'w') as f:
            json.dump(list(seen_jobs), f, indent=2)
    except Exception as e:
        logging.error(f"Failed to save seen jobs: {e}")

if __name__ == '__main__':
    main()


