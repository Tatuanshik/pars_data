import requests
import json
import re
import os
import logging
from bs4 import BeautifulSoup
from dotenv import load_dotenv


load_dotenv()
url = os.getenv('URL_3')


logging.basicConfig(level=logging.ERROR)


def convert_time(match):
    """""Преобразует строку времени из 12-часовом формате в 24-ой,
    например: 8 a.m. - 08:00, 8 p.m. - 21:00"""
    time_str = match.group(0).strip()
    hour_minute = time_str.split(':')
    hour = int(hour_minute[0])
    minute = int(hour_minute[1][:2])
    if 'p.m.' in time_str and hour != 12:
        hour += 12
    elif 'a.m.' in time_str and hour == 12:
        hour = 0
    return f"{hour:02}:{minute:02}"

def convert_to_24_hour_format(hours):
    """Функция обрабатывает строку в 12-часовом формате, которое может содержать одно или несколько значений
    и возвращает упорядоченные значения, например: 8:00 a.m. and 12:30 p.m. - 08:00 and 12:30"""
    try:
        return re.sub(r'\d{1,2}:\d{2}\s*[ap\.m]*', convert_time, hours)
    except Exception as e:
        logging.error(f'Ошибка при конвертации: {hours} - {str(e)}')
        return hours


def translate_working_hours(data):
    """"Функция переводит сокращенные дни недели на испанском языке в английские дни недели сокращенные до 3х букв
    также функция приводит формат к необходимому виду, где необходимо меняет значение на дефис, например: 8:00 a.m. and 12:30 p.m.
    будет 08:00 and 12:30"""
    days_map = {
        'lunes': 'mon',
        'martes': 'tue',
        'miércoles': 'wed',
        'jueves': 'thu',
        'viernes': 'fri',
        'sábado': 'sat',
        'domingos': 'sun',
        'domingo': 'sun',
        'festivos': 'holiday'
    }
    translated_data = []
    for location in data:
        translated_location = location.copy()
        working_hours = location.get('working_hours', [])
        translated_hours = []
        for hours in working_hours:
            if 'prestamos servicio 24 horas' in hours.lower() or 'prestamos servicio las 24 horas' in hours.lower():
                translated_hours.append('24/7')
                continue
            for start_day, end_day in days_map.items():
                hours = hours.replace(start_day, end_day)
            hours = convert_to_24_hour_format(hours)
            hours = re.sub(r'\b(y|a|\/)\b', '–', hours)
            hours = hours.replace('/', '-')
            translated_hours.append(hours)
        translated_location['working_hours'] = translated_hours
        translated_data.append(translated_location)
    return translated_data


def get_stores_info(url):
    """Основаня логика парсера данных со страниц с информацией о магазинах"""
    response = requests.get(url)
    last_word = url.strip('/').split('/')[-1]
    city_name = last_word.split('-')[-1].capitalize()

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
    else:
        logging.error(f'Ошибка при запросе к URL: {url} - {response.status_code}')
        return []

    stores_data = []
    store_sections = soup.find_all('div', class_='elementor-widget-container')
    for store in store_sections:
        loc_data = {}
        name_tag = store.find('h3', class_='elementor-heading-title elementor-size-default')
        if name_tag:
            loc_data['name'] = name_tag.text.strip().replace('\n', ' ')
        address_tag = store.find_all(['p', 'h4'])
        for addres in address_tag:
            if 'Dirección' in addres.text:
                loc_data['address'] = addres.text.split(':', 1)[-1].strip()
                if loc_data['address']:
                    loc_data['address'] = city_name + ', ' + loc_data['address']
                    break
            next_tag = addres.find_next_sibling()
            if next_tag and (next_tag.name == 'p' or next_tag.name == 'h4'):
                loc_data['address'] = city_name + ', ' + next_tag.text.strip()
                break
        phone_tag = store.find_all(['p', 'h4'])
        for phone in phone_tag:
            if 'Teléfono' in phone.text:
                loc_data['phone'] = phone.text.split(':', 1)[-1].strip()
                if loc_data['phone']:
                    break
                next_tag = phone.find_next_sibling()
                if next_tag and (next_tag.name == 'p' or next_tag.name == 'h4'):
                    loc_data['phone'] = next_tag.text.split(':', 1)[-1].strip()
                    break
        schedule = store.find_all(['p', 'h4'])
        schedules = []
        for sh in schedule:
            if 'Horario de atención:' in sh.text:
                hours_text = sh.text.replace('Horario de atención:', '').strip()
                if hours_text:
                    schedules.append(hours_text.lower())
                    loc_data['working_hours'] = schedules
                next_tag = sh.find_next_sibling()
                while next_tag and (next_tag.name == 'p' or next_tag.name == 'h4'):
                    schedules.append(next_tag.text.strip().lower())
                    next_tag = next_tag.find_next_sibling()
                    loc_data['working_hours'] = schedules
                break
        if loc_data:
            stores_data.append(loc_data)
    combined_stores_data = []
    for i in range(0, len(stores_data), 2):
        if i + 1 < len(stores_data):
            combined_store = {**stores_data[i], **stores_data[i + 1]}
            combined_stores_data.append(combined_store)
        else:
            combined_stores_data.append(stores_data[i])
    return combined_stores_data


def get_parser():
    """Функция извлекает информацию о страницах с нужной информацией о магазинах,
    передает найденные ссылки функцию get_stores_info """
    base_url = url
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser') if response.status_code == 200 else None
    if soup:
        links = soup.select('ul.sub-menu.elementor-nav-menu--dropdown li a')
        locations_data = set()
        all_stores_data = []
        for link in links:
            if 'Pastelerías en' in link.text or 'Pastelería en' in link.text:
                store_url = link['href']
                if store_url not in locations_data:
                    locations_data.add(store_url)
                    store_info = get_stores_info(store_url)
                    all_stores_data.extend(store_info)
        translated_data = translate_working_hours(all_stores_data)
        save_json(translated_data, 'santaelena_locations.json')


def save_json(data, filename):
    """Сохранение в формат json"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    get_parser()
