import requests
from bs4 import BeautifulSoup

url = 'https://dev.bg/company/jobs/full-stack-development/?_seniority=intern%2Cjunior'
headers = {'User-Agent': 'Mozilla/5.0'}
response = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')
cards = soup.find_all('div', class_='job-list-item')
print(len(cards))