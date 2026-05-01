import json
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import DATA1_PATH, DATA3_PATH, FILES_DIR, REQUESTS_DIR


def find_standarts_from_str(s: str):
    return re.findall(r'[0-9]{4,5}', s)


def get_field(data: dict, *keys: str):
    for key in keys:
        if key in data:
            return data[key]
    return None


def from_json_to_text(d: dict) -> str:
    text = ''

    selected_standarts = get_field(d, 'selectedStandarts', 'selectedStandards') or []
    if selected_standarts:
        text += 'Выбранные стандарты:\n'
        for i, standart in enumerate(selected_standarts, start=1):
            text += f'{i}. {standart}\n'

    name = get_field(d, 'Name', 'name')
    if name:
        text += f'Наименование компании: {name}\n'

    region = get_field(d, 'Region', 'region')
    if region:
        text += f'Регион: {region}\n'

    for i in range(21):
        address = get_field(d, f'Address_{i}', f'address_{i}')
        number = get_field(d, f'Number_{i}', f'number_{i}')
        if address is not None and number is not None:
            text += f'Информация об офисе №{i+1}:\n'
            text += f'  Адрес компании: {address}\n'
            text += f'  Общая численность: {number}\n'

    activity = get_field(d, 'Activity', 'activity')
    if activity:
        text += f'Область сертификации (основной ОКВЭД или вид деятельности компании): {activity}\n'

    date_value = get_field(d, 'Date', 'date')
    if date_value:
        text += f'Желаемые сроки для проведения аудита: {date_value}\n'

    notes = get_field(d, 'Notes', 'notes')
    if notes is not None:
        text += f'Примечания и пожелания: {notes}\n'

    fullname = get_field(d, 'Fullname', 'fullname')
    phone = get_field(d, 'Phone', 'phone')
    email = get_field(d, 'Email', 'email')
    connection_type = get_field(d, 'ConnectionType', 'connection')
    connection_time = get_field(d, 'ConnectionTime', 'connectionTime')

    if fullname or phone:
        text += 'Контактные данные:\n'

    if fullname:
        text += f'ФИО: {fullname}\n'
    if phone:
        text += f'Телефон: {phone}\n'
    if email:
        text += f'Адрес электронной почты: {email}\n'
    if connection_type:
        text += f'Предпочитаемый вид связи: {connection_type}\n'
    if connection_time:
        text += f'Примечание: {connection_time}\n'

    selected_companies = d.get('selectedCompanies', [])
    if selected_companies:
        text += 'Выбранные компании:\n'
        for i, company in enumerate(selected_companies, start=1):
            text += f'{i}. {company}\n'

    return text


def save_request(d: dict, request_id: str):
    email_text = from_json_to_text(d)
    with open('email_sample.txt', 'r') as f:
        sample = f.read()
    sample = sample.replace('<ТЕКСТ ЗАПРОСА>', email_text)
    d['email_text'] = sample
    write_request(d, request_id)


def write_request(d: dict, request_id: str):
    with open(REQUESTS_DIR / f'{request_id}.json', 'w') as f:
        json.dump(d, f)


def load_request(request_id: str) -> dict:
    with open(REQUESTS_DIR / f'{request_id}.json', 'r') as f:
        return json.load(f)


def make_email_from_json(path_to_json):
    with open(path_to_json, 'r') as f:
        data = json.load(f)
    data.pop('selectedCompanies', None)
    sample = data['email_text']
    msg = MIMEMultipart()
    msg['Subject'] = 'Audit Advisor: Заявка на сертификацию системы менеджмента'
    msg.attach(MIMEText(sample, 'plain'))
    return msg


def add_user(user_id, username):
    with open(FILES_DIR / 'users.txt', 'a') as f:
        f.write(f'{user_id}:{username}\n')


def save_binary_file(filename: str, content: bytes):
    with open(FILES_DIR / filename, 'wb') as f:
        f.write(content)


def load_binary_file(filename: str) -> bytes:
    with open(FILES_DIR / filename, 'rb') as f:
        return f.read()


def list_binary_files() -> list[str]:
    return sorted([path.name for path in FILES_DIR.iterdir() if path.is_file() and not path.name.startswith('.')])


def save_cache_data(data1: list[dict], data3: list[dict]):
    with open(DATA1_PATH, 'w') as f:
        json.dump(data1, f)
    with open(DATA3_PATH, 'w') as f:
        json.dump(data3, f)
