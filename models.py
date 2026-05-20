import json
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from config import DATA1_PATH, DATA3_PATH, DATA_US_PATH, FILES_DIR, REQUESTS_DIR, TEMPLATES_DIR


def find_standarts_from_str(s: str):
    return re.findall(r'[0-9]{4,5}', s)


def get_field(data: dict, *keys: str):
    for key in keys:
        if key in data:
            return data[key]
    return None


def normalize_country(country: str | None) -> str:
    normalized = (country or "russia").strip().lower()
    if normalized in {"usa", "us", "united states", "america"}:
        return "usa"
    if normalized in {"uk", "united kingdom", "great britain", "britain"}:
        return "uk"
    return "russia"


def get_template_path(template_kind: str, country: str | None) -> Path:
    normalized_country = normalize_country(country)
    template_map = {
        "company": {
            "russia": Path("email_sample.txt"),
            "usa": TEMPLATES_DIR / "usa_company.txt",
            "uk": TEMPLATES_DIR / "uk_company.txt",
        },
        "success": {
            "russia": Path("answer.txt"),
            "usa": TEMPLATES_DIR / "usa_success.txt",
            "uk": TEMPLATES_DIR / "uk_success.txt",
        },
        "bad": {
            "russia": Path("bad_answer.txt"),
            "usa": TEMPLATES_DIR / "usa_bad.txt",
            "uk": TEMPLATES_DIR / "uk_bad.txt",
        },
    }
    return template_map[template_kind].get(normalized_country, template_map[template_kind]["russia"])


def load_template(template_kind: str, country: str | None) -> str:
    with open(get_template_path(template_kind, country), 'r') as f:
        return f.read()


def load_json(path: Path) -> list[dict]:
    with open(path, 'r') as f:
        return json.load(f)


def get_region_name(region_value: str | int | None, country: str | None) -> str | None:
    if region_value in (None, ""):
        return None

    normalized_country = normalize_country(country)
    try:
        region_number = int(str(region_value))
    except (TypeError, ValueError):
        return str(region_value)

    if normalized_country == "usa":
        for company in load_json(DATA_US_PATH):
            try:
                if int(company.get("Region_number")) == region_number and company.get("Region"):
                    return company["Region"]
            except (TypeError, ValueError):
                continue
        return str(region_value)

    if normalized_country == "russia":
        for company in load_json(DATA1_PATH):
            try:
                if int(company.get("Код региона")) == region_number and company.get("Регион"):
                    return company["Регион"]
            except (TypeError, ValueError):
                continue

    return str(region_value)


def split_subject_and_body(template_text: str, fallback_subject: str) -> tuple[str, str]:
    lines = template_text.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)

    if lines and lines[0].strip().startswith("Audit Advisor:"):
        subject = lines[0].strip()
        body = "\n".join(lines[1:]).lstrip("\n")
        return subject, body

    return fallback_subject, template_text.strip()


def localize_connection_type(connection_type: str | None, country: str | None) -> str | None:
    if not connection_type:
        return connection_type

    normalized_country = normalize_country(country)
    if normalized_country in {"usa", "uk"}:
        return connection_type

    connection_type_map = {
        "email": "По электронной почте",
        "phone": "По телефону",
        "both": "И то, и другое",
    }
    return connection_type_map.get(connection_type, connection_type)


