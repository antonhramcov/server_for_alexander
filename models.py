import json
from random import shuffle
from re import findall
from bot import send_request
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_list_regions() -> list:
    with open('files/regions.txt', 'r', encoding="utf-8") as f:
        return [i.strip() for i in f.readlines()]

def make_correct_name(s:str) -> str:
    words = findall(r'[^\\"]+', s)
    if len(words)==2:
        words[1] = f'"{words[1]}"'
        return ''.join(words)
    else:
        return None

def search_companies(standarts:list) -> list:
    companies = {}
    for standart in standarts:
        with open(f'files/{standart}.csv', 'r') as f:
            comps = [(comp.split(',')[0], comp.split(',')[1].strip()) for comp in f.readlines()[1:]]
        for comp in comps:
            if comp[1] not in companies:
                companies[comp[1]] = {'name':comp[0], 'standarts':[standart]}
            else:
                companies[comp[1]]['standarts'].append(standart)
    return sorted(companies.items(), key=lambda items: len(items[1]['standarts']), reverse=True)


def get_args_from_url(s) -> dict:
    args = {}
    for arg in s.split('?')[1].split('&'):
        if arg.split('=')[0] not in args:
            if arg.split('=')[0].startswith('standarts') or arg.split('=')[0].startswith('address') or arg.split('=')[0].startswith('number'):
                args[arg.split('=')[0]] = [arg.split('=')[1]]
            else:
                args[arg.split('=')[0]] = arg.split('=')[1]
        else:
            args[arg.split('=')[0]].append(arg.split('=')[1])
    return args

def get_names_companies_for_request(l:list) -> list:
    output_list = [i for i in [make_correct_name(comp[1]['name']) for comp in l[:20]] if i!=None]
    shuffle(output_list)
    return output_list

def from_json_to_text(d:dict) -> str:
    text = ''
    text += f'Выбранные стандарты:\n'
    for i in range(len(d['selectedStandarts'])):
        text += f'{i + 1}. {d['selectedStandarts'][i]}\n'
    text += f'Наименование компании: {d['name']}\n'
    text += f'Регион: {d['region']}\n'
    for i in range(21):
        if f'address_{i}' in d and f'number_{i}' in d:
            text += f'Информация об офисе №{i+1}:\n'
            text += f'  Адрес компании: {d[f'address_{i}']}\n'
            text += f'  Общая численность: {d[f'number_{i}']}\n'
    text += f'Область сертификации (основной ОКВЭД или вид деятельности компании): {d['activity']}\n'
    text += f'Желаемые сроки для проведения аудита: {d['date']}\n'
    text += f'Примечания и пожелания: {d['notes']}\n'
    text += f'Контактные данные:\n'
    text += f'ФИО: {d['fullname']}\n'
    text += f'Телефон: {d['phone']}\n'
    text += f'Адрес электронной почты: {d['email']}\n'
    text += f'Предпочитаемый вид связи и время для связи: {d['connection']}\n'
    if 'selectedCompanies' in d:
        text += f'Выбранные компании:\n'
        for i in range(len(d['selectedCompanies'])):
            text += f'{i+1}. {d['selectedCompanies'][i]}\n'
    return text

def save_request(d:dict, id:str):
    with open(f'requests/{id}.json', 'w') as f:
        json.dump(d, f)
    return f'Заявка {id} сохранена'

def load_requests(id:str) -> dict:
    with open(f'requests/{id}.json', 'r') as f:
        d = json.load(f)
    return d

def bot_send_message(text:str, unical_id):
    asyncio.run(send_request(text, unical_id))

def make_email_from_json(path_to_json):
    with open(path_to_json, 'r') as f:
        d = json.load(f)
    del d['selectedCompanies']
    text = from_json_to_text(d)
    with open('email_sample.txt', 'r') as f:
        sample = f.read()
    sample = sample.replace('<ТЕКСТ ЗАПРОСА>', text)
    msg = MIMEMultipart()
    msg['Subject'] = 'Audit Advisor: Заявка на сертификацию системы менеджмента'
    msg.attach(MIMEText(sample, 'plain'))
    return msg

def get_dict_names_and_email():
    with open('files/Live_Status.csv', 'r') as f:
        names = {i.split(',')[0].replace('"',''):i.split(',')[3] for i in f.readlines()[1:]}
    return names

def get_list_emails(list_companies):
    companies = [comp.replace('"', '') for comp in list_companies]
    emails = get_dict_names_and_email()
    return [emails.get(comp) for comp in companies]

def add_user(id, username):
    with open('files/users.txt', 'a') as f:
        f.write(f'{id}:{username}\n')