# Job Postings Scraper & Email Alerts

A Python automation project that scrapes junior Python and full-stack developer job postings from websites, deduplicates them, and sends HTML email alerts. Scheduled to run automatically using GitHub Actions.

---

## Features

- **Web Scraping**: Uses `requests` and `BeautifulSoup` to parse job listings from multiple URLs.
- **Deduplication**: Keeps track of previously seen jobs to avoid sending duplicate emails.
- **HTML Email Alerts**: Sends formatted emails with job title, company, and link.
- **Environment Variables**: Uses `.env` or GitHub Secrets for secure storage of credentials.
- **Scheduled Automation**: Runs automatically at 09:00 AM and 2:00 PM UTC using GitHub Actions.
- **Persistent State**: Stores seen jobs between runs using GitHub Actions caching.
- **Logging**: Logs scraping results, warnings, and sent emails.

---

## Technologies Used

- Python 3
- [Requests](https://pypi.org/project/requests/)
- [BeautifulSoup](https://pypi.org/project/beautifulsoup4/)
- [Jinja2](https://pypi.org/project/Jinja2/) for HTML email templates
- [smtplib](https://docs.python.org/3/library/smtplib.html) for sending emails
- GitHub Actions for scheduled automation
- GitHub Secrets for secure credentials

---

## Installation (Local Testing)

1. Clone the repository:

```bash
git clone https://github.com/<your-username>/job_postings_scrapper.git
cd job_postings_scrapper

```
2. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file with your credentials (you can use the template_env file):
- For Gmail with 2FA enabled, generate an App Password

5. Run the script:
```bash
python job_alerts.py
```


## GitHub Actions (Automation)

 - Workflow file: .github/workflows/job_alerts.yml

 - Schedule: 09:00 AM and 2:00 PM UTC daily

 - Requires GitHub Secrets:
   EMAIL_ADDRESS=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   TO_EMAIL=recipient_email@gmail.com

 - The workflow automatically caches seen_jobs.json to persist state between runs.

## Project Structure
```bash
job_postings_scrapper/
├── job_alerts.py          # Main scraping and emailing script
├── email_template.html    # HTML template for emails
├── requirements.txt       # Project dependencies
├── .github/workflows/     # GitHub Actions workflow
├── .gitignore
└── README.md
```

## How It Works
1. Scraping: Script fetches job postings from configured URLs.

2. Parsing: Extracts job title, company, and link from HTML.

3. Deduplication: Checks seen_jobs.json for already sent jobs.

4. Emailing: Sends HTML email listing all new jobs.

5. Persistence: Updates seen_jobs.json and caches it via GitHub Actions.

6. Automation: GitHub Actions runs the script automatically on schedule.

## Skills Demonstrated
- Web scraping and HTML parsing

- Python automation and scheduling

- Secure handling of credentials

- GitHub Actions for CI/CD

- Data persistence across runs

- Email formatting and sending

## License

MIT License