def from_json_to_text(d: dict) -> str:
    country = normalize_country(get_field(d, 'Country', 'country'))
    text = ''

    selected_standarts = get_field(d, 'selectedStandarts', 'selectedStandards') or []
    if selected_standarts:
        text += 'Selected standards:\n' if country in {"usa", "uk"} else 'Выбранные стандарты:\n'
        for i, standart in enumerate(selected_standarts, start=1):
            text += f'{i}. {standart}\n'

    name = get_field(d, 'Name', 'name')
    if name:
        if country in {"usa", "uk"}:
            text += f'Company name: {name}\n'
        else:
            text += f'Наименование компании: {name}\n'

    region = get_region_name(get_field(d, 'Region', 'region'), country)
    if region:
        if country == "usa":
            text += f'State: {region}\n'
        elif country == "uk":
            text += f'Region: {region}\n'
        else:
            text += f'Регион: {region}\n'

    country = get_field(d, 'Country', 'country')
    if country:
        text += f'Country: {country}\n' if normalize_country(country) in {"usa", "uk"} else f'Страна: {country}\n'

    for i in range(21):
        address = get_field(d, f'Address_{i}', f'address_{i}')
        number = get_field(d, f'Number_{i}', f'number_{i}')
        if address is not None and number is not None:
            if normalize_country(get_field(d, 'Country', 'country')) in {"usa", "uk"}:
                text += f'Location #{i+1}:\n'
                text += f'  Address: {address}\n'
                text += f'  Number of employees: {number}\n'
            else:
                text += f'Информация об офисе №{i+1}:\n'
                text += f'  Адрес компании: {address}\n'
                text += f'  Общая численность: {number}\n'

    activity = get_field(d, 'Activity', 'activity')
    if activity:
        if normalize_country(get_field(d, 'Country', 'country')) in {"usa", "uk"}:
            text += f'Certification scope or primary business activity: {activity}\n'
        else:
            text += f'Область сертификации (основной ОКВЭД или вид деятельности компании): {activity}\n'

    date_value = get_field(d, 'Date', 'date')
    if date_value:
        if normalize_country(get_field(d, 'Country', 'country')) in {"usa", "uk"}:
            text += f'Preferred audit timeline: {date_value}\n'
        else:
            text += f'Желаемые сроки для проведения аудита: {date_value}\n'

    notes = get_field(d, 'Notes', 'notes')
    if notes is not None:
        text += f'Notes: {notes}\n' if normalize_country(get_field(d, 'Country', 'country')) in {"usa", "uk"} else f'Примечания и пожелания: {notes}\n'

    fullname = get_field(d, 'Fullname', 'fullname')
    phone = get_field(d, 'Phone', 'phone')
    email = get_field(d, 'Email', 'email')
    connection_type = get_field(d, 'ConnectionType', 'connection')
    connection_time = get_field(d, 'ConnectionTime', 'connectionTime')
    localized_connection_type = localize_connection_type(connection_type, get_field(d, 'Country', 'country'))

    if fullname or phone:
        text += 'Contact details:\n' if normalize_country(get_field(d, 'Country', 'country')) in {"usa", "uk"} else 'Контактные данные:\n'

    if fullname:
        text += f'Contact person: {fullname}\n' if normalize_country(get_field(d, 'Country', 'country')) in {"usa", "uk"} else f'ФИО: {fullname}\n'
    if phone:
        text += f'Phone: {phone}\n' if normalize_country(get_field(d, 'Country', 'country')) in {"usa", "uk"} else f'Телефон: {phone}\n'
    if email:
        text += f'Email: {email}\n' if normalize_country(get_field(d, 'Country', 'country')) in {"usa", "uk"} else f'Адрес электронной почты: {email}\n'
    if localized_connection_type:
        text += f'Preferred contact method: {localized_connection_type}\n' if normalize_country(get_field(d, 'Country', 'country')) in {"usa", "uk"} else f'Предпочитаемый вид связи: {localized_connection_type}\n'
    if connection_time:
        text += f'Preferred contact time or note: {connection_time}\n' if normalize_country(get_field(d, 'Country', 'country')) in {"usa", "uk"} else f'Примечание: {connection_time}\n'

    selected_companies = d.get('selectedCompanies', [])
    if selected_companies:
        text += 'Selected certification bodies:\n' if normalize_country(get_field(d, 'Country', 'country')) in {"usa", "uk"} else 'Выбранные компании:\n'
        for i, company in enumerate(selected_companies, start=1):
            text += f'{i}. {company}\n'

    return text


def save_request(d: dict, request_id: str):
    country = normalize_country(get_field(d, 'Country', 'country'))
    email_text = from_json_to_text(d)
    sample = load_template('company', country)
    sample = sample.replace('<ТЕКСТ ЗАПРОСА>', email_text).replace('<ДЕТАЛИ ЗАПРОСА>', email_text)
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
    fallback_subjects = {
        "russia": 'Audit Advisor: Заявка на сертификацию системы менеджмента',
        "usa": 'Audit Advisor: New Client Inquiry — Certification Request Ready for Your Proposal',
        "uk": 'Audit Advisor: New Client Inquiry — Certification Request Ready for Your Proposal',
    }
    country = normalize_country(get_field(data, 'Country', 'country'))
    subject, body = split_subject_and_body(sample, fallback_subjects[country])
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
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


def save_cache_data(data1: list[dict], data3: list[dict], data_us: list[dict] | None = None):
    with open(DATA1_PATH, 'w') as f:
        json.dump(data1, f)
    with open(DATA3_PATH, 'w') as f:
        json.dump(data3, f)
    if data_us is not None:
        with open(DATA_US_PATH, 'w') as f:
            json.dump(data_us, f)
