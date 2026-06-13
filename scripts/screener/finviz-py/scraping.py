import requests
from bs4 import BeautifulSoup

ticker = "BABA"
url = f"https://www.gurufocus.com/term/shiller-pe-ratio/{ticker}"
html = requests.get(url).text
soup = BeautifulSoup(html, "html.parser")

text = soup.get_text()
for line in text.splitlines():
    print(line)
    if "Shiller PE Ratio Range Over" in line:
        print(line.strip())