import requests
import re
import json
from bs4 import BeautifulSoup


#def get_parser():
response = requests.get('https://www.santaelena.com.co/tiendas-pasteleria/')
soup = BeautifulSoup(response.text, 'html.parser')
links = soup.find_all('ul', class_='sub-menu elementor-nav-menu--dropdown')
print(links)



def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)