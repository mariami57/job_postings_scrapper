import requests

url = "https://www.jobs.bg/front_job_search.php?subm=1&categories%5B%5D=56&techs%5B%5D=Python&job_type%5B%5D=4&is_entry_level=1"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers)
print(response.text[:1000])