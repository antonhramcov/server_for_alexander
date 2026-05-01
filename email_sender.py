import smtplib
from pathlib import Path
from tempfile import NamedTemporaryFile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import models
from config import SMTP_EMAIL, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT


email = SMTP_EMAIL
password = SMTP_PASSWORD


def send_email(address, path_to_json):
    if not isinstance(path_to_json, (str, Path)):
        with NamedTemporaryFile(mode='wb', suffix='.json', delete=True) as temp_file:
            temp_file.write(path_to_json.data)
            temp_file.flush()
            msg = models.make_email_from_json(temp_file.name)
    else:
        msg = models.make_email_from_json(path_to_json)
    msg['From'] = email
    msg['To'] = address
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(email, password)
        server.sendmail(email, address, msg.as_string())
        server.quit()
    except Exception as e:
        return f'Обнаружена ошибка {e}'
    else:
        return f'Письмо было отправлено на {address}'


def send_bad_email(address):
    msg = MIMEMultipart()
    with open('bad_answer.txt', 'r') as f:
        sample = f.read()
    msg['Subject'] = 'Audit Advisor: Ваш запрос на сертификацию отклонён'
    msg.attach(MIMEText(sample, 'plain'))
    msg['From'] = email
    msg['To'] = address
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(email, password)
        server.sendmail(email, address, msg.as_string())
        server.quit()
    except Exception as e:
        return f'Обнаружена ошибка {e}'
    else:
        return f'Письмо было отправлено на {address}'


def send_answer(address):
    msg = MIMEMultipart()
    with open('answer.txt', 'r') as f:
        sample = f.read()
    msg['Subject'] = '​Audit Advisor: Подтверждение успешной отправки запроса на сертификациюн'
    msg.attach(MIMEText(sample, 'plain'))
    msg['From'] = email
    msg['To'] = address
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(email, password)
        server.sendmail(email, address, msg.as_string())
        server.quit()
    except Exception as e:
        return f'Обнаружена ошибка {e}'
    else:
        return f'Письмо было отправлено на {address}'
