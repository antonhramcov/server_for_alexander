import json, re, requests
from random import shuffle
from re import findall
import bot, keywords
import asyncio, threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def find_standarts_from_str(s:str):
    return re.findall(r'[0-9]{4,5}',s)

def get_list_regions() -> list:
    with open('files/regions.txt', 'r', encoding="utf-8") as f:
        return [i.strip() for i in f.readlines()]

def make_correct_name(s:str) -> str:
    return s.replace('"','').replace('  ', ' ')

def search_companies(standarts:list) -> list:
    companies = {}
    for standart in standarts:
        int_standart = int(standart)
        with open(f'files/{int_standart}.csv', 'r') as f:
            text = f.read()
            if text.count(';')>text.count(','):
                separator = ';'
            else:
                separator = ','
        with open(f'files/{int_standart}.csv', 'r') as f:
            comps = [(comp.split(separator)[0], comp.split(separator)[1].strip()) for comp in f.readlines()[1:]]
        for comp in comps:
            if comp[1] not in companies:
                companies[comp[1]] = {'name':comp[0], 'standarts':[standart]}
            else:
                companies[comp[1]]['standarts'].append(standart)
    filtered_companies = {}
    for key, val in companies.items():
        for std in standarts:
            if std not in val['standarts']:
                break
        else:
            if key not in filtered_companies:
                filtered_companies[key] = val
    return sorted(filtered_companies.items(), key=lambda items: len(items[1]['standarts']), reverse=True)


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
    output_list = [i for i in [make_correct_name(comp[1]['name']) for comp in l] if i!=None]
    shuffle(output_list)
    return output_list

def from_json_to_text(d:dict) -> str:
    text = ''
    if 'selectedStandarts' in d:
        text += f'Выбранные стандарты:\n'
        for i in range(len(d['selectedStandarts'])):
            text += f'{i + 1}. {d["selectedStandarts"][i]}\n'
    if 'Name' in d:
        text += f'Наименование компании: {d["Name"]}\n'
    if 'Region' in d:
        text += f'Регион: {d["Region"]}\n'
    for i in range(21):
        if f'Address_{i}' in d and f'Number_{i}' in d:
            text += f'Информация об офисе №{i+1}:\n'
            text += f'  Адрес компании: {d[f"Address_{i}"]}\n'
            text += f'  Общая численность: {d[f"Number_{i}"]}\n'
    if 'Activity' in d:
        text += f'Область сертификации (основной ОКВЭД или вид деятельности компании): {d["Activity"]}\n'
    if 'Date' in d:
        text += f'Желаемые сроки для проведения аудита: {d["Date"]}\n'
    if 'Notes' in d:
        text += f'Примечания и пожелания: {d["Notes"]}\n'
    if 'Fullname' in d or 'Phone' in d:
        text += f'Контактные данные:\n'
    if 'Fullname' in d:
        text += f'ФИО: {d["Fullname"]}\n'
    if 'Phone' in d:
        text += f'Телефон: {d["Phone"]}\n'
    if 'Email' in d:
        text += f'Адрес электронной почты: {d["Email"]}\n'
    if 'ConnectionType' in d:
        text += f'Предпочитаемый вид связи: {d["connectionType"]}\n'
    if 'ConnectionTime' in d:
        if len(d['ConnectionTime'])>0:
            text += f'Примечание: {d["ConnectionTime"]}\n'
    return text

def save_request(d:dict, id:str):
    email_text = from_json_to_text(d)
    with open('email_sample.txt', 'r') as f:
        sample = f.read()
    sample = sample.replace('<ТЕКСТ ЗАПРОСА>', email_text)
    d['email_text'] = sample
    with open(f'requests/{id}.json', 'w') as f:
        json.dump(d, f)
    return f'Заявка {id} сохранена'

def load_requests(id:str) -> dict:
    with open(f'requests/{id}.json', 'r') as f:
        d = json.load(f)
    return d

def bot_send_message(text:str, unical_id):
    url = f'https://api.telegram.org/bot{bot.token}/sendMessage'
    count = 0
    keyboard = []
    for companie in text.split('Выбранные компании:')[-1].split('\n'):
        if len(companie) > 1:
            count += 1
            new_button = {'text':f'{keywords.smile1}{companie}{keywords.smile1}', 'callback_data':f'{count}-yes'}
            keyboard.append([new_button])
    send_button = {'text':keywords.word1, 'callback_data':f'send_{unical_id}'}
    del_button = {'text':keywords.word2, 'callback_data':f'del_{unical_id}'}
    keyboard.append([send_button, del_button])
    data = {
        'chat_id': bot.id_moderator,
        'text': text,
        'reply_markup': {
        'inline_keyboard': keyboard
    }}
    response = requests.post(url, json=data)

def make_email_from_json(path_to_json):
    with open(path_to_json, 'r') as f:
        d = json.load(f)
    del d['selectedCompanies']
    sample = d['email_text']
    msg = MIMEMultipart()
    msg['Subject'] = 'Audit Advisor: Заявка на сертификацию системы менеджмента'
    msg.attach(MIMEText(sample, 'plain'))
    return msg

def get_dict_names_and_email():
    with open('files/Live_Status.csv', 'r') as f:
        names = {i.split(',')[0].replace('"',''):i.split(',')[3] for i in f.readlines()[1:]}
    return names


def add_user(id, username):
    with open('files/users.txt', 'a') as f:
        f.write(f'{id}:{username}\n')

