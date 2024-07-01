import requests
import re
import os
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv


load_dotenv()
url = os.getenv('URL')
def get_dentalia_locations():
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    location = []
    location_elements = soup.find_all('div', class_="dg-map_clinic-card")
    for element in location_elements:
        print(element.prettify())
    for element in location_elements:
        try:
            loc_data = {}

            name_loc = element.find('div', class_='heading-style-h5 text-weight-medium')
            if name_loc:
                loc_data['name'] = name_loc.text.strip()
            else:
                loc_data['name'] = 'Unknowen'

            address_loc = element.get('m8l-c-filter-location')
            if address_loc:
                loc_data['address'] = address_loc if address_loc else 'Адрес не указан'

            latio_local = element.get('m8l-map-coord').split(',')
            if len(latio_local) == 2:
                loc_data['latio'] = [float(latio_local[0].strip()), float(latio_local[1].strip())]

            phones_numb = element.find('a', href=lambda x: x.startswith('tel:'))
            loc_data['phones'] = [phones_numb.text.strip()]

            work_hours = element.find('div', class_='dg-map_clinic-info_row')
            if work_hours:
                work_hours = work_hours.find_next('div', string=re.compile(r'L-V|S|D'))
                if work_hours:
                    loc_data['working_hours'] = [work_hours.text.strip()]
            print(work_hours)
            location.append(loc_data)
        except Exception as e:
            print(f'Something wrong: {e}')

    return location


def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


locations = get_dentalia_locations()
save_json(locations, 'dentalia_locations.json')
