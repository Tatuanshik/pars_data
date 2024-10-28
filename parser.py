import requests
import re
import os
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('URL')


def format_working_hours(work_hours_str):
    """Функция переводит сокращенные дни недели на испанском языке в английские дни недели сокращенные до 3х букв,
    например M - tue"""
    day_ranges = re.findall(r'([A-Z]-[A-Z]|[A-Z])\s*(\d{1,2}:\d{2})\s*a\s*(\d{1,2}:\d{2})', work_hours_str)
    days_map = {
        'L': 'mon',
        'M': 'tue',
        'X': 'wed',
        'J': 'thu',
        'V': 'fri',
        'S': 'sat',
        'D': 'sun'
    }
    working_hours = {}
    for day_range, open_time, close_time in day_ranges:
        if '-' in day_range:
            start_day, end_day = day_range.split('-')
            start_index = list(days_map.keys()).index(start_day)
            end_index = list(days_map.keys()).index(end_day)
            for i in range(start_index, end_index + 1):
                day = list(days_map.keys())[i]
                working_hours[days_map[day]] = f"{open_time} - {close_time}"
        else:
            day = days_map.get(day_range)
            if day:
                working_hours[day] = f"{open_time} - {close_time}"
    compressed_hours = compress_working_hours(working_hours)
    return compressed_hours


def compress_working_hours(working_hours):
    """Функция сжимает дни недели, которые повторяютя в удобный формат, например
     из 'mon': '9:00 - 17:00' и 'tue': '9:00 - 17:00' wed': '9:00 - 17:00'
     будет: mon - wed: 09:00 - 17:00"""
    compressed_hours = {}
    current_range = []
    current_time = None
    for day, time in working_hours.items():
        if time != current_time:
            if current_range:
                if len(current_range) > 1:
                    compressed_hours[f"{current_range[0]}-{current_range[-1]}"] = current_time
                else:
                    compressed_hours[current_range[0]] = current_time
            current_range = [day]
            current_time = time
        else:
            current_range.append(day)
    if current_range:
        if len(current_range) > 1:
            compressed_hours[f'{current_range[0]}-{current_range[-1]}'] = current_time
        else:
            compressed_hours[current_range[0]] = current_time
    return compressed_hours


def get_parser():
    """Функция содержит основаную логику парсера"""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    location = []
    location_elements = soup.find_all('div', class_="dg-map_clinic-card")
    for element in location_elements:
        try:
            loc_data = {}
            name_loc = element.find('div', class_='heading-style-h5 text-weight-medium')
            if name_loc:
                loc_data['name'] = name_loc.text.capitalize().strip()
            else:
                loc_data['name'] = 'Unknown'
            address_loc = element.get('m8l-c-filter-location')
            loc_data['address'] = address_loc if address_loc else 'Адрес не указан'
            latio_local = element.get('m8l-map-coord')
            if latio_local:
                latio_local = latio_local.split(',')
                if len(latio_local) == 2:
                    loc_data['latio'] = [float(latio_local[0].strip()), float(latio_local[1].strip())]
            phones_numb = element.find('a', href=lambda x: x.startswith('tel:'))
            loc_data['phones'] = [phones_numb.text.strip()] if phones_numb else []
            work_hours = element.find('div', class_='dg-map_clinic-info_row')
            if work_hours:
                work_hours = work_hours.find_next('div', string=re.compile(r'L-V|S|D'))
                if work_hours:
                    formatted_hours = format_working_hours(work_hours.text.strip())
                    loc_data['working_hours'] = formatted_hours
            location.append(loc_data)
        except Exception as e:
            print(f'Something went wrong: {e}')
    return location


def save_json(data, filename):
    """Сохранение данных в формат json"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    dentalia_locations = get_parser()
    save_json(dentalia_locations, 'dentalia_locations.json')

