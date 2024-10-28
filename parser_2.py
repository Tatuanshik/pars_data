import requests
import re
import os
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv


load_dotenv()
url = os.getenv('URL_2')


def format_working_hours(schedule):
    """Функция переводит дни недели в необхоидимый формат, например 1-5 будет Пн-Пт"""
    days_map = {0: 'Вс', 1: 'Пн', 2: 'Вт', 3: 'Ср', 4: 'Чт', 5: 'Пт', 6: 'Сб'}
    format_hours = []
    intervals = []
    for entry in schedule:
        intervals.append((entry['startDay'], entry['endDay'], entry['openTime'][:5], entry['closeTime'][:5]))

    for start_day, end_day, open_time, close_time in intervals:
        if start_day == end_day:
            format_hours.append(f"{days_map[start_day]} {open_time} - {close_time}")
        else:
            format_hours.append(f"{days_map[start_day]} - {days_map[end_day]} {open_time} - {close_time}")
    return format_hours


def get_parser():
    """Функция содержит основаную логику парсера"""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    location_elements = soup.find_all('script', string=lambda text: text and 'window.initialState = {' in text)
    phone_n = soup.find('a', href=lambda x: x.startswith('tel:'))
    for loc in location_elements:
        script_content = loc.text
        json_match = re.search(r'window\.initialState\s*=\s*({.*})', script_content)
        if json_match:
            json_str = json_match.group(1)
        try:
            data_dict = json.loads(json_str)
            delivery_zone = data_dict.get('shops')
            restaurants = []
            for zone in delivery_zone:
                loc_data = {}
                loc_data['name'] = 'Японский домик'
                address_loc = zone.get('address')
                if address_loc:
                    loc_data['address'] = f'Омск, {address_loc}'
                loc_data['phones'] = [phone_n.text]
                latio_local = zone.get('coord')
                if len(latio_local) == 2:
                    loc_data['latio'] = [float(latio_local['latitude'].strip()), float(latio_local['longitude'].strip())]
                working_hours = zone.get('schedule')
                loc_data['working_hours'] = format_working_hours(working_hours)
                restaurants.append(loc_data)
        except Exception as e:
            print(f'Something wrong: {e}')
    return restaurants


def save_json(data, filename):
    """Сохранение данных в формат json"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    restaurant_data = get_parser()
    save_json(restaurant_data, 'sushi_omsk_locations.json')
