import requests



urls = [
    'https://dev.bg/company/jobs/python/?_seniority=intern%2Cjunior',
    'https://dev.bg/company/jobs/full-stack-development/?_seniority=intern%2Cjunior'
        ]


headers = {
    "User-Agent": "Mozilla/5.0 (compatible; JobScraper/1.0)"
}

responses = []

for url in urls:
    response = requests.get(url, headers=headers, timeout=10)
    # print(url, response.status_code)
    responses.append(response)
